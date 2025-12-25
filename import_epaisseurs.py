#!/usr/bin/env python3
"""
Script pour importer les épaisseurs standards dans Simple Wood
Exécuter avec: python3 import_epaisseurs.py

Les épaisseurs sont données par essence:
- ep_frais: épaisseur de sciage (bois frais)
- ep_sec: épaisseur après séchage (retrait)
"""

import requests

BASE_URL = "http://localhost:5000"

# Épaisseurs standards (à adapter selon vos besoins)
# Le retrait est d'environ 8-10% pour les feuillus
EPAISSEURS = [
    # Hêtre (HET)
    {"essence": "HET", "ep_frais": 20, "ep_sec": 18},
    {"essence": "HET", "ep_frais": 27, "ep_sec": 25},
    {"essence": "HET", "ep_frais": 30, "ep_sec": 27},
    {"essence": "HET", "ep_frais": 34, "ep_sec": 30},
    {"essence": "HET", "ep_frais": 42, "ep_sec": 38},
    {"essence": "HET", "ep_frais": 46, "ep_sec": 41},
    {"essence": "HET", "ep_frais": 55, "ep_sec": 50},
    {"essence": "HET", "ep_frais": 60, "ep_sec": 54},
    {"essence": "HET", "ep_frais": 67, "ep_sec": 60},
    {"essence": "HET", "ep_frais": 75, "ep_sec": 68},
    {"essence": "HET", "ep_frais": 85, "ep_sec": 76},
    
    # Chêne (CHE)
    {"essence": "CHE", "ep_frais": 20, "ep_sec": 18},
    {"essence": "CHE", "ep_frais": 27, "ep_sec": 25},
    {"essence": "CHE", "ep_frais": 30, "ep_sec": 27},
    {"essence": "CHE", "ep_frais": 34, "ep_sec": 30},
    {"essence": "CHE", "ep_frais": 42, "ep_sec": 38},
    {"essence": "CHE", "ep_frais": 46, "ep_sec": 41},
    {"essence": "CHE", "ep_frais": 55, "ep_sec": 50},
    {"essence": "CHE", "ep_frais": 60, "ep_sec": 54},
    {"essence": "CHE", "ep_frais": 75, "ep_sec": 68},
    
    # Frêne (FRE)
    {"essence": "FRE", "ep_frais": 27, "ep_sec": 25},
    {"essence": "FRE", "ep_frais": 34, "ep_sec": 30},
    {"essence": "FRE", "ep_frais": 42, "ep_sec": 38},
    {"essence": "FRE", "ep_frais": 55, "ep_sec": 50},
    {"essence": "FRE", "ep_frais": 67, "ep_sec": 60},
    
    # Érable (ERS)
    {"essence": "ERS", "ep_frais": 27, "ep_sec": 25},
    {"essence": "ERS", "ep_frais": 34, "ep_sec": 30},
    {"essence": "ERS", "ep_frais": 42, "ep_sec": 38},
    {"essence": "ERS", "ep_frais": 55, "ep_sec": 50},
    
    # Merisier (MER)
    {"essence": "MER", "ep_frais": 27, "ep_sec": 25},
    {"essence": "MER", "ep_frais": 34, "ep_sec": 30},
    {"essence": "MER", "ep_frais": 55, "ep_sec": 50},
    
    # Noyer (NOY)
    {"essence": "NOY", "ep_frais": 34, "ep_sec": 30},
    {"essence": "NOY", "ep_frais": 42, "ep_sec": 38},
    {"essence": "NOY", "ep_frais": 55, "ep_sec": 50},
]

def import_epaisseurs():
    print(f"Import de {len(EPAISSEURS)} épaisseurs...")
    
    success = 0
    errors = 0
    
    for e in EPAISSEURS:
        try:
            response = requests.post(
                f"{BASE_URL}/api/tables/epaisseurs/values",
                json=e,
                timeout=10
            )
            result = response.json()
            if result.get('success'):
                print(f"  ✓ {e['essence']} : {e['ep_frais']}mm → {e['ep_sec']}mm")
                success += 1
            else:
                print(f"  ✗ {e['essence']} {e['ep_frais']}mm - {result.get('message', 'Erreur')}")
                errors += 1
        except Exception as ex:
            print(f"  ✗ {e['essence']} {e['ep_frais']}mm - {ex}")
            errors += 1
    
    print(f"\nTerminé: {success} importées, {errors} erreurs")

if __name__ == "__main__":
    import_epaisseurs()
