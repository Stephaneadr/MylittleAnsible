# 📦 MylittleAnsible

**MylittleAnsible** est un projet pédagogique visant à automatiser la configuration de systèmes via Ansible.  
Il est structuré autour de fichiers d'inventaire, de tâches et de modules personnalisés pour faciliter la gestion d'infrastructures.

## 🧰 Contenu du projet

- **`mla/`** : Contient les modules Ansible personnalisés développés dans le cadre du projet.
- **`inventory.yaml`** : Fichier d'inventaire définissant les hôtes et groupes cibles.
- **`todo.yaml`** : Liste des tâches à exécuter, organisées en playbooks Ansible.
- **`Documentation des modules.pdf`** : Documentation détaillée des modules personnalisés.
- **`.vscode/`** : Configuration de l'environnement de développement pour Visual Studio Code.

## 🚀 Prérequis

- [Ansible](https://www.ansible.com/) installé sur votre machine.
- Accès SSH aux hôtes définis dans `inventory.yaml`.

## ⚙️ Utilisation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/Stephaneadr/MylittleAnsible.git
   cd MylittleAnsible
```

2. Exécuter le playbook :
```
ansible-playbook -i inventory.yaml todo.yaml
```

## 📄 Documentation

La documentation des modules personnalisés est disponible dans le fichier `Documentation des modules.pdf`.  
Elle fournit des détails sur l'utilisation et le fonctionnement de chaque module.


