# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: xbh03.commvault.clients.manage_client
short_description: Manage the description of an existing client or pseudoclient
description:
  - Adds, updates or clears the description of an existing client entity using CVPySDK.
  - Supports client entities resolvable by the SDK, including filesystem pseudoclients.
  - Does not create or delete clients, install agents, or modify subclients.
  - Only the description is changed; other client properties are preserved.
  - Supports check mode and diff mode.
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
      - Name of the existing client, resolved by CVPySDK.
      - Specify exactly one of I(client) or I(client_id).
    type: str
  client_id:
    description:
      - Positive ID of the existing client entity, resolved by CVPySDK.
      - Must be a client ID, not an instance ID or a subclient ID.
      - Specify exactly one of I(client) or I(client_id).
    type: int
  description:
    description:
      - Desired client description. An empty string clears the description.
    type: str
    required: true
requirements:
  - cvpysdk >= 11.38
author:
  - Commvault Systems Inc
'''

EXAMPLES = r'''
- name: Update the description of an existing filesystem pseudoclient
  xbh03.commvault.clients.manage_client:
    client: filesystem-pseudoclient01
    description: Production filesystem

- name: Clear the description using the client ID
  xbh03.commvault.clients.manage_client:
    client_id: 123
    description: ''
'''

RETURN = r'''
client:
  description: Resolved client name.
  returned: success
  type: str
client_id:
  description: Resolved client ID.
  returned: success
  type: int
description:
  description: Current description, or an empty string when unset. In check mode this is the unchanged value.
  returned: success
  type: str
'''

from cvpysdk.exception import SDKException

from ansible_collections.xbh03.commvault.plugins.module_utils.clients import get_client
from ansible_collections.xbh03.commvault.plugins.module_utils.cv_ansible_module import CVAnsibleModule


def main():
    """Manage the description without changing unrelated client properties."""
    module = CVAnsibleModule(
        argument_spec=dict(
            client=dict(type=str),
            client_id=dict(type=int),
            description=dict(type=str, required=True),
        ),
        mutually_exclusive=[['client', 'client_id']],
        required_one_of=[['client', 'client_id']],
    )
    result = dict(changed=False)
    try:
        client = get_client(module.commcell, module.params['client'], module.params['client_id'])
        current = client.description or ''
        desired = module.params['description']
        result.update(client=client.client_name, client_id=int(client.client_id), description=current)
        if module._diff:
            result['diff'] = dict(before=dict(description=current), after=dict(description=desired))
        if current != desired:
            if module.check_mode:
                result['changed'] = True
            else:
                client.description = desired
                result['changed'] = True
                client.refresh()
                result['description'] = client.description or ''
                if result['description'] != desired:
                    raise ValueError("Client description could not be verified after the update")
        module.exit_json(**result)
    except (SDKException, ValueError) as error:
        module.fail_json(msg=str(error), **result)


if __name__ == '__main__':
    main()
