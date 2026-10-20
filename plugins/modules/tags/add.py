# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# SPDX-License-Identifier: Apache-2.0

DOCUMENTATION = r'''
---
module: xbh03.commvault.tags.add
short_description: Creates an entity tag
description:
  - Creates a Command Center entity tag if it does not already exist.
  - Tag names are compared case-insensitively by CVPySDK.
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
    description: Name of the entity tag.
    type: str
    required: true
author:
  - Commvault Systems Inc
'''

EXAMPLES = r'''
- name: Create a tag
  xbh03.commvault.tags.add:
    name: Production
'''

RETURN = r'''
name:
  description: Name of the tag.
  returned: success
  type: str
id:
  description: ID of the tag. Null when check mode predicts creation.
  returned: success
  type: str
'''

from ansible_collections.xbh03.commvault.plugins.module_utils.cv_ansible_module import CVAnsibleModule
from ansible_collections.xbh03.commvault.plugins.module_utils.tags import validate_names


def main():
    module = CVAnsibleModule(argument_spec=dict(name=dict(type=str, required=True)))
    result = dict(changed=False, name=module.params['name'], id=None)
    try:
        validate_names([result['name']])
        tags = module.commcell.tags
        tags.refresh()
        if tags.has_tag(result['name']):
            tag = tags.get(result['name'])
        elif module.check_mode:
            result['changed'] = True
            module.exit_json(**result)
        else:
            tag = tags.add(result['name'])
            result['changed'] = True
        result.update(name=tag.tag_name, id=tag.tag_id)
        module.exit_json(**result)
    except Exception as error:
        module.fail_json(msg=str(error), **result)


if __name__ == "__main__":
    main()
