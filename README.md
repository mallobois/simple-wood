# Simple Wood

Système d'étiquetage Zebra pour scierie - MALLO BOIS

## Installation sur Raspberry Pi

```bash
# Cloner le repo
git clone https://github.com/TON_USERNAME/simple-wood.git
cd simple-wood

# Créer l'environnement Python
python3 -m venv venv
source venv/bin/activate
pip install flask

# Lancer
python3 app.py
```

Accès : `http://<IP_RASPBERRY>:5000`

## Mise à jour

```bash
cd ~/simple-wood
git pull
source venv/bin/activate
python3 app.py
```

## Structure

```
simple-wood/
├── app.py              # Serveur Flask
├── config.json         # Configuration (créé au 1er lancement)
├── requirements.txt
└── templates/
    ├── index.html      # Accueil
    ├── troncons.html   # Étiquettes tronçons
    ├── paquets.html    # Étiquettes paquets
    ├── colis.html      # Étiquettes colis
    └── parametres.html # Configuration
```

## Configuration imprimante

Par défaut : `192.168.1.67:9100`

Modifiable dans Paramètres ou directement dans `config.json`.

---

ÉTABLISSEMENTS MALLO BOIS SAS — Réguisheim
