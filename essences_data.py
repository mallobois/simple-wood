# ============================================================================
# DONNÉES DE RÉFÉRENCE - ESSENCES
# ============================================================================
# PSF = Point de Saturation des Fibres (%)
# retrait_t = Retrait tangentiel total PSF → 0% (%)
# retrait_r = Retrait radial total PSF → 0% (%)
# ratio_t_r = Rapport T/R (>2 = bois nerveux)
# temp_max = Température max séchoir (°C)
# risque_fentes = Sensibilité aux fentes (1=faible, 5=élevé)
# risque_collapse = Sensibilité au collapse (1=faible, 5=élevé)
# duree_27mm = Durée séchage indicative pour 27mm (jours)
# durete = Dureté Monnin (N/mm²)
# silice = Teneur en silice (%)
# fil = Type de fil
# grain = Grosseur du grain
# durabilite = Classe durabilité naturelle (1=très durable, 5=non durable)
# impregnabilite = Classe imprégnabilité (1=facile, 4=non imprégnable)
# aubier = Distinction aubier/duramen
# couleur = Description couleur
# couleur_hex = Code couleur hexadécimal
# Sources: CIRAD, Wood Handbook, FCBA, CTBA, Wood Database

ESSENCES_DATA = [
    # ==================== FEUILLUS - BOIS NERVEUX ====================
    {
        "code": "HET", "nom": "Hêtre", "nom_latin": "Fagus sylvatica",
        "nom_en": "European Beech", "nom_de": "Rotbuche",
        "densite_frais": 950, "densite_sec": 720,
        "psf": 32, "retrait_t": 11.8, "retrait_r": 5.8, "ratio_t_r": 2.0,
        "temp_max": 65, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 35,
        "durete": 34, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 1, "aubier": "non distinct",
        "couleur": "blanc rosé à brun clair", "couleur_hex": "#D4A574"
    },
    {
        "code": "CHA", "nom": "Charme", "nom_latin": "Carpinus betulus",
        "nom_en": "European Hornbeam", "nom_de": "Hainbuche",
        "densite_frais": 1000, "densite_sec": 800,
        "psf": 30, "retrait_t": 11.5, "retrait_r": 6.5, "ratio_t_r": 1.8,
        "temp_max": 55, "risque_fentes": 4, "risque_collapse": 3, "duree_27mm": 50,
        "durete": 45, "silice": 0, "fil": "irrégulier", "grain": "fin",
        "durabilite": 5, "impregnabilite": 3, "aubier": "non distinct",
        "couleur": "blanc grisâtre", "couleur_hex": "#C8C0B0"
    },
    # ==================== FEUILLUS - CHÊNES ====================
    {
        "code": "CHE", "nom": "Chêne indigène", "nom_latin": "Quercus",
        "nom_en": "European Oak", "nom_de": "Eiche",
        "densite_frais": 1070, "densite_sec": 720,
        "psf": 29, "retrait_t": 10.0, "retrait_r": 4.5, "ratio_t_r": 2.2,
        "temp_max": 55, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 60,
        "durete": 38, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 2, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun jaune à brun foncé", "couleur_hex": "#A67C52"
    },
    {
        "code": "CHS", "nom": "Chêne sessile", "nom_latin": "Quercus petraea",
        "nom_en": "Sessile Oak", "nom_de": "Traubeneiche",
        "densite_frais": 1070, "densite_sec": 720,
        "psf": 29, "retrait_t": 9.8, "retrait_r": 4.3, "ratio_t_r": 2.3,
        "temp_max": 55, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 60,
        "durete": 38, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 2, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun miel", "couleur_hex": "#B8860B"
    },
    {
        "code": "CHP", "nom": "Chêne pédonculé", "nom_latin": "Quercus robur",
        "nom_en": "Pedunculate Oak", "nom_de": "Stieleiche",
        "densite_frais": 1070, "densite_sec": 720,
        "psf": 29, "retrait_t": 10.2, "retrait_r": 4.6, "ratio_t_r": 2.2,
        "temp_max": 55, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 65,
        "durete": 38, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 2, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun jaune", "couleur_hex": "#A67C52"
    },
    {
        "code": "CHR", "nom": "Chêne rouge", "nom_latin": "Quercus rubra",
        "nom_en": "Red Oak", "nom_de": "Roteiche",
        "densite_frais": 1000, "densite_sec": 660,
        "psf": 27, "retrait_t": 8.6, "retrait_r": 4.0, "ratio_t_r": 2.2,
        "temp_max": 60, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 45,
        "durete": 32, "silice": 0, "fil": "droit", "grain": "grossier",
        "durabilite": 4, "impregnabilite": 2, "aubier": "distinct",
        "couleur": "brun rosé à rouge", "couleur_hex": "#B5651D"
    },
    # ==================== FEUILLUS - FRÊNES ====================
    {
        "code": "FRE", "nom": "Frêne", "nom_latin": "Fraxinus",
        "nom_en": "European Ash", "nom_de": "Esche",
        "densite_frais": 920, "densite_sec": 690,
        "psf": 28, "retrait_t": 8.0, "retrait_r": 5.0, "ratio_t_r": 1.6,
        "temp_max": 70, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 25,
        "durete": 34, "silice": 0, "fil": "droit", "grain": "grossier",
        "durabilite": 5, "impregnabilite": 2, "aubier": "non distinct",
        "couleur": "blanc crème à brun clair", "couleur_hex": "#E8DCC4"
    },
    {
        "code": "FRC", "nom": "Frêne commun", "nom_latin": "Fraxinus excelsior",
        "nom_en": "Common Ash", "nom_de": "Gemeine Esche",
        "densite_frais": 920, "densite_sec": 690,
        "psf": 28, "retrait_t": 8.0, "retrait_r": 5.0, "ratio_t_r": 1.6,
        "temp_max": 70, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 25,
        "durete": 34, "silice": 0, "fil": "droit", "grain": "grossier",
        "durabilite": 5, "impregnabilite": 2, "aubier": "non distinct",
        "couleur": "blanc crème à brun clair", "couleur_hex": "#E8DCC4"
    },
    # ==================== FEUILLUS - DIVERS ====================
    {
        "code": "CHT", "nom": "Châtaignier", "nom_latin": "Castanea sativa",
        "nom_en": "Sweet Chestnut", "nom_de": "Edelkastanie",
        "densite_frais": 950, "densite_sec": 590,
        "psf": 30, "retrait_t": 6.5, "retrait_r": 3.5, "ratio_t_r": 1.9,
        "temp_max": 55, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 40,
        "durete": 18, "silice": 0, "fil": "droit à spiralé", "grain": "grossier",
        "durabilite": 2, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun jaune à brun foncé", "couleur_hex": "#8B7355"
    },
    {
        "code": "MER", "nom": "Merisier", "nom_latin": "Prunus avium",
        "nom_en": "Wild Cherry", "nom_de": "Vogelkirsche",
        "densite_frais": 900, "densite_sec": 620,
        "psf": 29, "retrait_t": 7.5, "retrait_r": 3.8, "ratio_t_r": 2.0,
        "temp_max": 50, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 35,
        "durete": 30, "silice": 0, "fil": "droit à ondulé", "grain": "fin",
        "durabilite": 4, "impregnabilite": 3, "aubier": "distinct",
        "couleur": "brun rosé à rouge doré", "couleur_hex": "#B5651D"
    },
    {
        "code": "NOY", "nom": "Noyer", "nom_latin": "Juglans regia",
        "nom_en": "European Walnut", "nom_de": "Walnuss",
        "densite_frais": 900, "densite_sec": 680,
        "psf": 27, "retrait_t": 7.5, "retrait_r": 5.5, "ratio_t_r": 1.4,
        "temp_max": 55, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 35,
        "durete": 28, "silice": 0, "fil": "droit à ondulé", "grain": "moyen",
        "durabilite": 3, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun gris à brun chocolat", "couleur_hex": "#5C4033"
    },
    {
        "code": "NON", "nom": "Noyer noir", "nom_latin": "Juglans nigra",
        "nom_en": "Black Walnut", "nom_de": "Schwarznuss",
        "densite_frais": 900, "densite_sec": 610,
        "psf": 26, "retrait_t": 7.8, "retrait_r": 5.5, "ratio_t_r": 1.4,
        "temp_max": 55, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 35,
        "durete": 26, "silice": 0, "fil": "droit à ondulé", "grain": "moyen",
        "durabilite": 3, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun chocolat à noir violacé", "couleur_hex": "#3D2314"
    },
    {
        "code": "ROB", "nom": "Robinier", "nom_latin": "Robinia pseudoacacia",
        "nom_en": "Black Locust", "nom_de": "Robinie",
        "densite_frais": 950, "densite_sec": 770,
        "psf": 26, "retrait_t": 5.0, "retrait_r": 3.0, "ratio_t_r": 1.7,
        "temp_max": 65, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 30,
        "durete": 46, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 1, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "jaune verdâtre à brun doré", "couleur_hex": "#9B8B4E"
    },
    # ==================== FEUILLUS - ÉRABLES ====================
    {
        "code": "ERP", "nom": "Érable plane", "nom_latin": "Acer platanoides",
        "nom_en": "Norway Maple", "nom_de": "Spitzahorn",
        "densite_frais": 900, "densite_sec": 650,
        "psf": 29, "retrait_t": 8.0, "retrait_r": 3.0, "ratio_t_r": 2.7,
        "temp_max": 55, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 35,
        "durete": 30, "silice": 0, "fil": "droit à ondulé", "grain": "fin",
        "durabilite": 5, "impregnabilite": 3, "aubier": "non distinct",
        "couleur": "blanc crème à jaunâtre", "couleur_hex": "#F5DEB3"
    },
    {
        "code": "ERC", "nom": "Érable champêtre", "nom_latin": "Acer campestre",
        "nom_en": "Field Maple", "nom_de": "Feldahorn",
        "densite_frais": 900, "densite_sec": 650,
        "psf": 29, "retrait_t": 7.8, "retrait_r": 3.2, "ratio_t_r": 2.4,
        "temp_max": 55, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 35,
        "durete": 32, "silice": 0, "fil": "droit à ondulé", "grain": "fin",
        "durabilite": 5, "impregnabilite": 3, "aubier": "non distinct",
        "couleur": "blanc crème à rosé", "couleur_hex": "#F5DEB3"
    },
    {
        "code": "ERS", "nom": "Érable sycomore", "nom_latin": "Acer pseudoplatanus",
        "nom_en": "Sycamore Maple", "nom_de": "Bergahorn",
        "densite_frais": 900, "densite_sec": 650,
        "psf": 29, "retrait_t": 8.5, "retrait_r": 3.5, "ratio_t_r": 2.4,
        "temp_max": 55, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 35,
        "durete": 32, "silice": 0, "fil": "droit à ondulé", "grain": "fin",
        "durabilite": 5, "impregnabilite": 3, "aubier": "non distinct",
        "couleur": "blanc nacré", "couleur_hex": "#FFFAF0"
    },
    # ==================== FEUILLUS - BOIS BLANCS ====================
    {
        "code": "BOU", "nom": "Bouleau", "nom_latin": "Betula",
        "nom_en": "Birch", "nom_de": "Birke",
        "densite_frais": 850, "densite_sec": 650,
        "psf": 28, "retrait_t": 7.5, "retrait_r": 5.5, "ratio_t_r": 1.4,
        "temp_max": 60, "risque_fentes": 2, "risque_collapse": 2, "duree_27mm": 25,
        "durete": 22, "silice": 0, "fil": "droit à ondulé", "grain": "fin",
        "durabilite": 5, "impregnabilite": 2, "aubier": "non distinct",
        "couleur": "blanc crème à jaune pâle", "couleur_hex": "#F5F5DC"
    },
    {
        "code": "TRE", "nom": "Tremble", "nom_latin": "Populus tremula",
        "nom_en": "Aspen", "nom_de": "Zitterpappel",
        "densite_frais": 800, "densite_sec": 500,
        "psf": 29, "retrait_t": 8.5, "retrait_r": 3.5, "ratio_t_r": 2.4,
        "temp_max": 70, "risque_fentes": 2, "risque_collapse": 3, "duree_27mm": 20,
        "durete": 12, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 1, "aubier": "non distinct",
        "couleur": "blanc grisâtre", "couleur_hex": "#E8E4D9"
    },
    {
        "code": "PEU", "nom": "Peuplier", "nom_latin": "Populus",
        "nom_en": "Poplar", "nom_de": "Pappel",
        "densite_frais": 800, "densite_sec": 450,
        "psf": 29, "retrait_t": 8.5, "retrait_r": 3.5, "ratio_t_r": 2.4,
        "temp_max": 75, "risque_fentes": 1, "risque_collapse": 3, "duree_27mm": 15,
        "durete": 10, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 1, "aubier": "non distinct",
        "couleur": "blanc crème à gris", "couleur_hex": "#E8E4D9"
    },
    {
        "code": "TIL", "nom": "Tilleul", "nom_latin": "Tilia",
        "nom_en": "Linden", "nom_de": "Linde",
        "densite_frais": 800, "densite_sec": 530,
        "psf": 31, "retrait_t": 9.5, "retrait_r": 5.5, "ratio_t_r": 1.7,
        "temp_max": 60, "risque_fentes": 2, "risque_collapse": 2, "duree_27mm": 25,
        "durete": 12, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 1, "aubier": "non distinct",
        "couleur": "blanc jaunâtre à rosé", "couleur_hex": "#F5E6D3"
    },
    {
        "code": "AUN", "nom": "Aulne glutineux", "nom_latin": "Alnus glutinosa",
        "nom_en": "Common Alder", "nom_de": "Schwarzerle",
        "densite_frais": 850, "densite_sec": 530,
        "psf": 29, "retrait_t": 7.3, "retrait_r": 4.0, "ratio_t_r": 1.8,
        "temp_max": 60, "risque_fentes": 2, "risque_collapse": 2, "duree_27mm": 25,
        "durete": 15, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 2, "aubier": "non distinct",
        "couleur": "orange rosé à brun rougeâtre", "couleur_hex": "#CD853F"
    },
    # ==================== FEUILLUS - FRUITIERS & SORBUS ====================
    {
        "code": "ALT", "nom": "Alisier torminal", "nom_latin": "Sorbus torminalis",
        "nom_en": "Wild Service Tree", "nom_de": "Elsbeere",
        "densite_frais": 950, "densite_sec": 750,
        "psf": 30, "retrait_t": 10.0, "retrait_r": 5.0, "ratio_t_r": 2.0,
        "temp_max": 50, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 50,
        "durete": 40, "silice": 0, "fil": "droit", "grain": "très fin",
        "durabilite": 4, "impregnabilite": 3, "aubier": "peu distinct",
        "couleur": "brun rosé satiné", "couleur_hex": "#C9A080"
    },
    {
        "code": "ALB", "nom": "Alisier blanc", "nom_latin": "Sorbus aria",
        "nom_en": "Whitebeam", "nom_de": "Mehlbeere",
        "densite_frais": 950, "densite_sec": 750,
        "psf": 30, "retrait_t": 9.5, "retrait_r": 4.8, "ratio_t_r": 2.0,
        "temp_max": 50, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 50,
        "durete": 38, "silice": 0, "fil": "droit", "grain": "très fin",
        "durabilite": 4, "impregnabilite": 3, "aubier": "peu distinct",
        "couleur": "blanc rosé", "couleur_hex": "#D4A080"
    },
    {
        "code": "COR", "nom": "Cormier", "nom_latin": "Sorbus domestica",
        "nom_en": "Service Tree", "nom_de": "Speierling",
        "densite_frais": 950, "densite_sec": 800,
        "psf": 30, "retrait_t": 10.5, "retrait_r": 5.2, "ratio_t_r": 2.0,
        "temp_max": 45, "risque_fentes": 5, "risque_collapse": 3, "duree_27mm": 60,
        "durete": 48, "silice": 0, "fil": "droit", "grain": "très fin",
        "durabilite": 3, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun rouge à brun foncé", "couleur_hex": "#8B4513"
    },
    {
        "code": "ORM", "nom": "Orme", "nom_latin": "Ulmus",
        "nom_en": "Elm", "nom_de": "Ulme",
        "densite_frais": 950, "densite_sec": 680,
        "psf": 28, "retrait_t": 8.0, "retrait_r": 4.5, "ratio_t_r": 1.8,
        "temp_max": 55, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 40,
        "durete": 30, "silice": 0, "fil": "contrefil fréquent", "grain": "grossier",
        "durabilite": 4, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun clair à brun rougeâtre", "couleur_hex": "#A0826D"
    },
    {
        "code": "PLA", "nom": "Platane", "nom_latin": "Platanus acerifolia",
        "nom_en": "Plane Tree", "nom_de": "Platane",
        "densite_frais": 900, "densite_sec": 620,
        "psf": 28, "retrait_t": 8.5, "retrait_r": 4.5, "ratio_t_r": 1.9,
        "temp_max": 55, "risque_fentes": 3, "risque_collapse": 2, "duree_27mm": 35,
        "durete": 28, "silice": 0, "fil": "contrefil", "grain": "fin",
        "durabilite": 5, "impregnabilite": 2, "aubier": "peu distinct",
        "couleur": "brun rosé maillé", "couleur_hex": "#C9A080"
    },
    {
        "code": "MAR", "nom": "Marronnier", "nom_latin": "Aesculus hippocastanum",
        "nom_en": "Horse Chestnut", "nom_de": "Rosskastanie",
        "densite_frais": 850, "densite_sec": 510,
        "psf": 30, "retrait_t": 8.0, "retrait_r": 3.0, "ratio_t_r": 2.7,
        "temp_max": 60, "risque_fentes": 2, "risque_collapse": 2, "duree_27mm": 25,
        "durete": 14, "silice": 0, "fil": "spiralé", "grain": "fin",
        "durabilite": 5, "impregnabilite": 1, "aubier": "non distinct",
        "couleur": "blanc crème à jaunâtre", "couleur_hex": "#F5F5DC"
    },
    {
        "code": "SAU", "nom": "Saule blanc", "nom_latin": "Salix alba",
        "nom_en": "White Willow", "nom_de": "Silberweide",
        "densite_frais": 750, "densite_sec": 450,
        "psf": 28, "retrait_t": 8.5, "retrait_r": 4.0, "ratio_t_r": 2.1,
        "temp_max": 65, "risque_fentes": 2, "risque_collapse": 3, "duree_27mm": 20,
        "durete": 10, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 1, "aubier": "non distinct",
        "couleur": "blanc rosé à grisâtre", "couleur_hex": "#E8DCC4"
    },
    {
        "code": "POI", "nom": "Poirier", "nom_latin": "Pyrus communis",
        "nom_en": "Pear", "nom_de": "Birnbaum",
        "densite_frais": 950, "densite_sec": 700,
        "psf": 28, "retrait_t": 10.0, "retrait_r": 4.5, "ratio_t_r": 2.2,
        "temp_max": 50, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 45,
        "durete": 35, "silice": 0, "fil": "droit", "grain": "très fin",
        "durabilite": 4, "impregnabilite": 3, "aubier": "non distinct",
        "couleur": "rose saumon à brun rosé", "couleur_hex": "#D4A080"
    },
    {
        "code": "POM", "nom": "Pommier", "nom_latin": "Malus domestica",
        "nom_en": "Apple", "nom_de": "Apfelbaum",
        "densite_frais": 950, "densite_sec": 700,
        "psf": 28, "retrait_t": 10.0, "retrait_r": 4.5, "ratio_t_r": 2.2,
        "temp_max": 50, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 45,
        "durete": 35, "silice": 0, "fil": "droit à irrégulier", "grain": "très fin",
        "durabilite": 4, "impregnabilite": 3, "aubier": "peu distinct",
        "couleur": "brun rougeâtre", "couleur_hex": "#B07050"
    },
    {
        "code": "PRU", "nom": "Prunier", "nom_latin": "Prunus domestica",
        "nom_en": "Plum", "nom_de": "Zwetschgenbaum",
        "densite_frais": 950, "densite_sec": 750,
        "psf": 28, "retrait_t": 9.0, "retrait_r": 4.0, "ratio_t_r": 2.3,
        "temp_max": 50, "risque_fentes": 4, "risque_collapse": 2, "duree_27mm": 45,
        "durete": 38, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 4, "impregnabilite": 3, "aubier": "distinct",
        "couleur": "brun violacé à rouge", "couleur_hex": "#6B3A3A"
    },
    {
        "code": "MIC", "nom": "Micocoulier", "nom_latin": "Celtis australis",
        "nom_en": "European Hackberry", "nom_de": "Zürgelbaum",
        "densite_frais": 900, "densite_sec": 650,
        "psf": 27, "retrait_t": 8.0, "retrait_r": 4.0, "ratio_t_r": 2.0,
        "temp_max": 60, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 30,
        "durete": 30, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 4, "impregnabilite": 2, "aubier": "non distinct",
        "couleur": "jaune grisâtre", "couleur_hex": "#C8B896"
    },
    # ==================== RÉSINEUX ====================
    {
        "code": "EPC", "nom": "Épicéa commun", "nom_latin": "Picea abies",
        "nom_en": "Norway Spruce", "nom_de": "Fichte",
        "densite_frais": 860, "densite_sec": 470,
        "psf": 30, "retrait_t": 8.0, "retrait_r": 4.0, "ratio_t_r": 2.0,
        "temp_max": 80, "risque_fentes": 1, "risque_collapse": 1, "duree_27mm": 15,
        "durete": 12, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 4, "impregnabilite": 4, "aubier": "non distinct",
        "couleur": "blanc crème à jaune pâle", "couleur_hex": "#F5E6C8"
    },
    {
        "code": "DOU", "nom": "Douglas", "nom_latin": "Pseudotsuga menziesii",
        "nom_en": "Douglas Fir", "nom_de": "Douglasie",
        "densite_frais": 850, "densite_sec": 530,
        "psf": 26, "retrait_t": 7.6, "retrait_r": 4.8, "ratio_t_r": 1.6,
        "temp_max": 75, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 20,
        "durete": 18, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 3, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun rosé à rouge orangé", "couleur_hex": "#C98B6A"
    },
    {
        "code": "MEE", "nom": "Mélèze d'Europe", "nom_latin": "Larix decidua",
        "nom_en": "European Larch", "nom_de": "Europäische Lärche",
        "densite_frais": 900, "densite_sec": 590,
        "psf": 28, "retrait_t": 7.8, "retrait_r": 3.3, "ratio_t_r": 2.4,
        "temp_max": 70, "risque_fentes": 3, "risque_collapse": 1, "duree_27mm": 30,
        "durete": 19, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 3, "impregnabilite": 4, "aubier": "distinct",
        "couleur": "brun rouge veiné", "couleur_hex": "#A0522D"
    },
    {
        "code": "PIS", "nom": "Pin sylvestre", "nom_latin": "Pinus sylvestris",
        "nom_en": "Scots Pine", "nom_de": "Waldkiefer",
        "densite_frais": 850, "densite_sec": 520,
        "psf": 28, "retrait_t": 7.5, "retrait_r": 4.0, "ratio_t_r": 1.9,
        "temp_max": 75, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 20,
        "durete": 16, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 4, "impregnabilite": 3, "aubier": "distinct",
        "couleur": "jaune rougeâtre", "couleur_hex": "#D4A460"
    },
    {
        "code": "PIM", "nom": "Pin maritime", "nom_latin": "Pinus pinaster",
        "nom_en": "Maritime Pine", "nom_de": "Seekiefer",
        "densite_frais": 900, "densite_sec": 530,
        "psf": 29, "retrait_t": 8.0, "retrait_r": 4.5, "ratio_t_r": 1.8,
        "temp_max": 75, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 20,
        "durete": 15, "silice": 0, "fil": "droit", "grain": "grossier",
        "durabilite": 4, "impregnabilite": 2, "aubier": "distinct",
        "couleur": "jaune à brun rosé", "couleur_hex": "#D4A460"
    },
    {
        "code": "PIN", "nom": "Pin noir", "nom_latin": "Pinus nigra",
        "nom_en": "Black Pine", "nom_de": "Schwarzkiefer",
        "densite_frais": 900, "densite_sec": 550,
        "psf": 28, "retrait_t": 7.5, "retrait_r": 4.0, "ratio_t_r": 1.9,
        "temp_max": 75, "risque_fentes": 2, "risque_collapse": 1, "duree_27mm": 20,
        "durete": 17, "silice": 0, "fil": "droit", "grain": "moyen",
        "durabilite": 4, "impregnabilite": 3, "aubier": "distinct",
        "couleur": "jaune orangé", "couleur_hex": "#D4A460"
    },
    {
        "code": "SAP", "nom": "Sapin pectiné", "nom_latin": "Abies alba",
        "nom_en": "Silver Fir", "nom_de": "Weißtanne",
        "densite_frais": 850, "densite_sec": 450,
        "psf": 30, "retrait_t": 7.5, "retrait_r": 3.8, "ratio_t_r": 2.0,
        "temp_max": 80, "risque_fentes": 1, "risque_collapse": 1, "duree_27mm": 15,
        "durete": 11, "silice": 0, "fil": "droit", "grain": "fin",
        "durabilite": 5, "impregnabilite": 3, "aubier": "non distinct",
        "couleur": "blanc crème à jaune pâle", "couleur_hex": "#F5E6C8"
    },
]
