import time
import paramiko
import logging
from getpass import getpass
import click
import jinja2
import yaml
import subprocess


def connect_to_host(hostname, username):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, username=username)
    return client


def apt_package_management(package_name, desired_state):
    if desired_state == 'present':
        command = ['sudo','apt', 'install', '-y', package_name]
        action = 'Install'
    elif desired_state == 'absent':
        command = ['sudo','apt', 'remove', '-y', package_name]
        action = 'Remove'
    else:
        print("Invalid desired_state value")
        return

    try:
        subprocess.check_call(command)
        print(f"{action} package {package_name} successful")
    except subprocess.CalledProcessError:
        print(f"{action} package {package_name} failed")


def service_management(service_name, desired_state):
    if desired_state in ['start', 'restart', 'stop']:
        command = ['sudo','systemctl', desired_state, service_name]
        action = 'Manage'
    elif desired_state in ['enabled', 'disabled']:
        if desired_state == 'enabled':
            command = ['sudo','systemctl', 'enable', service_name]
            action = 'Enable'
        else:
            command = ['sudo','systemctl', 'disable', service_name]
            action = 'Disable'
    else:
        print("Invalid desired_state value")
        return

    try:
        subprocess.check_call(command)
        print(f"{action} service {service_name} successful")
    except subprocess.CalledProcessError:
        print(f"{action} service {service_name} failed")




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
            client = connect_to_host(hostname, username)
            print(f"Connexion réussie à l'hôte : {hostname}")
            stdin, stdout, stderr = client.exec_command("hostname")
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
                        apt_package_management(package_name, desired_state)
                    elif module_name == 'service_status':
                        service_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        service_management(service_name, desired_state)
                    else:
                        print(f"Module '{module_name}' non pris en charge")

    # Fermer la connexion SSH
    client.close()


@click.command()
@click.option('-f', '--playbook', required=True, help='Chemin vers le fichier de playbook')
@click.option('-i', '--inventory', required=True, help='Chemin vers le fichier d\'inventaire')

def main(playbook, inventory):
    execute_playbook(playbook, inventory)


if __name__ == '__main__':
    main()

