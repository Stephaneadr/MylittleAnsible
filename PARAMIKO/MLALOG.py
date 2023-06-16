import paramiko
import logging
from getpass import getpass
import click
import yaml
from paramiko import SSHClient
from jinja2 import Environment, FileSystemLoader
import os

class CmdResult:
    def __init__(self, stdout: str, stderr: str, exit_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


""" def connect_to_host(hostname, username):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, username=username)
    return client """

choice = input ("choisi t'a méthode de connexion :\n 1 - Username/Password\n 2 - Key-file\n")
    
def connect_to_host(hostname, username):
    client = paramiko.SSHClient()
    if choice == "1":
        password = getpass('enter your password :')
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        return client
    elif choice == "2":
        key_file = paramiko.Ed25519Key.from_private_key_file("/home/stef/.ssh/id_ed25519")
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username,pkey=key_file, allow_agent=False, look_for_keys=False)
        return client
    else :
        client.load_system_host_keys() # Première méthode know_host
        client.connect(hostname, username=username)
        return client

def command_module(command, shell, ssh_client):
    if shell is None:
        shell = '/bin/bash'
    full_command = f'sudo {shell} -c "{command}"'
    run_remote_cmd(full_command, ssh_client)


def sysctl_module(attribute, value, permanent, ssh_client):
    command = f'sudo sysctl -w {"--permanent" if permanent else ""} {attribute}={value}'
    run_remote_cmd(command, ssh_client)
    """ hostname = ssh_client.get_transport().getpeername()[0]
    print(f"[4] host={hostname} op=sysctl attribute={attribute} value={value} permanent={permanent}")
    print(f"[4] host={hostname} op=sysctl status={'OK' if result.exit_code == 0 else 'FAILED'}")
 """

def copy_module(src, dest, backup, ssh_client):
    command = f'sudo cp -r {"--backup=numbered" if backup else ""} {src} {dest}'
    run_remote_cmd(command, ssh_client)

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

    run_remote_cmd(command, ssh_client)


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

def copy_sftp( source_dir, destination_dir, ssh_client):

    # Créer une session SFTP
    sftp = ssh_client.open_sftp()
    
    # Appeler la fonction récursive pour copier le dossier et les sous-dossiers
    copy_sftp_recursive(source_dir, destination_dir, sftp)

    # Fermer la session SFTP et la connexion SSH
    sftp.close()


def service_management(service_name, desired_state, ssh_client):
    if desired_state in ['start', 'restart', 'stop']:
        command = f'sudo systemctl {desired_state} {service_name}'
        action = 'Manage'
    elif desired_state in ['enabled', 'disabled']:
        if desired_state == 'enabled':
            command = f'sudo systemctl enable {service_name}'
        else:
            command = f'sudo systemctl disable {service_name}'
    else:
        print("Invalid desired_state value")
        return

    run_remote_cmd(command, ssh_client)


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


    # Collecter les informations sur les tâches et les hôtes
    tasks_count = sum(len(playbook_task.get('tasks', [])) for playbook_task in playbook)
    hosts = [host['hostname'] for host in inventory['hosts']]


    logging.info(f"processing {tasks_count} tasks on hosts: {', '.join(hosts)}")

    # Parcourir les playbooks dans le fichier de playbook
    for playbook_task in playbook:
        name = playbook_task.get('name')
        hosts = playbook_task.get('hosts')
        params = playbook_task.get('params')

        # Parcourir les hôtes spécifiés dans le playbook
        for host in inventory['hosts']:
            hostname = host['hostname']
            username = host['username']


            # Se connecter à l'hôte distant
            ssh_client = connect_to_host(choice)
            logging.info(f"Connexion réussie à l'hôte : {hostname}")

            # Vérifier si des tâches sont définies
            if params:
                # Parcourir les tâches du playbook
                for param in params:
                    module = next(iter(param.keys()))  # Récupérer le nom du module
                    module_args = param.get(module)

                    # Exécuter l'action correspondante en fonction du module
                    if module == 'apt_package':
                        package_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        apt_package_management(package_name, desired_state, ssh_client)
                        logging.info(f"[1] host={hostname} op=apt status='OK'")
                    elif module == 'service_status':
                        service_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        service_management(service_name, desired_state, ssh_client)
                        logging.info(f"[2] host={hostname} op=service name={service_name} state={desired_state}")
                    elif module == 'copy':
                        src = module_args.get('src')
                        dest = module_args.get('dest')
                        backup = module_args.get('backup', False)
                        copy_module(src, dest, backup, ssh_client) 
                        logging.info(f"[3] host={hostname} op=copy src={src} dest={dest} backup={backup}")
                    elif module == 'sysctl':
                        attribute = module_args.get('attribute')
                        value = module_args.get('value')
                        permanent = module_args.get('permanent', False)
                        sysctl_module(attribute, value, permanent, ssh_client)
                        logging.info(f"[4] host={hostname} op=sysctl attribute={attribute} value={value} permanent={permanent}")
                    elif module == 'command':
                        command = module_args.get('command')
                        shell = module_args.get('shell', '/bin/bash')
                        command_module(command, shell, ssh_client)
                        logging.info(f"[5] host={hostname} op=command command={command} shell={shell}")
                        logging.info(f"[5] host={hostname} op=command status='OK'")
                    else:
                        pass

            # Fermer la connexion SSH

            ssh_client.close()
        
        logging.info(f"done processing tasks for hosts: {hostname}")


@click.command()
@click.option('-f', '--playbook', required=True, help='Chemin vers le fichier de playbook')
@click.option('-i', '--inventory', required=True, help='Chemin vers le fichier d\'inventaire')
def main(playbook, inventory):
    execute_playbook(playbook, inventory)


if __name__ == '__main__':
    main()
