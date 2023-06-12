#!/usr/bin/python3.9

from ansible.module_utils.basic import AnsibleModule
import subprocess

def apt_package_management(package_name, desired_state):
    try:
        if desired_state == 'present':
            subprocess.check_call(['apt', 'install', '-y', package_name])
            return True
        elif desired_state == 'absent':
            subprocess.check_call(['apt', 'remove', '-y', package_name])
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )
    )

    package_name = module.params['name']
    desired_state = module.params['state']

    changed = apt_package_management(package_name, desired_state)

    result = dict(
        name=package_name,
        state=desired_state,
        changed=changed
    )

    module.exit_json(**result)

if __name__ == '__main__':
    main()