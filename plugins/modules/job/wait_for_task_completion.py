# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------------------------


DOCUMENTATION = '''
module: xbh03.commvault.job.wait_for_task_completion
short_description: Wait for Job completion
description:
    - This module wait the job completion
    - xbh03.commvault.job.wait_for_task_completion module can be used in playbooks to wait the completion of the Job

options:
    webserver_hostname:
        description:
            - Hostname of the Web Server.
        type: str
        required: false

    commcell_username:
        description:
            - Commcell username
        type: str
        required: false
    
    commcell_password:
        description:
            - Commcell password
        type: str
        required: false

    job_id:
        description:
            - ID of the job
        type: int
        required: true
    
    timeout:
        description:
            - Time for timeout
        type: int
        required: True

'''
EXAMPLES = '''
# Wait the completion of a particular Job

- name: "Wait for task completion Job"
  xbh03.commvault.job.wait_for_task_completion:
    job_id: 3
    timeout: 300

- name: "wait for task completion Job"
  xbh03.commvault.job.wait_for_task_completion:
    webserver_hostname: "demo-CS-Name"
    commcell_username: "user"
    commcell_password: "CS-password"
    job_id: 23
    timeout: 600

'''

RETURN = r'''#'''

from ansible_collections.xbh03.commvault.plugins.module_utils.cv_ansible_module import CVAnsibleModule
try:
    from cvpysdk.job import Job
    from cvpysdk.exception import SDKException
except ModuleNotFoundError:
    pass


def main():
    """Main method for this module."""
    try:
        module_args = dict(
            job_id=dict(type=int, required=True),
            timeout=dict(type=int, required=True)
        )

        module = CVAnsibleModule(argument_spec=module_args)

        job_id = int(module.params['job_id'])
        timeout = int(module.params['timeout'])
        commcell_obj = module.commcell

        job = Job(commcell_obj,job_id)
        job.wait_for_completion(timeout=timeout)

        if job.status not in ['Pending', 'Waiting', 'Running', 'Queued'] :
            module.result['failed'] = False
            module.result['changed'] = True
            module.exit_json(**module.result)


    except Exception as exp:
        module.fail_json(msg=str(exp), changed=False)


if __name__ == "__main__":
    main()
