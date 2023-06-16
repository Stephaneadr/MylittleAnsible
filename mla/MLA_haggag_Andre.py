import paramiko
import logging
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


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')




def command_module(command, shell, ssh_client):
    logger = logging.getLogger(__name__)
    hostname = ssh_client.get_transport().getpeername()[0]
    if shell is None:
        shell = '/bin/bash'
        command = f'{command}'
    result = run_remote_cmd(command, ssh_client)
    if result.stderr == False:
        logger.error(f"{result.stderr}")
    else:
        logging.info(
            f"[5] host={hostname} op=command status={'OK' if result.exit_code == 0 else 'ko'}")
        logger.info(f"[5] host={hostname} - resultat : {result.stdout}")


def sysctl_module(attribute, value, permanent, ssh_client):
    logger = logging.getLogger(__name__)
    hostname = ssh_client.get_transport().getpeername()[0]

    # Effectue la commande définie selon la variable permanent
    if permanent == True:
        command = f'sudo sysctl -w {attribute}={value} >> /etc/sysctl.conf | sudo sysctl  --system '
    else:
        command = f'sudo sysctl -w {attribute}={value}'
    result = run_remote_cmd(command, ssh_client)
    if result.stderr == False:
        logger.error(f"{result.stderr}")
    else:
        logging.info(
            f"[4] host={hostname} op=sysctl status={'OK' if result.exit_code == 0 else 'ko'}")


def copy_module(src, dest, backup, ssh_client):
    logger = logging.getLogger(__name__)
    hostname = ssh_client.get_transport().getpeername()[0]

    # Vérifier si le fichier source existe localement
    if not os.path.exists(src):
        logger.error(
            f"[3] host={hostname} op=copy src={src} status=ko (Source file not found)")
        return

    # Vérifier si la destination est un dossier existant sur l'hôte distant
    sftp = ssh_client.open_sftp()
    try:
        parent_dir, dest_name = os.path.split(dest)
        dir_items = sftp.listdir(parent_dir)
        if dest_name in dir_items:
            if backup:
                # Effectuer une sauvegarde du fichier/dossier existant
                backup_path = f"{dest}.bak"
                sftp.rename(dest, backup_path)
                logger.warning(
                    f"[3] host={hostname} op=copy src={src} dest={dest} backup={backup} status=CHANGED (Backup created: {backup_path})")
            else:
                logger.error(
                    f"[3] host={hostname} op=copy src={src} dest={dest} backup={backup} status=ko (Destination already exists)")
                sftp.close()
                return
    except FileNotFoundError:
        logger.info(
            f"[3] host={hostname} op=copy src={src} dest={dest} status=ko (Destination directory not found)")
        sftp.close()
        return

    # Construire le chemin de destination complet
    dest_path = os.path.join(dest, os.path.basename(src))
    # Copier le fichier/dossier de la machine locale vers l'hôte distant

    sftp.put(src, dest_path)
    sftp.close()
    logging.warning(
        f"[3] host={hostname} op=copy src={src} dest={dest} backup={backup} status=CHANGED")


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
    elif desired_state == 'absent':
        command = f'sudo apt-get remove -y {package_name}'
    else:
        print("Invalid desired_state value")
        return

    run_remote_cmd(command, ssh_client)


def service_management(service_name, desired_state, ssh_client):
    if desired_state in ['started', 'restarted', 'stopped']:
        if desired_state == 'started':
            command = f'sudo systemctl start {service_name}'
        elif desired_state == 'restarted':
            command = f'sudo systemctl restart {service_name}'
        else:
            command = f'sudo systemctl stop {service_name}'
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

    # Collecter les informations sur les tâches et les hôtes
    tasks_count = sum(len(playbook_task.get('params', []))
                      for playbook_task in playbook)
    hosts = [host['hostname'] for host in inventory['hosts']]

    def connect_to_host():
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        return client

    logging.info(
        f"processing {tasks_count} tasks on hosts: {', '.join(hosts)}")

    # Parcourir les playbooks dans le fichier de playbook
    for playbook_task in playbook:
        hosts = playbook_task.get('hosts')
        params = playbook_task.get('params')
        modules = playbook_task.get('module')

        # Parcourir les hôtes spécifiés dans le playbook
        for host in inventory['hosts']:
            hostname = host['hostname']
            username = host['username']
            password = host['password']

            # Se connecter à l'hôte distant
            ssh_client = connect_to_host()
            logging.info(f"Connexion réussie à l'hôte : {hostname}")

            # Vérifier si des tâches sont définies
            if params:
                # Parcourir les tâches du playbook
                for param in params:
                    # Récupérer le nom du module
                    module = next(iter(param.keys()))
                    module_args = param.get(module)

                    # Exécuter l'action correspondante en fonction du module
                    if modules == 'apt':
                        package_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        apt_package_management(
                            package_name, desired_state, ssh_client)
                        logging.info(
                            f"[1] host={hostname} op=apt name={package_name} state={desired_state}")
                    elif modules == 'service':
                        service_name = module_args.get('name')
                        desired_state = module_args.get('state')
                        service_management(
                            service_name, desired_state, ssh_client)
                        logging.info(
                            f"[2] host={hostname} op=service name={service_name} state={desired_state}")
                    elif modules == 'copy':
                        src = module_args.get('src')
                        dest = module_args.get('dest')
                        backup = module_args.get('backup', False)
                        copy_module(src, dest, backup, ssh_client)
                        logging.info(
                            f"[3] host={hostname} op=copy src={src} dest={dest} backup={backup}")
                    elif modules == 'sysctl':
                        attribute = module_args.get('attribute')
                        value = module_args.get('value')
                        permanent = module_args.get('permanent', False)
                        sysctl_module(attribute, value, permanent, ssh_client)
                        logging.info(
                            f"[4] host={hostname} op=sysctl attribute={attribute} value={value} permanent={permanent}")
                    elif modules == 'command':
                        command = module_args.get('command')
                        shell = module_args.get('shell', '/bin/bash')
                        command_module(command, shell, ssh_client)
                        logging.info(
                            f"[5] host={hostname} op=command command={command} shell={shell}")
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
