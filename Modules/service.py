ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: service
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
version_added: "0.1"
short_description:  Manage services.
description:
    - Controls services on remote hosts. Supported init systems include BSD init,
      OpenRC, SysV, Solaris SMF, systemd, upstart.
options:
    name:
        required: true
        description:
        - Name of the service.
    state:
        required: false
        choices: [ started, stopped, restarted, reloaded ]
        description:
          - C(started)/C(stopped) are idempotent actions that will not run
            commands unless necessary.  C(restarted) will always bounce the
            service.  C(reloaded) will always reload. B(At least one of state
            and enabled are required.)
    sleep:
        required: false
        version_added: "1.3"
        description:
        - If the service is being C(restarted) then sleep this many seconds
          between the stop and start command. This helps to workaround badly
          behaving init scripts that exit immediately after signaling a process
          to stop.
    pattern:
        required: false
        version_added: "0.7"
        description:
        - If the service does not respond to the status command, name a
          substring to look for as would be found in the output of the I(ps)
          command as a stand-in for a status result.  If the string is found,
          the service will be assumed to be running.
    enabled:
        required: false
        choices: [ "yes", "no" ]
        description:
        - Whether the service should start on boot. B(At least one of state and
          enabled are required.)

    runlevel:
        required: false
        default: 'default'
        description:
        - "For OpenRC init scripts (ex: Gentoo) only.  The runlevel that this service belongs to."
    arguments:
        description:
        - Additional arguments provided on the command line
        aliases: [ 'args' ]
    use:
        description:
            - The service module actually uses system specific modules, normally through auto detection, this setting can force a specific module.
            - Normally it uses the value of the 'ansible_service_mgr' fact and falls back to the old 'service' module when none matching is found.
        default: 'auto'
        version_added: 2.2
'''

EXAMPLES = '''
# Example action to start service httpd, if not running
- service:
    name: httpd
    state: started

# Example action to stop service httpd, if running
- service:
    name: httpd
    state: stopped

# Example action to restart service httpd, in all cases
- service:
    name: httpd
    state: restarted

# Example action to reload service httpd, in all cases
- service:
    name: httpd
    state: reloaded

# Example action to enable service httpd, and not touch the running state
- service:
    name: httpd
    enabled: yes

# Example action to start service foo, based on running process /usr/bin/foo
- service:
    name: foo
    pattern: /usr/bin/foo
    state: started

# Example action to restart network service for interface eth0
- service:
    name: network
    state: restarted
    args: eth0

'''

from ansible.module_utils.basic import AnsibleModule
import subprocess

def get_service_status(service_name):
    try:
        output = subprocess.check_output(['systemctl', 'show', '--property=ActiveState', '--value', service_name])
        status = output.decode().strip()
        return status
    except subprocess.CalledProcessError:
        return 'unknown'

def manage_service(service_name, desired_state):
    try:
        subprocess.check_call(['systemctl', desired_state, service_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['started', 'restarted', 'stopped', 'enabled', 'disabled'])
        )
    )

    service_name = module.params['name']
    desired_state = module.params['state']
    current_state = get_service_status(service_name)

    if desired_state in ['started', 'restarted', 'stopped']:
        changed = manage_service(service_name, desired_state)
    elif desired_state in ['enabled', 'disabled']:
        if desired_state == 'enabled' and current_state != 'enabled':
            changed = manage_service(service_name, 'enable')
        elif desired_state == 'disabled' and current_state != 'disabled':
            changed = manage_service(service_name, 'disable')
        else:
            changed = False
    else:
        changed = False

    result = dict(
        name=service_name,
        state=current_state,
        changed=changed
    )

    module.exit_json(**result)

if __name__ == '__main__':
    main()

