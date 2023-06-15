from jinja2 import Environment, FileSystemLoader

# Configuration de l'environnement Jinja2
env = Environment(loader=FileSystemLoader('/chemin/vers/le/dossier/du/template'))

# Charger le template
template = env.get_template('template.html')

# Variables à utiliser dans le template
variables = {
    'nom': 'John Doe',
    'age': 30
}

# Rendu du template avec les variables
resultat = template.render(variables)

# Écrire le résultat dans un fichier de sortie
chemin_sortie = '/chemin/vers/le/dossier/de/sortie/fichier_sortie.html'
with open(chemin_sortie, 'w') as f:
    f.write(resultat)

print("Le rendu du template a été écrit dans le fichier de sortie.")