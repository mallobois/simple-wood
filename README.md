# Simple Wood

Système d'étiquetage Zebra

## Installation sur Raspberry Pi

```bash
# Installation automatique
curl -sSL https://raw.githubusercontent.com/mallobois/simple-wood/main/install.sh | bash
```

Puis copiez votre fichier `credentials.json` (Google Sheets) :
```bash
scp credentials.json pi@<IP_RASPBERRY>:~/simple-wood/
```

Accès : `http://<IP_RASPBERRY>:5000`

## Mise à jour

```bash
cd ~/simple-wood
git pull
sudo systemctl restart simple-wood
```

Ou via le bouton "Mettre à jour" dans Paramètres.

## Structure

```
simple-wood/
├── app.py              # Serveur Flask
├── config.json         # Configuration (créé au 1er lancement)
├── credentials.json    # Credentials Google Sheets (non commité)
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

## Google Sheets

Chaque impression est loguée dans un Google Sheet avec 3 onglets :
- **Tronçons** : Date, Heure, Série, Numéro, Code, Copies, Opérateur
- **Paquets** : + Essence, Qualité, Dimensions, Volume
- **Colis** : + Client, Référence, Destination, Poids

---


