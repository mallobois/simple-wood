#!/bin/bash
# Simple Wood - Installation et mise à jour
# Usage: curl -sSL https://raw.githubusercontent.com/mallobois/simple-wood/main/install.sh | bash

set -e

REPO="https://github.com/mallobois/simple-wood.git"
DIR="$HOME/simple-wood"

echo "================================"
echo "  Simple Wood - MALLO BOIS"
echo "================================"
echo ""

# Installation ou mise à jour
if [ -d "$DIR" ]; then
    echo "→ Mise à jour..."
    cd "$DIR"
    git pull
else
    echo "→ Installation..."
    git clone "$REPO" "$DIR"
    cd "$DIR"
    
    echo "→ Création environnement Python..."
    python3 -m venv venv
fi

echo "→ Installation dépendances..."
source venv/bin/activate
pip install --quiet flask gspread google-auth

# Vérifier credentials.json
if [ ! -f "$DIR/credentials.json" ]; then
    echo ""
    echo "⚠ ATTENTION: credentials.json manquant !"
    echo "  Copiez votre fichier credentials.json dans $DIR/"
    echo "  pour activer Google Sheets"
    echo ""
fi

echo ""
echo "✓ Terminé !"
echo ""
echo "Pour lancer : cd ~/simple-wood && source venv/bin/activate && python3 app.py"
echo ""

# Demander si on veut installer le service systemd
read -p "Installer le démarrage automatique ? (o/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Oo]$ ]]; then
    echo "→ Installation du service..."
    
    sudo tee /etc/systemd/system/simple-wood.service > /dev/null << EOF
[Unit]
Description=Simple Wood - Etiquettes Zebra
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DIR
Environment=PATH=$DIR/venv/bin
ExecStart=$DIR/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable simple-wood
    sudo systemctl restart simple-wood
    
    echo ""
    echo "✓ Service installé et démarré !"
    echo ""
    echo "Commandes utiles :"
    echo "  sudo systemctl status simple-wood   # Voir le statut"
    echo "  sudo systemctl restart simple-wood  # Redémarrer"
    echo "  sudo systemctl stop simple-wood     # Arrêter"
    echo ""
fi

# Afficher l'IP
IP=$(hostname -I | awk '{print $1}')
echo "Accès : http://$IP:5000"
echo ""
