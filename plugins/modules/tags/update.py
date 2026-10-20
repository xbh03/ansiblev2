# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: xbh03.commvault.tags.update
short_description: Renames an entity tag globally
description:
  - Renames a Command Center entity tag using its existing ID and tag container.
  - This does not delete and recreate the tag or update a value on a single client.
  - If the old name is absent and the new name exists, the rename is considered already applied.
  - Fails if neither name exists, or if the new name belongs to another tag.
  - Names differing only in case are considered identical, as in CVPySDK.
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
  name:
    description: Current name of the entity tag.
    type: str
    required: true
  new_name:
    description: Desired name of the entity tag.
    type: str
    required: true
author:
  - Commvault Systems Inc
'''

EXAMPLES = r'''
- name: Rename a tag without recreating it
  xbh03.commvault.tags.update:
    name: Production
    new_name: Critical
'''

RETURN = r'''
name:
  description: Desired name of the tag.
  returned: success
  type: str
id:
  description: ID of the tag, unchanged by the rename.
  returned: success
  type: str
'''

from ansible_collections.xbh03.commvault.plugins.module_utils.cv_ansible_module import CVAnsibleModule
from ansible_collections.xbh03.commvault.plugins.module_utils.tags import request, validate_names


def main():
    module = CVAnsibleModule(argument_spec=dict(
        name=dict(type=str, required=True),
        new_name=dict(type=str, required=True),
    ))
    name = module.params['name']
    new_name = module.params['new_name']
    result = dict(changed=False, name=new_name, id=None)
    try:
        validate_names([name, new_name])
        tags = module.commcell.tags
        tags.refresh()
        if not tags.has_tag(name):
            if not tags.has_tag(new_name):
                raise ValueError("Tag [{0}] does not exist".format(name))
            result['id'] = tags.get(new_name).tag_id
            module.exit_json(**result)

        tag = tags.get(name)
        result['id'] = tag.tag_id
        if name.lower() == new_name.lower():
            module.exit_json(**result)
        if tags.has_tag(new_name):
            raise ValueError("Tag [{0}] already exists".format(new_name))
        if not module.check_mode:
            # Same endpoint and payload as CVPySDK's Activate Tag.modify().
            response = request(module.commcell, 'PUT', 'EDiscovery/Tags', {
                'container': {'containerId': tags.DEFAULT_TAGSET_ID},
                'tags': [{'tagId': int(tag.tag_id), 'name': new_name}],
            })
            result['changed'] = True
            if 'tag' not in response:
                raise ValueError("Tag rename response is missing the tag")
            tags.refresh()
            if not tags.has_tag(new_name) or tags.get(new_name).tag_id != tag.tag_id:
                raise ValueError("Tag rename could not be verified with the original tag ID")
        result['changed'] = True
        module.exit_json(**result)
    except Exception as error:
        module.fail_json(msg=str(error), **result)


if __name__ == "__main__":
    main()
