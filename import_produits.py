#!/usr/bin/env python3
"""
Script pour importer les produits dans Simple Wood
Exécuter avec: python3 import_produits.py
"""

import requests

BASE_URL = "http://localhost:5000"

PRODUITS = [
    {"code": "GRU", "nom": "Grumes"},
    {"code": "TRO", "nom": "Tronçons"},
    {"code": "PQT", "nom": "Paquets"},
    {"code": "PDB", "nom": "Prédébits"},
    {"code": "PNX", "nom": "Panneaux"},
]

def import_produits():
    print(f"Import de {len(PRODUITS)} produits...")
    
    success = 0
    errors = 0
    
    for p in PRODUITS:
        try:
            response = requests.post(
                f"{BASE_URL}/api/tables/produits/values",
                json=p,
                timeout=10
            )
            result = response.json()
            if result.get('success'):
                print(f"  ✓ {p['code']} - {p['nom']}")
                success += 1
            else:
                print(f"  ✗ {p['code']} - {result.get('message', 'Erreur')}")
                errors += 1
        except Exception as ex:
            print(f"  ✗ {p['code']} - {ex}")
            errors += 1
    
    print(f"\nTerminé: {success} importés, {errors} erreurs")

if __name__ == "__main__":
    import_produits()
