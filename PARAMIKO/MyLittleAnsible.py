import time
import paramiko
import logging 
from getpass import getpass
import click
import jinja2
import yaml



def connect_to_host(hostname, username):
    client = paramiko.SSHClient()
    client.load_system_host_keys() # Méthode de connexion par default
    client.connect(hostname, username=username)
    return client


def execute_playbook(playbook_file, inventory_file):
    # Charger le fichier de playbook YAML
    with open(playbook_file, 'r') as file:
        playbook = yaml.safe_load(file)

    # Charger le fichier d'inventaire YAML
    with open(inventory_file, 'r') as file:
        inventory = yaml.safe_load(file)

    # Parcourir les hôtes dans l'inventaire
    for host in inventory['hosts']:
        hostname = host['hostname']
        username = host['username']

        # Se connecter à l'hôte distant
        client = connect_to_host(hostname, username)
        print(f"Connexion réussie à l'hôte : {hostname}")

        # Exécuter les actions du playbook
        for action in playbook['actions']:
            # Utiliser Jinja2 pour rendre les templates
            template = jinja2.Template(action['command'])
            rendered_command = template.render(hostname=hostname)

            # Exécuter la commande sur l'hôte distant
            stdin, stdout, stderr = client.exec_command(rendered_command)

            # Afficher les résultats
            print(f"Commande exécutée sur {hostname}:")
            print(stdout.read().decode())
            time.sleep(.5)

        # Fermer la connexion SSH
        client.close()


@click.command()
@click.option('-f', '--playbook', required=True, help='Chemin vers le fichier de playbook')
@click.option('-i', '--inventory', required=True, help='Chemin vers le fichier d\'inventaire')

def main(playbook, inventory):
    execute_playbook(playbook, inventory)


if __name__ == '__main__':
    main()

