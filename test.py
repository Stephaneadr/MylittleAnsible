import paramiko
import os

# Informations de connexion SSH
hostname = 'adresse_ip_machine_virtuelle'
port = 22
username = 'nom_utilisateur'
password = 'mot_de_passe'

# Chemin du dossier source et destination
dossier_source = '/chemin/vers/dossier_source'
dossier_destination = '/chemin/vers/dossier_destination'

# Fonction récursive pour copier les fichiers et dossiers
def copier_dossier(sftp, source, destination):
    if sftp.isfile(source):
        sftp.get(source, destination)
    else:
        if not os.path.exists(destination):
            os.makedirs(destination)
        fichiers = sftp.listdir(source)
        for fichier in fichiers:
            copier_dossier(sftp, source + '/' + fichier, destination + '/' + fichier)

# Connexion SSH et copie du dossier
try:
    # Connexion SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname, port, username, password)

    # Création d'une instance de SFTP
    sftp = ssh_client.open_sftp()

    # Copie du dossier
    copier_dossier(sftp, dossier_source, dossier_destination)

    # Fermeture de la connexion SFTP
    sftp.close()

    # Fermeture de la connexion SSH
    ssh_client.close()

    print("Copie terminée avec succès.")
except Exception as e:
    print("Erreur lors de la copie :", str(e))



ef copy_directory_ssh(hostname, port, username, password, source_dir, destination_dir):
    # Établir une connexion SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password)

    # Copier le dossier et son contenu
    scp = ssh.open_sftp()
    scp.put(source_dir, destination_dir, recursive=True)
    scp.close()

    # Fermer la connexion SSH
    ssh.close()

# Paramètres de connexion SSH
hostname = 'adresse_ip'
port = 22
username = 'utilisateur'
password = 'mot_de_passe'

# Dossier source et destination
source_dir = '/chemin/du/dossier/source'
destination_dir = '/chemin/du/dossier/destination'