#!/usr/bin/env python3
"""
Script pour importer toutes les données de référence dans Simple Wood
Exécuter avec: python3 import_all.py

Ordre d'import:
1. Essences (car référencées par qualités et épaisseurs)
2. Produits (car référencés par qualités)
3. Épaisseurs
4. Qualités (optionnel - à remplir manuellement)
"""

import subprocess
import sys

scripts = [
    ("Essences", "import_essences.py"),
    ("Produits", "import_produits.py"),
    ("Épaisseurs", "import_epaisseurs.py"),
]

print("=" * 50)
print("IMPORT DES DONNÉES DE RÉFÉRENCE - SIMPLE WOOD")
print("=" * 50)
print()

for name, script in scripts:
    print(f"\n{'='*20} {name} {'='*20}")
    result = subprocess.run([sys.executable, script], cwd="/Users/y/Documents/GitHub/simple-wood")
    if result.returncode != 0:
        print(f"⚠️  Erreur lors de l'import de {name}")

print("\n" + "=" * 50)
print("IMPORT TERMINÉ")
print("=" * 50)
print("\nN'oubliez pas de remplir la table des QUALITÉS")
print("(combinaisons Essence × Produit × Code qualité)")
print()
