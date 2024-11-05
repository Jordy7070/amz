# Système de Gestion d'Inventaire

Application Streamlit pour la gestion d'inventaire avec codes-barres EAN-128.

## Installation

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows
venv\Scripts\activate
# Sur Mac/Linux
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Configuration

1. Créer un dossier `.streamlit`
2. Ajouter le fichier `secrets.toml` avec la configuration MongoDB

## Lancement

```bash
streamlit run app.py
```

## Fonctionnalités

- Génération de codes-barres EAN-128
- Gestion d'inventaire
- Export de données
- Interface utilisateur intuitive
