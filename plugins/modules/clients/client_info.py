# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: commvault.ansible.clients.client_info
short_description: List clients or retrieve the properties of an existing client
description:
  - Returns properties and the ID of a client entity, including filesystem pseudoclients, using CVPySDK.
  - Without an identifier, returns the SDK client inventory, which is not filtered by workload.
  - Inventory and name/ID resolution follow SDK visibility and permissions.
  - Does not modify clients. Supports check mode.
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
      - Mutually exclusive with I(client_id). Omit both to list clients.
    type: str
  client_id:
    description:
      - Positive ID of the existing client entity, resolved by CVPySDK.
      - Mutually exclusive with I(client). Omit both to list clients.
    type: int
requirements:
  - cvpysdk >= 11.38
author:
  - Commvault Systems Inc
'''

EXAMPLES = r'''
- name: List clients visible to the SDK
  commvault.ansible.clients.client_info:
  register: inventory

- name: Retrieve a filesystem pseudoclient ID and its properties by name
  commvault.ansible.clients.client_info:
    client: filesystem-pseudoclient01
  register: pseudoclient

- name: Retrieve properties by client ID
  commvault.ansible.clients.client_info:
    client_id: 123
'''

RETURN = r'''
clients:
  description:
    - SDK inventory keyed by client name.
    - Each entry includes id (a string), hostname and displayName as returned by CVPySDK.
  returned: success, when neither client nor client_id is supplied
  type: dict
client:
  description: Resolved client name.
  returned: success, when an identifier is supplied
  type: str
client_id:
  description: Resolved client ID.
  returned: success, when an identifier is supplied
  type: int
description:
  description: Current description, or an empty string when unset.
  returned: success, when an identifier is supplied
  type: str
properties:
  description: Client property dictionary returned by CVPySDK, not the outer REST response envelope.
  returned: success, when an identifier is supplied
  type: dict
'''

from cvpysdk.exception import SDKException

from ansible_collections.commvault.ansible.plugins.module_utils.clients import get_client
from ansible_collections.commvault.ansible.plugins.module_utils.cv_ansible_module import CVAnsibleModule


def main():
    """Read the client inventory or a single client's properties."""
    module = CVAnsibleModule(
        argument_spec=dict(client=dict(type=str), client_id=dict(type=int)),
        mutually_exclusive=[['client', 'client_id']],
    )
    result = dict(changed=False)
    try:
        if module.params['client'] is None and module.params['client_id'] is None:
            module.commcell.clients.refresh()
            result['clients'] = module.commcell.clients.all_clients
        else:
            client = get_client(module.commcell, module.params['client'], module.params['client_id'])
            result.update(
                client=client.client_name,
                client_id=int(client.client_id),
                description=client.description or '',
                properties=client.properties,
            )
        module.exit_json(**result)
    except (SDKException, ValueError) as error:
        module.fail_json(msg=str(error), **result)


if __name__ == '__main__':
    main()
