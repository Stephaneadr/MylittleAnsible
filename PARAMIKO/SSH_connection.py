import time
from getpass import getpass
import click
import jinja2
import yaml
import paramiko


hostname = "192.168.1.21"
username = "stef"


client = paramiko.SSHClient()

choice = input ("choisi t'a méthode de connexion :\n 1 - Username/Password\n 2 - Key-file\n")

def SSH_connection(choice):
    if choice == "1":
        password = getpass('enter your password :')
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        stdin, stdout, stderr = client.exec_command("hostname")
        print(stdout.read().decode())
        time.sleep(.5)
        client.close()
    elif choice == "2":
        key_file = paramiko.Ed25519Key.from_private_key_file("/home/stef/.ssh/id_ed25519")
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username,pkey=key_file, allow_agent=False, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command("hostname")
        print(stdout.read().decode())
        time.sleep(.5)
        client.close()
    else :
        client.load_system_host_keys() # Première méthode know_host
        client.connect(hostname, username=username)
        stdin, stdout, stderr = client.exec_command("hostname")
        print(stdout.read().decode())
        time.sleep(.5)
        client.close()

SSH_connection(choice)
