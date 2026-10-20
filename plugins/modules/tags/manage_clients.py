# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: xbh03.commvault.tags.manage_clients
short_description: Associates or removes entity tags on a client
description:
  - Manages entity tags on CLIENT_ENTITY (3), including filesystem, VM and database clients with a client ID.
  - Does not manage database instances or subclients (entity types 5 and 7).
  - Only the requested associations are changed. Other tags and their values are preserved.
  - Tags must already exist when I(state=present).
  - Removal deletes the association, not the global tag, and removes all values of the requested tag on this client.
  - Specify exactly one of I(client) or I(client_id). Both identify the same client entity and perform identical tagging.
  - Either identifier can be used for any supported workload; client IDs are not restricted to VMs.
  - For a VM, identify the VM's own client entity by name or ID, not its virtualization client.
  - Supports check mode.
options:
  webserver_hostname:
    description: Hostname of the Web Server.
    type: str
  commcell_username:
    description: CommCell username.
    type: str
  commcell_password:
    description: CommCell password.
    type: str
  client:
    description:
      - Name of the target client, resolved to a client ID by CVPySDK.
      - Can be used for filesystem, VM or database clients when their names are resolvable by the SDK.
      - Specify exactly one of I(client) or I(client_id).
    type: str
  client_id:
    description:
      - Positive ID of the target client entity, used directly without SDK name resolution.
      - Can be used for any supported client, not only VM pseudoclients.
      - Useful when the name cannot be resolved or to identify the client explicitly.
      - Must be a client ID, not an instance ID, subclient ID or VM inventory identifier.
      - Specify exactly one of I(client) or I(client_id).
    type: int
  tags:
    description:
      - Names of tags to associate or remove.
      - Existing values are preserved. New associations without an explicit value use an empty value.
    type: list
    elements: str
    default: []
  tag_values:
    description:
      - Mapping of tag names to string values to ensure on the client.
      - Updates the existing association value using PUT, rather than adding another value.
      - An explicit empty string clears the value.
      - Only supported with I(state=present). Use I(tags) to remove associations.
    type: dict
    default: {}
  state:
    description: Whether the requested associations should exist.
    type: str
    choices: [present, absent]
    default: present
author:
  - Commvault Systems Inc
'''

EXAMPLES = r'''
- name: Associate tags with a filesystem client
  xbh03.commvault.tags.manage_clients:
    client: fileserver01
    tags: [Critical, Linux]
    tag_values:
      Environment: Production

- name: Identify the same filesystem client by ID instead of name (123 is an example ID)
  xbh03.commvault.tags.manage_clients:
    client_id: 123
    tags: [Critical]
    tag_values:
      Environment: Production

- name: Associate a tag with a VM using its SDK-resolvable client name
  xbh03.commvault.tags.manage_clients:
    client: vm-client01
    tags: [Critical]

- name: Update the Environment value on a database client
  xbh03.commvault.tags.manage_clients:
    client: database-server01
    tag_values:
      Environment: Production

- name: Remove an association without deleting the tag
  xbh03.commvault.tags.manage_clients:
    client: fileserver01
    tags: [Critical]
    state: absent
'''

RETURN = r'''
client_id:
  description: ID of the targeted client entity.
  returned: success
  type: int
tags:
  description: Requested tag names, deduplicated case-insensitively.
  returned: success
  type: list
  elements: str
tag_values:
  description: Explicitly requested tag values.
  returned: success
  type: dict
state:
  description: Desired state of the associations.
  returned: success
  type: str
'''

from ansible_collections.xbh03.commvault.plugins.module_utils.cv_ansible_module import CVAnsibleModule
from ansible_collections.xbh03.commvault.plugins.module_utils.tags import client_tags, request, validate_names


def main():
    module = CVAnsibleModule(
        argument_spec=dict(
            client=dict(type=str),
            client_id=dict(type=int),
            tags=dict(type=list, elements=str, default=[]),
            tag_values=dict(type=dict, default={}),
            state=dict(type=str, choices=['present', 'absent'], default='present'),
        ),
        mutually_exclusive=[['client', 'client_id']],
        required_one_of=[['client', 'client_id']],
    )
    result = dict(changed=False, client_id=module.params['client_id'],
                  tags=[], tag_values=module.params['tag_values'], state=module.params['state'])
    try:
        if result['state'] == 'absent' and result['tag_values']:
            raise ValueError("tag_values is only supported with state=present; use tags to remove associations")
        values = {}
        for name, value in result['tag_values'].items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise ValueError("tag_values must map string tag names to string values")
            if name.lower() in values:
                raise ValueError("tag_values contains duplicate case-insensitive tag names")
            if len(value) > 1024:
                raise ValueError("Tag values must not exceed 1024 characters")
            values[name.lower()] = value
        validate_names(module.params['tags'])
        validate_names(result['tag_values'])
        names = {}
        for name in list(module.params['tags']) + list(result['tag_values']):
            if len(name) > 512:
                raise ValueError("Tag names must not exceed 512 characters")
            names.setdefault(name.lower(), name)
        result['tags'] = list(names.values())
        if result['client_id'] is None:
            if not module.params['client'].strip():
                raise ValueError("Client name must not be empty or whitespace")
            result['client_id'] = int(module.commcell.clients.get(module.params['client']).client_id)
        if result['client_id'] <= 0:
            raise ValueError("client_id must be a positive integer")

        current = client_tags(module.commcell, result['client_id'])
        operations = []
        if result['state'] == 'present':
            tags = module.commcell.tags
            tags.refresh()
            missing = [name for name in names.values() if not tags.has_tag(name)]
            if missing:
                raise ValueError("Tags do not exist: {0}".format(', '.join(missing)))
            additions = []
            updates = []
            for key, name in names.items():
                assigned = [tag for tag in current if tag['name'].lower() == key]
                if not assigned:
                    additions.append({'name': name, 'value': values.get(key, '')})
                elif key in values and any(tag.get('value', '') != values[key] for tag in assigned):
                    if len(assigned) != 1:
                        raise ValueError(
                            "Multiple associations returned for tag [{0}]; cannot update safely".format(name))
                    updates.append(dict(assigned[0], value=values[key]))
            operations = [('POST', additions), ('PUT', updates)]
        else:
            changes = [tag for tag in current if tag['name'].lower() in names]
            operations = [('DELETE', changes)]

        for method, changes in operations:
            if changes:
                if module.check_mode:
                    result['changed'] = True
                    continue
                request(module.commcell, method, 'Tags', {
                    'entityTag': [{
                        'entityType': 3,
                        'entityId': result['client_id'],
                        'tag': changes,
                    }],
                })
                result['changed'] = True
        if result['changed'] and not module.check_mode:
            remaining = client_tags(module.commcell, result['client_id'])
            remaining_names = {tag['name'].lower() for tag in remaining}
            if result['state'] == 'present':
                verified = set(names).issubset(remaining_names) and all(
                    tag.get('value', '') == values[tag['name'].lower()]
                    for tag in remaining if tag['name'].lower() in values
                )
            else:
                verified = set(names).isdisjoint(remaining_names)
            if not verified:
                raise ValueError("Client tag associations could not be verified after the update")
        module.exit_json(**result)
    except Exception as error:
        module.fail_json(msg=str(error), **result)


if __name__ == "__main__":
    main()
