import time
import paramiko
import logging
from getpass import getpass
import click
import yaml
from paramiko import SSHClient
from datetime import date

class CmdResult:
    def __init__(self, stdout: str, stderr: str, exit_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


def connect_to_host(hostname, username):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, username=username)
    return client


def apt_package_management(package_name, desired_state, ssh_client):
    if desired_state == 'present':
        command = f'sudo apt-get install -y {package_name}'
        action = 'Install'
    elif desired_state == 'absent':
        command = f'sudo apt-get remove -y {package_name}'
        action = 'Remove'
    else:
        print("Invalid desired_state value")
        return

    result = run_remote_cmd(command, ssh_client)
    hostname = ssh_client.get_transport().getpeername()[0]
    print(f"{date} - [1] host={hostname} op=apt name={package_name} state={desired_state}")
    print(f"{date} -[1] host={hostname} op=apt status={'OK' if result.exit_code == 0 else 'CHANGED'}")
    print(f"stdout:\n{result.stdout}")
    print(f"stderr:\n{result.stderr}")


def service_management(service_name, desired_state, ssh_client):
    if desired_state in ['start', 'restart', 'stop']:
        command = f'sudo systemctl {desired_state} {service_name}'
        action = 'Manage'
    elif desired_state in ['enabled', 'disabled']:
        if desired_state == 'enabled':
            command = f'sudo systemctl enable {service_name}'
            action = 'Enable'
        else:
            command = f'sudo systemctl disable {service_name}'
            action = 'Disable'
    else:
        print("Invalid desired_state value")
        return

    result = run_remote_cmd(command, ssh_client)
    hostname = ssh_client.get_transport().getpeername()[0]
    print(f"{date} -[2] host={hostname} op=service name={service_name} state={desired_state}")
    print(f"{date} -[2] host={hostname} op=service status={'OK' if result.exit_code == 0 else 'CHANGED'}")
    print(f"stdout:\n{result.stdout}")
    print(f"stderr:\n{result.stderr}")


def run_remote_cmd(command: str, ssh_client: SSHClient) -> CmdResult:
    result = CmdResult("", "", -1)
    try:
        _, stdout, stderr = ssh_client.exec_command(command)
        result.stdout = stdout.read().decode('utf-8')
        result.stderr = stderr.read().decode('utf-8')
        result.exit_code = stdout.channel.recv_exit_status()
    except Exception as e:
        result.stderr = str(e)
    return result


def execute_playbook(playbook_file, inventory_file):
    # Charger le fichier de playbook YAML
    with open(playbook_file, 'r') as file:
        playbook = yaml.safe_load(file)

    # Charger le fichier d'inventaire YAML
    with open(inventory_file, 'r') as file:
        inventory = yaml.safe_load(file)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Collecter les informations sur les tâches et les hôtes
    tasks_count = sum(len(playbook_task.get('tasks', [])) for playbook_task in playbook)
    hosts = [host['hostname'] for host in inventory['hosts']]

    logger.info(f"processing {tasks_count} tasks on hosts: {', '.join(hosts)}")

    # Parcourir les playbooks dans le fichier de playbook
    for playbook_task in playbook:
        name = playbook_task.get('name')
        hosts = playbook_task.get('hosts')
        tasks = playbook_task.get('tasks')

        # Parcourir les hôtes spécifiés dans le playbook
        for host in inventory['hosts']:
            hostname = host['hostname']
            username = host['username']

            # Se connecter à l'hôte distant
            ssh_client = connect_to_host(hostname, username)
            logger.info(f"Connexion réussie à l'hôte : {hostname}")
            stdin, stdout, stderr = ssh_client.exec_command('hostname')
            logger.info(stdout.read().decode())
            time.sleep(.5)

            # Vérifier si des tâches sont définies
            if tasks:
                # Parcourir les tâches du playbook
                for task in tasks:
                    module_name = next(iter(task.keys()))  # Récupérer le nom du module
                    module_args = task.get(module_name)

                    # Exécuter l'action correspondante en fonction du module
                    if module_name == 'apt_package':
                        package_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        apt_package_management(package_name, desired_state, ssh_client)
                    elif module_name == 'service_status':
                        service_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        service_management(service_name, desired_state, ssh_client)
                    else:
                        print(f"Module '{module_name}' non pris en charge")

            # Fermer la connexion SSH
            ssh_client.close()

    logger.info(f"done processing tasks for hosts: {', '.join(hosts)}")


@click.command()
@click.option('-f', '--playbook', required=True, help='Chemin vers le fichier de playbook')
@click.option('-i', '--inventory', required=True, help='Chemin vers le fichier d\'inventaire')
def main(playbook, inventory):
    execute_playbook(playbook, inventory)


if __name__ == '__main__':
    main()
