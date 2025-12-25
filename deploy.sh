#!/bin/bash
# Script de mise à jour et déploiement simple-wood
# Usage: ./deploy.sh [message de commit]

cd ~/Documents/GitHub/simple-wood

echo "================================"
echo "  Simple Wood - Déploiement"
echo "================================"
echo ""

# 1. Vérifier qu'aucun fichier sensible n'est staged
echo "→ Vérification des fichiers sensibles..."
SENSITIVE_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E "(credentials|password|secret|\.key|\.env|config\.json)" || true)
SENSITIVE_STAGED=$(git status --porcelain | grep -E "(credentials|password|secret|\.key|\.env|config\.json)" | grep -v "^??" || true)

if [ -n "$SENSITIVE_FILES" ] || [ -n "$SENSITIVE_STAGED" ]; then
    echo ""
    echo "⚠️  ATTENTION: Fichiers sensibles détectés !"
    echo "$SENSITIVE_FILES"
    echo "$SENSITIVE_STAGED"
    echo ""
    echo "Ces fichiers ne seront PAS poussés."
    echo "Retrait des fichiers sensibles du staging..."
    git reset HEAD credentials.json 2>/dev/null
    git reset HEAD config.json 2>/dev/null
    git reset HEAD .env 2>/dev/null
    echo ""
fi

# 2. Arrêter Flask s'il tourne
echo "→ Arrêt du serveur local..."
pkill -f "flask run" 2>/dev/null
pkill -f "python3 app.py" 2>/dev/null
sleep 1

# 3. Afficher les fichiers modifiés
echo "→ Fichiers à commiter :"
git status --short
echo ""

# 4. Vérification finale avant push
FINAL_CHECK=$(git diff --cached --name-only | grep -E "(credentials|password|secret|\.key|\.env)" || true)
if [ -n "$FINAL_CHECK" ]; then
    echo "❌ ERREUR: Fichiers sensibles toujours présents. Abandon."
    exit 1
fi

# 5. Pousser sur GitHub
COMMIT_MSG="${1:-Mise à jour Claude}"
echo "→ Commit: $COMMIT_MSG"
git add .

# Re-vérifier après git add
git reset HEAD credentials.json 2>/dev/null
git reset HEAD config.json 2>/dev/null
git reset HEAD .env 2>/dev/null

git commit -m "$COMMIT_MSG"
git push

echo ""
echo "→ Relance du serveur local..."

# 6. Activer l'environnement virtuel et relancer Flask
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run --port 5001 &

sleep 2
echo ""
echo "================================"
echo "✓ Déploiement terminé !"
echo ""
echo "Local:  http://localhost:5001"
echo "GitHub: https://github.com/mallobois/simple-wood"
echo ""
echo "Sur Raspberry: cd ~/simple-wood && git pull"
echo "================================"
