# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: commvault.ansible.tags.delete
short_description: Deletes an entity tag globally
description:
  - Deletes a Command Center entity tag and its associations.
  - Does nothing when the tag does not exist.
  - To remove only a client association, use M(commvault.ansible.tags.manage_clients).
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
    description: Name of the entity tag to delete.
    type: str
    required: true
author:
  - Commvault Systems Inc
'''

EXAMPLES = r'''
- name: Delete a tag globally
  commvault.ansible.tags.delete:
    name: Production
'''

RETURN = r'''
name:
  description: Name of the tag.
  returned: success
  type: str
'''

from ansible_collections.commvault.ansible.plugins.module_utils.cv_ansible_module import CVAnsibleModule
from ansible_collections.commvault.ansible.plugins.module_utils.tags import validate_names


def main():
    module = CVAnsibleModule(argument_spec=dict(name=dict(type=str, required=True)))
    result = dict(changed=False, name=module.params['name'])
    try:
        validate_names([result['name']])
        tags = module.commcell.tags
        tags.refresh()
        if tags.has_tag(result['name']):
            if not module.check_mode:
                tags.delete(result['name'])
            result['changed'] = True
        module.exit_json(**result)
    except Exception as error:
        module.fail_json(msg=str(error), **result)


if __name__ == "__main__":
    main()
