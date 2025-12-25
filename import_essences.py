#!/usr/bin/env python3
"""
Script pour importer les essences ONF dans Simple Wood
Exécuter avec: python3 import_essences.py
"""

import requests

BASE_URL = "http://localhost:5000"

ESSENCES = [
    # Feuillus principaux
    {"code": "HET", "nom": "Hêtre", "nom_latin": "Fagus sylvatica", "densite_frais": 950, "densite_sec": 650},
    {"code": "CHE", "nom": "Chêne indigène", "nom_latin": "Quercus", "densite_frais": 1070, "densite_sec": 720},
    {"code": "CHS", "nom": "Chêne sessile", "nom_latin": "Quercus petraea", "densite_frais": 1070, "densite_sec": 720},
    {"code": "CHP", "nom": "Chêne pédonculé", "nom_latin": "Quercus robur", "densite_frais": 1070, "densite_sec": 720},
    {"code": "CHX", "nom": "Chêne sessile ou pédonculé", "nom_latin": "Quercus petraea/robur", "densite_frais": 1070, "densite_sec": 720},
    {"code": "FRE", "nom": "Frêne", "nom_latin": "Fraxinus", "densite_frais": 920, "densite_sec": 680},
    {"code": "FRC", "nom": "Frêne commun", "nom_latin": "Fraxinus excelsior", "densite_frais": 920, "densite_sec": 680},
    {"code": "CHT", "nom": "Châtaignier", "nom_latin": "Castanea sativa", "densite_frais": 950, "densite_sec": 590},
    {"code": "MER", "nom": "Merisier", "nom_latin": "Prunus avium", "densite_frais": 900, "densite_sec": 620},
    {"code": "CHA", "nom": "Charme", "nom_latin": "Carpinus betulus", "densite_frais": 1000, "densite_sec": 750},
    {"code": "NOY", "nom": "Noyer", "nom_latin": "Juglans regia", "densite_frais": 900, "densite_sec": 680},
    {"code": "ROB", "nom": "Robinier", "nom_latin": "Robinia pseudoacacia", "densite_frais": 950, "densite_sec": 770},
    {"code": "ERP", "nom": "Érable plane", "nom_latin": "Acer platanoides", "densite_frais": 900, "densite_sec": 650},
    {"code": "ERC", "nom": "Érable champêtre", "nom_latin": "Acer campestre", "densite_frais": 900, "densite_sec": 650},
    {"code": "ERS", "nom": "Érable sycomore", "nom_latin": "Acer pseudoplatanus", "densite_frais": 900, "densite_sec": 650},
    {"code": "BOU", "nom": "Bouleau", "nom_latin": "Betula", "densite_frais": 850, "densite_sec": 650},
    {"code": "TRE", "nom": "Tremble", "nom_latin": "Populus tremula", "densite_frais": 800, "densite_sec": 500},
    {"code": "PEU", "nom": "Peuplier", "nom_latin": "Populus", "densite_frais": 800, "densite_sec": 450},
    {"code": "TIL", "nom": "Tilleul", "nom_latin": "Tilia", "densite_frais": 800, "densite_sec": 530},
    {"code": "ALT", "nom": "Alisier torminal", "nom_latin": "Sorbus torminalis", "densite_frais": 950, "densite_sec": 750},
    {"code": "ALB", "nom": "Alisier blanc", "nom_latin": "Sorbus aria", "densite_frais": 950, "densite_sec": 750},
    {"code": "COR", "nom": "Cormier", "nom_latin": "Sorbus domestica", "densite_frais": 950, "densite_sec": 750},
    {"code": "SOR", "nom": "Sorbier des oiseleurs", "nom_latin": "Sorbus aucuparia", "densite_frais": 900, "densite_sec": 700},
    {"code": "AUN", "nom": "Aulne glutineux", "nom_latin": "Alnus glutinosa", "densite_frais": 850, "densite_sec": 530},
    {"code": "SAU", "nom": "Saule", "nom_latin": "Salix", "densite_frais": 800, "densite_sec": 450},
    {"code": "ORM", "nom": "Orme", "nom_latin": "Ulmus", "densite_frais": 950, "densite_sec": 680},
    
    # Résineux
    {"code": "EPC", "nom": "Épicéa commun", "nom_latin": "Picea abies", "densite_frais": 860, "densite_sec": 470},
    {"code": "EPS", "nom": "Épicéa de Sitka", "nom_latin": "Picea sitchensis", "densite_frais": 850, "densite_sec": 450},
    {"code": "DOU", "nom": "Douglas", "nom_latin": "Pseudotsuga menziesii", "densite_frais": 850, "densite_sec": 530},
    {"code": "MEE", "nom": "Mélèze d'Europe", "nom_latin": "Larix decidua", "densite_frais": 900, "densite_sec": 590},
    {"code": "MEJ", "nom": "Mélèze du Japon", "nom_latin": "Larix kaempferi", "densite_frais": 900, "densite_sec": 590},
    {"code": "P.S", "nom": "Pin sylvestre", "nom_latin": "Pinus sylvestris", "densite_frais": 850, "densite_sec": 520},
    {"code": "P.M", "nom": "Pin maritime", "nom_latin": "Pinus pinaster", "densite_frais": 900, "densite_sec": 530},
    {"code": "P.N", "nom": "Pin noir", "nom_latin": "Pinus nigra", "densite_frais": 900, "densite_sec": 550},
    {"code": "P.L", "nom": "Pin laricio", "nom_latin": "Pinus nigra laricio", "densite_frais": 900, "densite_sec": 550},
    {"code": "P.W", "nom": "Pin Weymouth", "nom_latin": "Pinus strobus", "densite_frais": 800, "densite_sec": 400},
    {"code": "S.P", "nom": "Sapin pectiné", "nom_latin": "Abies alba", "densite_frais": 850, "densite_sec": 450},
    {"code": "S.N", "nom": "Sapin de Nordmann", "nom_latin": "Abies nordmanniana", "densite_frais": 850, "densite_sec": 450},
    {"code": "CEA", "nom": "Cèdre de l'Atlas", "nom_latin": "Cedrus atlantica", "densite_frais": 850, "densite_sec": 580},
    {"code": "CYP", "nom": "Cyprès", "nom_latin": "Cupressus", "densite_frais": 800, "densite_sec": 510},
    
    # Codes génériques
    {"code": "F.D", "nom": "Feuillu dur", "nom_latin": "", "densite_frais": 950, "densite_sec": 700},
    {"code": "F.T", "nom": "Feuillu tendre", "nom_latin": "", "densite_frais": 800, "densite_sec": 500},
    {"code": "A.R", "nom": "Autre résineux", "nom_latin": "", "densite_frais": 850, "densite_sec": 500},
    {"code": "XXX", "nom": "Toutes essences", "nom_latin": "", "densite_frais": 900, "densite_sec": 600},
]

def import_essences():
    print(f"Import de {len(ESSENCES)} essences...")
    
    success = 0
    errors = 0
    
    for e in ESSENCES:
        try:
            response = requests.post(
                f"{BASE_URL}/api/tables/essences/values",
                json=e,
                timeout=10
            )
            result = response.json()
            if result.get('success'):
                print(f"  ✓ {e['code']} - {e['nom']}")
                success += 1
            else:
                print(f"  ✗ {e['code']} - {result.get('message', 'Erreur')}")
                errors += 1
        except Exception as ex:
            print(f"  ✗ {e['code']} - {ex}")
            errors += 1
    
    print(f"\nTerminé: {success} importées, {errors} erreurs")

if __name__ == "__main__":
    import_essences()
