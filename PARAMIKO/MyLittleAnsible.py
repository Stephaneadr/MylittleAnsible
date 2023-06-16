import time
import paramiko
import logging
from getpass import getpass
import click
import yaml
from paramiko import SSHClient
from typing import Dict
from jinja2 import Environment, FileSystemLoader

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


def copy_sftp_recursive(source, destination, sftp):
    try:
        sftp.mkdir(destination)
    except IOError as e:
        # Ignorer les erreurs si le dossier existe déjà
        if "File already exists" not in str(e):
            raise
    for item in sftp.listdir_attr(source):
        item_path = source + '/' + item.filename
        if os.path.isfile(item_path):
            sftp.put(item_path, destination + '/' + item.filename)
        else:
            sub_destination = destination + '/' + item.filename
            sftp.mkdir(sub_destination)
            copy_sftp_recursive(item_path, sub_destination)

def copy_sftp(hostname, username, password, source_dir, destination_dir, ssh_client):
    # Établir une connexion SSH
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname, username=username, password=password)

    # Créer une session SFTP
    sftp = ssh_client.open_sftp()
    
    # Appeler la fonction récursive pour copier le dossier et les sous-dossiers
    copy_sftp_recursive(source_dir, destination_dir, sftp)

    # Fermer la session SFTP et la connexion SSH
    sftp.close()
    ssh_client.close()



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
    print(f"{action} package {package_name} - Exit code: {result.exit_code}")
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
    print(f"{action} service {service_name} - Exit code: {result.exit_code}")
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

def render(playbook):

    template_params = playbook['module']['params']
    src_template = template_params['src']
    dest_file = template_params['dest']
    variables = template_params.get('vars', {})
    env = Environment(loader=FileSystemLoader(src_template))
    template = env.get_template(src_template)
    resultat = template.render(variables)
    with open(dest_file, 'w') as f:
        f.write(resultat)
    print("Le rendu du template a été écrit dans le fichier de destination.")

def execute_playbook(playbook_file, inventory_file):
    # Charger le fichier de playbook YAML
    with open(playbook_file, 'r') as file:
        playbook = yaml.safe_load(file)

    # Charger le fichier d'inventaire YAML
    with open(inventory_file, 'r') as file:
        inventory = yaml.safe_load(file)

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
            print(f"Connexion réussie à l'hôte : {hostname}")
            stdin, stdout, stderr = ssh_client.exec_command('hostname')
            print(stdout.read().decode())
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


@click.command()
@click.option('-f', '--playbook', required=True, help='Chemin vers le fichier de playbook')
@click.option('-i', '--inventory', required=True, help='Chemin vers le fichier d\'inventaire')

def main(playbook, inventory):
    execute_playbook(playbook, inventory)


if __name__ == '__main__':
    main()
