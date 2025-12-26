#!/usr/bin/env python3
"""
MALLO BOIS - WoodStock
Système d'étiquetage industriel pour scierie
Flask + Google Sheets + Zebra ZPL
"""

import os
import json
import socket
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

import gspread
from google.oauth2.service_account import Credentials

# ============================================================================
# CONFIGURATION
# ============================================================================

app = Flask(__name__)
app.secret_key = 'mallo-bois-woodstock-2024'

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / 'config.json'
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'

SPREADSHEET_ID = '1dSPJFr8Nq5RwanZBKszpFwXXvacHROG_9MAD8FRgiOk'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

gs_client = None
spreadsheet = None

# ============================================================================
# DONNÉES DE RÉFÉRENCE - ESSENCES (BASE TECHNIQUE COMPLÈTE)
# ============================================================================
# Sources: CIRAD, Wood Handbook, FCBA, CTBA, Wood Database
#
# IDENTIFICATION:
#   code, nom, nom_latin, nom_en, nom_de
#
# DENSITÉS:
#   densite_frais (kg/m³), densite_sec (kg/m³)
#
# RETRAIT (PSF → 0%):
#   psf = Point de Saturation des Fibres (%)
#   retrait_t = Retrait tangentiel (%)
#   retrait_r = Retrait radial (%)
#   ratio_t_r = Rapport T/R (>2 = bois nerveux)
#
# SÉCHAGE:
#   temp_max = Température max séchoir (°C)
#   risque_fentes = Sensibilité aux fentes (1=faible, 5=élevé)
#   risque_collapse = Sensibilité au collapse (1=faible, 5=élevé)
#   duree_27mm = Durée séchage indicative pour 27mm (jours)
#
# USINAGE:
#   durete = Dureté Monnin (N/mm²)
#   silice = Teneur en silice (%)
#   fil = Type de fil (droit, ondulé, contrefil, spiralé, irrégulier)
#   grain = Grosseur du grain (très fin, fin, moyen, grossier)
#
# DURABILITÉ:
#   durabilite = Classe durabilité naturelle (1=très durable, 5=non durable)
#   impregnabilite = Classe imprégnabilité (1=facile, 4=non imprégnable)
#   aubier = Distinction aubier/duramen (distinct, peu distinct, non distinct)
#
# ASPECT:
#   couleur = Description couleur
#   couleur_hex = Code couleur hexadécimal

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

PRODUITS_DATA = [
    {"code": "GRU", "nom": "Grumes"},
    {"code": "TRO", "nom": "Tronçons"},
    {"code": "PQT", "nom": "Paquets"},
    {"code": "PDB", "nom": "Prédébits"},
    {"code": "PNX", "nom": "Panneaux"},
]

# ============================================================================
# CALCUL AUTOMATIQUE DES ÉPAISSEURS
# ============================================================================
# Siccité cible: 8% (standard min 8%, max 10%)
# Formule: retrait_effectif = retrait_t × (PSF - H_cible) / PSF
#          ep_frais = ep_sec / (1 - retrait_effectif)

HUMIDITE_CIBLE = 8  # %
EPAISSEURS_CIBLES = [18, 27, 32, 45, 50, 80]  # mm sec


def _calculer_epaisseurs():
    """Calcule les épaisseurs frais pour chaque essence et épaisseur sèche cible"""
    result = []
    for ess in ESSENCES_DATA:
        code = ess["code"]
        psf = ess["psf"]
        retrait_t = ess["retrait_t"]
        retrait_eff = (retrait_t / 100) * (psf - HUMIDITE_CIBLE) / psf
        for ep_sec in EPAISSEURS_CIBLES:
            ep_frais = round(ep_sec / (1 - retrait_eff))
            result.append({"essence": code, "ep_frais": ep_frais, "ep_sec": ep_sec})
    return result


EPAISSEURS_DATA = _calculer_epaisseurs()


def _afficher_tableau_epaisseurs():
    """Affiche le tableau des épaisseurs au démarrage"""
    print("\n" + "=" * 90)
    print("  📐 TABLEAU DES ÉPAISSEURS (frais → sec à 8%)")
    print("=" * 90)
    print(f"{'Essence':<8} {'PSF':>4} {'Ret.T':>6} {'T/R':>5} │ " + " │ ".join(f"{e:>2}mm" for e in EPAISSEURS_CIBLES))
    print("-" * 90)
    for ess in ESSENCES_DATA:
        code = ess["code"]
        psf = ess["psf"]
        rt = ess["retrait_t"]
        tr = ess.get("ratio_t_r", rt / ess.get("retrait_r", 5))
        eps = [e for e in EPAISSEURS_DATA if e["essence"] == code]
        vals = " │ ".join(f"{e['ep_frais']:>4}" for e in eps)
        print(f"{code:<8} {psf:>3}% {rt:>5.1f}% {tr:>4.1f} │ {vals}")
    print("=" * 90)
    print(f"  {len(ESSENCES_DATA)} essences × {len(EPAISSEURS_CIBLES)} épaisseurs = {len(EPAISSEURS_DATA)} combinaisons")
    print()


# ============================================================================
# CONFIGURATION PAR DÉFAUT
# ============================================================================

DEFAULT_CONFIG = {
    'printers': [
        {'id': 'zebra1', 'nom': 'Zebra Principale', 'ip': '192.168.1.67', 'port': 9100}
    ],
    'postes': [
        {
            'id': 'achats', 'nom': 'Achats et réception', 'description': 'Gestion des achats et réceptions',
            'serie': '2501', 'compteur': 0, 'prefixe': 'ACH-', 'printer': 'zebra1',
            'copies_defaut': 1, 'champs': []
        },
        {
            'id': 'grumier', 'nom': 'Réception grumier', 'description': 'Réception des grumes',
            'serie': '2501', 'compteur': 0, 'prefixe': 'GRU-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'GRU', 'champs': []
        },
        {
            'id': 'tronconnage', 'nom': 'Tronçonnage', 'description': 'Découpe des grumes en tronçons',
            'serie': '2501', 'compteur': 0, 'prefixe': 'TRO-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'TRO', 'source_poste': 'grumier', 'champs': []
        },
        {
            'id': 'sciage', 'nom': 'Sciage', 'description': 'Sciage des tronçons',
            'serie': '2501', 'compteur': 0, 'prefixe': 'SCI-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'PQT', 'source_poste': 'tronconnage', 'champs': []
        },
        {
            'id': 'paquets', 'nom': 'Paquets', 'description': 'Mise en paquets',
            'serie': '2501', 'compteur': 0, 'prefixe': 'PQT-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'PQT', 'source_poste': 'sciage', 'champs': []
        },
        {
            'id': 'sechage', 'nom': 'Séchage', 'description': 'Gestion du séchage',
            'serie': '2501', 'compteur': 0, 'prefixe': 'SEC-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'PQT', 'source_poste': 'paquets', 'champs': []
        },
        {
            'id': 'delignage', 'nom': 'Délignage', 'description': 'Délignage des planches',
            'serie': '2501', 'compteur': 0, 'prefixe': 'DEL-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'PDB', 'source_poste': 'sechage', 'champs': []
        },
        {
            'id': 'decoupe', 'nom': 'Découpe', 'description': 'Découpe des prédébits',
            'serie': '2501', 'compteur': 0, 'prefixe': 'DEC-', 'printer': 'zebra1',
            'copies_defaut': 1, 'type_produit': 'PDB', 'source_poste': 'delignage', 'champs': []
        },
        {
            'id': 'colis', 'nom': 'Colis', 'description': 'Préparation des colis',
            'serie': '2501', 'compteur': 0, 'prefixe': 'COL-', 'printer': 'zebra1',
            'copies_defaut': 1, 'champs': []
        },
        {
            'id': 'expeditions', 'nom': 'Expéditions', 'description': 'Gestion des expéditions',
            'serie': '2501', 'compteur': 0, 'prefixe': 'EXP-', 'printer': 'zebra1',
            'copies_defaut': 1, 'champs': []
        },
        {
            'id': 'inventaire', 'nom': 'Inventaire', 'description': 'Inventaire du stock',
            'serie': '2501', 'compteur': 0, 'prefixe': 'INV-', 'printer': 'zebra1',
            'copies_defaut': 1, 'champs': []
        }
    ],
    'tables': [
        {
            'id': 'essences', 'nom': 'Essences',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'},
                {'id': 'nom_latin', 'nom': 'Nom latin', 'type': 'text'},
                {'id': 'nom_en', 'nom': 'Nom EN', 'type': 'text'},
                {'id': 'nom_de', 'nom': 'Nom DE', 'type': 'text'},
                {'id': 'densite_frais', 'nom': 'Densité frais', 'type': 'number'},
                {'id': 'densite_sec', 'nom': 'Densité sec', 'type': 'number'},
                {'id': 'psf', 'nom': 'PSF %', 'type': 'number'},
                {'id': 'retrait_t', 'nom': 'Retrait T %', 'type': 'number'},
                {'id': 'retrait_r', 'nom': 'Retrait R %', 'type': 'number'},
                {'id': 'ratio_t_r', 'nom': 'Ratio T/R', 'type': 'number'},
                {'id': 'temp_max', 'nom': 'Temp max °C', 'type': 'number'},
                {'id': 'risque_fentes', 'nom': 'Risque fentes', 'type': 'number'},
                {'id': 'risque_collapse', 'nom': 'Risque collapse', 'type': 'number'},
                {'id': 'duree_27mm', 'nom': 'Durée 27mm (j)', 'type': 'number'},
                {'id': 'durete', 'nom': 'Dureté Monnin', 'type': 'number'},
                {'id': 'fil', 'nom': 'Fil', 'type': 'text'},
                {'id': 'grain', 'nom': 'Grain', 'type': 'text'},
                {'id': 'durabilite', 'nom': 'Durabilité', 'type': 'number'},
                {'id': 'impregnabilite', 'nom': 'Imprégnabilité', 'type': 'number'},
                {'id': 'aubier', 'nom': 'Aubier', 'type': 'text'},
                {'id': 'couleur', 'nom': 'Couleur', 'type': 'text'},
                {'id': 'couleur_hex', 'nom': 'Couleur hex', 'type': 'text'}
            ]
        },
        {
            'id': 'produits', 'nom': 'Produits',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'}
            ]
        },
        {
            'id': 'qualites', 'nom': 'Qualités',
            'colonnes': [
                {'id': 'essence', 'nom': 'Essence', 'type': 'ref', 'ref_table': 'essences', 'ref_col': 'Code'},
                {'id': 'produit', 'nom': 'Produit', 'type': 'ref', 'ref_table': 'produits', 'ref_col': 'Code'},
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'}
            ]
        },
        {
            'id': 'epaisseurs', 'nom': 'Épaisseurs',
            'colonnes': [
                {'id': 'essence', 'nom': 'Essence', 'type': 'ref', 'ref_table': 'essences', 'ref_col': 'Code'},
                {'id': 'ep_frais', 'nom': 'Ép. frais (mm)', 'type': 'number'},
                {'id': 'ep_sec', 'nom': 'Ép. sec (mm)', 'type': 'number'}
            ]
        },
        {
            'id': 'forets', 'nom': 'Forêts',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'},
                {'id': 'departement', 'nom': 'Département', 'type': 'text'}
            ]
        },
        {
            'id': 'lots', 'nom': 'Lots',
            'colonnes': [
                {'id': 'numero', 'nom': 'Numéro', 'type': 'text'},
                {'id': 'foret', 'nom': 'Forêt', 'type': 'ref', 'ref_table': 'forets', 'ref_col': 'Nom'},
                {'id': 'date_achat', 'nom': 'Date achat', 'type': 'date'},
                {'id': 'volume', 'nom': 'Volume m³', 'type': 'number'}
            ]
        }
    ]
}

# ============================================================================
# DÉCORATEURS
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('user_droits') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ============================================================================
# GOOGLE SHEETS
# ============================================================================

def init_google_sheets():
    global gs_client, spreadsheet
    try:
        if CREDENTIALS_FILE.exists():
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            gs_client = gspread.authorize(creds)
            spreadsheet = gs_client.open_by_key(SPREADSHEET_ID)
            print("✓ Google Sheets connecté")
            init_users_sheet()
        else:
            print("⚠ credentials.json non trouvé")
    except Exception as e:
        print(f"⚠ Erreur Google Sheets: {e}")


def init_users_sheet():
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        if len(sheet.get_all_values()) <= 1:
            sheet.append_row(['admin', '123456', 'Administrateur', 'AD', 'admin', ''])
            sheet.append_row(['operateur', '111111', 'Opérateur', 'OP', 'operateur', ''])
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title='Utilisateurs', rows=100, cols=10)
        sheet.append_row(['Identifiant', 'Mot de passe', 'Nom', 'Initiales', 'Droits', 'Postes'])
        sheet.append_row(['admin', '123456', 'Administrateur', 'AD', 'admin', ''])
        sheet.append_row(['operateur', '111111', 'Opérateur', 'OP', 'operateur', ''])
        print("  → Onglet Utilisateurs créé")


def init_reference_tables():
    """Synchronise les tables de référence (ajoute les entrées manquantes en batch)"""
    if spreadsheet is None:
        return
    
    config = load_config()
    
    # Essences
    table_cfg = next((t for t in config.get('tables', []) if t['id'] == 'essences'), None)
    if table_cfg:
        sheet = get_or_create_table_sheet('essences', table_cfg)
        if sheet:
            existing = sheet.get_all_records()
            existing_codes = {str(e.get('Code', '')).upper() for e in existing}
            colonnes = table_cfg.get('colonnes', [])
            rows_to_add = []
            next_id = len(existing) + 1
            for item in ESSENCES_DATA:
                if item['code'].upper() not in existing_codes:
                    rows_to_add.append([next_id] + [item.get(col['id'], '') for col in colonnes])
                    next_id += 1
            if rows_to_add:
                sheet.append_rows(rows_to_add)
                print(f"  → Essences: {len(rows_to_add)} ajoutée(s)")
    
    # Produits
    table_cfg = next((t for t in config.get('tables', []) if t['id'] == 'produits'), None)
    if table_cfg:
        sheet = get_or_create_table_sheet('produits', table_cfg)
        if sheet:
            existing = sheet.get_all_records()
            existing_codes = {str(e.get('Code', '')).upper() for e in existing}
            colonnes = table_cfg.get('colonnes', [])
            rows_to_add = []
            next_id = len(existing) + 1
            for item in PRODUITS_DATA:
                if item['code'].upper() not in existing_codes:
                    rows_to_add.append([next_id] + [item.get(col['id'], '') for col in colonnes])
                    next_id += 1
            if rows_to_add:
                sheet.append_rows(rows_to_add)
                print(f"  → Produits: {len(rows_to_add)} ajouté(s)")
    
    # Épaisseurs
    table_cfg = next((t for t in config.get('tables', []) if t['id'] == 'epaisseurs'), None)
    if table_cfg:
        sheet = get_or_create_table_sheet('epaisseurs', table_cfg)
        if sheet:
            existing = sheet.get_all_records()
            existing_keys = {
                (str(e.get('Essence', '')).upper(), int(e.get('Ép. sec (mm)', 0) or 0))
                for e in existing
            }
            colonnes = table_cfg.get('colonnes', [])
            rows_to_add = []
            next_id = len(existing) + 1
            for item in EPAISSEURS_DATA:
                key = (item['essence'].upper(), item['ep_sec'])
                if key not in existing_keys:
                    rows_to_add.append([next_id] + [item.get(col['id'], '') for col in colonnes])
                    next_id += 1
            if rows_to_add:
                sheet.append_rows(rows_to_add)
                print(f"  → Épaisseurs: {len(rows_to_add)} ajoutée(s)")


def get_or_create_poste_sheet(poste_id: str, poste_config: dict):
    sheet_name = f"Poste_{poste_id}"
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        headers = ['Date', 'Heure', 'Série', 'Numéro']
        if poste_config.get('type_produit'):
            headers.extend(['Essence', 'Qualité', 'Épaisseur'])
        if poste_config.get('source_poste'):
            headers.append('Source')
        for field in poste_config.get('champs', []):
            headers.append(field['nom'])
        headers.extend(['Copies', 'Opérateur'])
        sheet.append_row(headers)
        return sheet


def log_to_poste_sheet(poste_id: str, poste_config: dict, data: dict, copies: int, operateur: str):
    if spreadsheet is None:
        return
    try:
        sheet = get_or_create_poste_sheet(poste_id, poste_config)
        now = datetime.now()
        row = [now.strftime('%d/%m/%Y'), now.strftime('%H:%M:%S'), poste_config.get('serie', '2501'), data.get('numero', '')]
        if poste_config.get('type_produit'):
            row.extend([data.get('essence', ''), data.get('qualite', ''), data.get('epaisseur', '')])
        if poste_config.get('source_poste'):
            row.append(data.get('source', ''))
        for field in poste_config.get('champs', []):
            row.append(data.get(field['id'], ''))
        row.extend([copies, operateur])
        sheet.append_row(row)
    except Exception as e:
        print(f"Erreur log: {e}")


def get_poste_history(poste_id: str, limit: int = 50) -> list:
    if spreadsheet is None:
        return []
    try:
        sheet = spreadsheet.worksheet(f"Poste_{poste_id}")
        records = sheet.get_all_records()
        return list(reversed(records[-limit:]))
    except:
        return []


# ============================================================================
# TABLES DE RÉFÉRENCE
# ============================================================================

def get_or_create_table_sheet(table_id: str, table_config: dict):
    if spreadsheet is None:
        return None
    sheet_name = f"Table_{table_id}"
    colonnes = table_config.get('colonnes', [{'id': 'valeur', 'nom': 'Valeur'}])
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=len(colonnes) + 1)
        headers = ['ID'] + [c['nom'] for c in colonnes]
        sheet.append_row(headers)
        print(f"  → Table {table_config.get('nom', table_id)} créée")
        return sheet


def get_table_values(table_id: str, table_config: dict = None) -> list:
    if spreadsheet is None:
        return []
    try:
        sheet = spreadsheet.worksheet(f"Table_{table_id}")
        return sheet.get_all_records()
    except:
        return []


def add_table_value(table_id: str, table_config: dict, data: dict) -> bool:
    if spreadsheet is None:
        return False
    try:
        sheet = spreadsheet.worksheet(f"Table_{table_id}")
        records = sheet.get_all_records()
        new_id = len(records) + 1
        colonnes = table_config.get('colonnes', [])
        row = [new_id] + [data.get(col['id'], '') for col in colonnes]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Erreur ajout table: {e}")
        return False


def update_table_value(table_id: str, table_config: dict, row_id: int, data: dict) -> bool:
    if spreadsheet is None:
        return False
    try:
        sheet = spreadsheet.worksheet(f"Table_{table_id}")
        records = sheet.get_all_records()
        colonnes = table_config.get('colonnes', [])
        for i, row in enumerate(records):
            if row.get('ID') == row_id:
                row_num = i + 2
                for j, col in enumerate(colonnes):
                    sheet.update_cell(row_num, j + 2, data.get(col['id'], ''))
                return True
        return False
    except Exception as e:
        print(f"Erreur update: {e}")
        return False


def delete_table_value(table_id: str, row_id: int) -> bool:
    if spreadsheet is None:
        return False
    try:
        sheet = spreadsheet.worksheet(f"Table_{table_id}")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if row.get('ID') == row_id:
                sheet.delete_rows(i + 2)
                return True
        return False
    except Exception as e:
        print(f"Erreur delete: {e}")
        return False


# ============================================================================
# UTILISATEURS
# ============================================================================

def get_users() -> dict:
    default = {'admin': {'password': '123456', 'nom': 'Administrateur', 'initiales': 'AD', 'droits': 'admin', 'postes': []}}
    if spreadsheet is None:
        return default
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        if not records:
            return default
        users = {}
        for row in records:
            uid = row.get('Identifiant', '')
            if uid:
                nom = row.get('Nom', uid)
                postes_str = str(row.get('Postes', ''))
                users[uid] = {
                    'password': str(row.get('Mot de passe', '')),
                    'nom': nom,
                    'initiales': row.get('Initiales', nom[:2].upper()),
                    'droits': row.get('Droits', 'operateur'),
                    'postes': [p.strip() for p in postes_str.split(',') if p.strip()]
                }
        return users if users else default
    except Exception as e:
        print(f"Erreur utilisateurs: {e}")
        return default


# ============================================================================
# CONFIGURATION
# ============================================================================

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in ['printers', 'postes', 'tables']:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG.get(key, [])
                return config
        except Exception as e:
            print(f"Erreur config: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")


def get_poste(config: dict, poste_id: str) -> dict:
    for p in config.get('postes', []):
        if p['id'] == poste_id:
            return p
    return None


def get_printer(config: dict, printer_id: str) -> dict:
    for p in config.get('printers', []):
        if p.get('id') == printer_id:
            return p
    if config.get('printers'):
        return config['printers'][0]
    return {'ip': '192.168.1.67', 'port': 9100}


# ============================================================================
# IMPRESSION ZPL
# ============================================================================

def send_zpl(zpl_code: str, printer: dict) -> dict:
    ip = printer.get('ip', '192.168.1.67')
    port = printer.get('port', 9100)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((ip, port))
            sock.sendall(zpl_code.encode('utf-8'))
        return {'success': True, 'message': f'Envoyé à {ip}:{port}'}
    except socket.timeout:
        return {'success': False, 'message': 'Timeout connexion'}
    except ConnectionRefusedError:
        return {'success': False, 'message': 'Connexion refusée'}
    except OSError as e:
        return {'success': False, 'message': str(e)}


def format_numero(n: int, spaced: bool = True) -> str:
    s = f"{n:06d}"
    return f"{s[0:2]} {s[2:4]} {s[4:6]}" if spaced else s


def generate_zpl(poste: dict, data: dict, source: str = '') -> str:
    serie = poste.get('serie', '2501')
    compteur = poste.get('compteur', 0)
    prefixe = poste.get('prefixe', '')
    numero = format_numero(compteur)
    qr_data = f"{prefixe}{serie}-{format_numero(compteur, spaced=False)}"
    
    lines = []
    y = 180
    
    essence = data.get('essence', '')
    if essence:
        line = essence
        if data.get('qualite'):
            line += f" · {data['qualite']}"
        if data.get('epaisseur'):
            ep = data['epaisseur'].split('/')[0] if '/' in data['epaisseur'] else data['epaisseur']
            line += f" · {ep}mm"
        lines.append(f"^FO400,{y}^A0N,28,28^FD{line}^FS")
        y += 35
    
    if source:
        lines.append(f"^FO400,{y}^A0N,22,22^FDSource: {source}^FS")
        y += 30
    
    for field in poste.get('champs', []):
        value = data.get(field['id'], '')
        if value:
            lines.append(f"^FO400,{y}^A0N,22,22^FD{field['nom']}: {value}^FS")
            y += 28
    
    champs_zpl = '\n'.join(lines)
    
    return f"""^XA
^CI28
^PW812
^LL406
^LH0,0
~SD25
^FO30,28
^BQN,2,12
^FDQA,{qr_data}^FS
^FO400,30^A0N,36,36^FD{serie}^FS
^FO400,80^A0N,80,80^FD{numero}^FS
{champs_zpl}
^FO400,360^A0N,24,24^FDMALLO BOIS^FS
^FO30,370^A0N,18,18^FD{datetime.now().strftime('%d/%m/%Y')}^FS
^XZ"""


# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')
        users = get_users()
        if username in users and users[username]['password'] == password:
            session['user'] = username
            session['user_nom'] = users[username]['nom']
            session['user_droits'] = users[username].get('droits', 'operateur')
            session['user_postes'] = users[username].get('postes', [])
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Code PIN incorrect'})
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    config = load_config()
    user_postes = session.get('user_postes', [])
    is_admin = session.get('user_droits') == 'admin'
    
    # Admin voit tous les postes, opérateur uniquement les siens
    if is_admin:
        postes = config.get('postes', [])
    else:
        postes = [p for p in config.get('postes', []) if p['id'] in user_postes]
    
    return render_template('index.html', user=session.get('user_nom', ''), droits=session.get('user_droits', 'operateur'), postes=postes)


# ============================================================================
# ROUTES POSTES
# ============================================================================

@app.route('/poste/<poste_id>')
@login_required
def page_poste(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    
    user_postes = session.get('user_postes', [])
    is_admin = session.get('user_droits') == 'admin'
    
    # Vérifier les droits : admin OK, sinon vérifier que le poste est autorisé
    if not is_admin and poste_id not in user_postes:
        return redirect(url_for('index'))
    
    # Templates spécifiques par poste
    if poste_id == 'achats':
        return render_template('poste_achats.html', poste=poste)
    
    return render_template('poste_tache.html', poste=poste, printers=config.get('printers', []))


@app.route('/poste/<poste_id>/parametres')
@admin_required
def page_poste_params(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    return render_template('poste_parametres.html', poste=poste, printers=config.get('printers', []), all_postes=config.get('postes', []))


@app.route('/poste/<poste_id>/liste')
@admin_required
def page_poste_liste(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    return render_template('poste_liste.html', poste=poste, history=get_poste_history(poste_id))


@app.route('/parametres')
@admin_required
def page_parametres():
    return render_template('parametres.html', config=load_config())


@app.route('/essences')
@admin_required
def page_essences():
    return render_template('essences.html')


# ============================================================================
# API UTILISATEURS
# ============================================================================

@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = get_users()
    return jsonify([{'id': uid, 'nom': d['nom'], 'initiales': d['initiales']} for uid, d in users.items()])


@app.route('/api/users/full', methods=['GET'])
def api_get_users_full():
    users = get_users()
    return jsonify([{'id': uid, 'nom': d['nom'], 'initiales': d['initiales'], 'droits': d.get('droits', 'operateur'), 'postes': d.get('postes', [])} for uid, d in users.items()])


@app.route('/api/users', methods=['POST'])
def api_create_user():
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    data = request.json
    uid = data.get('id', '').strip().lower()
    password = data.get('password', '')
    if not uid or not data.get('nom') or not data.get('initiales') or not password:
        return jsonify({'success': False, 'message': 'Champs requis manquants'})
    if len(password) < 6 or len(password) > 8 or not password.isdigit():
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    if uid in get_users():
        return jsonify({'success': False, 'message': 'Identifiant déjà utilisé'})
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        postes_str = ','.join(data.get('postes', []))
        sheet.append_row([uid, password, data['nom'], data['initiales'], data.get('droits', 'operateur'), postes_str])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/users', methods=['PUT'])
def api_update_user():
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    data = request.json
    uid = data.get('id', '').strip()
    password = data.get('password', '')
    if password and (len(password) < 6 or len(password) > 8 or not password.isdigit()):
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('Identifiant', '')).lower() == uid.lower():
                row_num = i + 2
                sheet.update_cell(row_num, 3, data.get('nom', ''))
                sheet.update_cell(row_num, 4, data.get('initiales', ''))
                sheet.update_cell(row_num, 5, data.get('droits', 'operateur'))
                sheet.update_cell(row_num, 6, ','.join(data.get('postes', [])))
                if password:
                    sheet.update_cell(row_num, 2, password)
                return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/users/<uid>', methods=['DELETE'])
def api_delete_user(uid):
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('Identifiant', '')).lower() == uid.lower():
                sheet.delete_rows(i + 2)
                return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Non trouvé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============================================================================
# API IMPRIMANTES
# ============================================================================

@app.route('/api/printers', methods=['GET'])
def api_get_printers():
    return jsonify(load_config().get('printers', []))


@app.route('/api/printers', methods=['POST'])
def api_create_printer():
    config = load_config()
    if len(config.get('printers', [])) >= 6:
        return jsonify({'success': False, 'message': 'Maximum 6 imprimantes'})
    data = request.json
    pid = data.get('id', '').strip().lower()
    if any(p['id'] == pid for p in config.get('printers', [])):
        return jsonify({'success': False, 'message': 'ID déjà utilisé'})
    config['printers'].append({'id': pid, 'nom': data.get('nom', '').strip(), 'ip': data.get('ip', '').strip(), 'port': int(data.get('port', 9100))})
    save_config(config)
    return jsonify({'success': True})


@app.route('/api/printers', methods=['PUT'])
def api_update_printer():
    config = load_config()
    data = request.json
    for p in config.get('printers', []):
        if p['id'] == data.get('id'):
            p.update({k: data[k] for k in ['nom', 'ip'] if k in data})
            if 'port' in data:
                p['port'] = int(data['port'])
            save_config(config)
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Non trouvée'})


@app.route('/api/printers/<pid>', methods=['DELETE'])
def api_delete_printer(pid):
    config = load_config()
    if len(config.get('printers', [])) <= 1:
        return jsonify({'success': False, 'message': 'Au moins une imprimante requise'})
    config['printers'] = [p for p in config['printers'] if p['id'] != pid]
    save_config(config)
    return jsonify({'success': True})


@app.route('/api/printers/<pid>/test', methods=['POST'])
def api_test_printer(pid):
    config = load_config()
    printer = get_printer(config, pid)
    test_zpl = f"^XA^CI28^PW812^LL203^FO50,30^A0N,40,40^FDTEST {printer.get('nom', 'Imprimante')}^FS^FO50,80^A0N,25,25^FDMALLO BOIS - WoodStock^FS^FO50,120^A0N,20,20^FD{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}^FS^FO50,160^A0N,18,18^FDIP: {printer.get('ip')}:{printer.get('port')}^FS^XZ"
    return jsonify(send_zpl(test_zpl, printer))


# ============================================================================
# API POSTES
# ============================================================================

@app.route('/api/postes', methods=['GET'])
def api_get_postes():
    return jsonify(load_config().get('postes', []))


@app.route('/api/postes', methods=['POST'])
def api_create_poste():
    config = load_config()
    data = request.json
    pid = data.get('id', '').strip().lower().replace(' ', '_')
    if not pid:
        return jsonify({'success': False, 'message': 'ID requis'})
    if any(p['id'] == pid for p in config.get('postes', [])):
        return jsonify({'success': False, 'message': 'ID déjà utilisé'})
    config['postes'].append({'id': pid, 'nom': data.get('nom', pid), 'description': data.get('description', ''), 'serie': data.get('serie', '2501'), 'compteur': 0, 'prefixe': data.get('prefixe', ''), 'printer': data.get('printer', config['printers'][0]['id'] if config['printers'] else 'zebra1'), 'copies_defaut': int(data.get('copies_defaut', 1)), 'champs': data.get('champs', [])})
    save_config(config)
    return jsonify({'success': True})


@app.route('/api/postes/<poste_id>', methods=['PUT'])
def api_update_poste(poste_id):
    config = load_config()
    data = request.json
    for p in config.get('postes', []):
        if p['id'] == poste_id:
            for key in ['nom', 'description', 'serie', 'prefixe', 'printer', 'type_produit', 'source_poste']:
                if key in data:
                    p[key] = data[key]
            if 'copies_defaut' in data:
                p['copies_defaut'] = int(data['copies_defaut'])
            if 'compteur' in data:
                p['compteur'] = int(data['compteur']) % 1000000
            if 'champs' in data:
                p['champs'] = data['champs']
            save_config(config)
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Non trouvé'})


@app.route('/api/postes/<poste_id>', methods=['DELETE'])
def api_delete_poste(poste_id):
    config = load_config()
    if len(config.get('postes', [])) <= 1:
        return jsonify({'success': False, 'message': 'Au moins un poste requis'})
    config['postes'] = [p for p in config['postes'] if p['id'] != poste_id]
    save_config(config)
    return jsonify({'success': True})


# ============================================================================
# API TABLES
# ============================================================================

@app.route('/api/tables', methods=['GET'])
def api_get_tables():
    return jsonify(load_config().get('tables', []))


@app.route('/api/tables', methods=['POST'])
def api_create_table():
    config = load_config()
    data = request.json
    tid = data.get('id', '').strip().lower().replace(' ', '_')
    nom = data.get('nom', '').strip()
    if not tid or not nom:
        return jsonify({'success': False, 'message': 'ID et nom requis'})
    if any(t['id'] == tid for t in config.get('tables', [])):
        return jsonify({'success': False, 'message': 'ID déjà utilisé'})
    table_cfg = {'id': tid, 'nom': nom, 'colonnes': data.get('colonnes', [{'id': 'valeur', 'nom': 'Valeur', 'type': 'text'}])}
    config.setdefault('tables', []).append(table_cfg)
    save_config(config)
    get_or_create_table_sheet(tid, table_cfg)
    return jsonify({'success': True})


@app.route('/api/tables/<table_id>', methods=['PUT'])
def api_update_table(table_id):
    config = load_config()
    data = request.json
    for t in config.get('tables', []):
        if t['id'] == table_id:
            if 'nom' in data:
                t['nom'] = data['nom']
            if 'colonnes' in data:
                t['colonnes'] = data['colonnes']
            save_config(config)
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Non trouvée'})


@app.route('/api/tables/<table_id>', methods=['DELETE'])
def api_delete_table(table_id):
    config = load_config()
    config['tables'] = [t for t in config.get('tables', []) if t['id'] != table_id]
    save_config(config)
    return jsonify({'success': True})


@app.route('/api/tables/<table_id>/values', methods=['GET'])
def api_get_table_values(table_id):
    config = load_config()
    table_cfg = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
    if table_cfg:
        get_or_create_table_sheet(table_id, table_cfg)
    return jsonify(get_table_values(table_id, table_cfg))


@app.route('/api/tables/<table_id>/values', methods=['POST'])
def api_add_table_value(table_id):
    config = load_config()
    table_cfg = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
    if not table_cfg:
        return jsonify({'success': False, 'message': 'Table non trouvée'})
    get_or_create_table_sheet(table_id, table_cfg)
    return jsonify({'success': add_table_value(table_id, table_cfg, request.json)})


@app.route('/api/tables/<table_id>/values/<int:row_id>', methods=['PUT'])
def api_update_table_value(table_id, row_id):
    config = load_config()
    table_cfg = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
    if not table_cfg:
        return jsonify({'success': False, 'message': 'Table non trouvée'})
    return jsonify({'success': update_table_value(table_id, table_cfg, row_id, request.json)})


@app.route('/api/tables/<table_id>/values/<int:row_id>', methods=['DELETE'])
def api_delete_table_value(table_id, row_id):
    return jsonify({'success': delete_table_value(table_id, row_id)})


@app.route('/api/qualites/<essence_code>/<produit_code>', methods=['GET'])
def api_get_qualites_filtrees(essence_code, produit_code):
    all_qualites = get_table_values('qualites')
    filtered = [q for q in all_qualites if q.get('Essence', '').upper() == essence_code.upper() and q.get('Produit', '').upper() == produit_code.upper()]
    return jsonify(filtered)


@app.route('/api/epaisseurs/<essence_code>', methods=['GET'])
def api_get_epaisseurs_filtrees(essence_code):
    all_ep = get_table_values('epaisseurs')
    filtered = [e for e in all_ep if e.get('Essence', '').upper() == essence_code.upper()]
    return jsonify(filtered)


# ============================================================================
# API IMPRESSION
# ============================================================================

@app.route('/api/print/<poste_id>', methods=['POST'])
def api_print(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return jsonify({'success': False, 'message': 'Poste non trouvé'})
    data = request.json or {}
    imprimer = data.get('imprimer', True)
    copies = min(max(int(data.get('copies', poste.get('copies_defaut', 1))), 0), 50)
    source = data.get('source', '')
    numero_imprime = format_numero(poste['compteur'])
    zpl = generate_zpl(poste, data, source)
    printer = get_printer(config, poste.get('printer', 'zebra1'))
    printed = 0
    result = {'success': True}
    if imprimer and copies > 0:
        for _ in range(copies):
            result = send_zpl(zpl, printer)
            if result['success']:
                printed += 1
            else:
                break
        if printed == 0:
            return jsonify({'success': False, 'message': result.get('message', 'Erreur impression'), 'compteur': poste['compteur']})
    log_data = {**data, 'numero': format_numero(poste['compteur'], spaced=False), 'source': source}
    log_to_poste_sheet(poste_id, poste, log_data, copies if imprimer else 0, session.get('user_nom', 'Inconnu'))
    for p in config['postes']:
        if p['id'] == poste_id:
            p['compteur'] = (p['compteur'] + 1) % 1000000
            break
    save_config(config)
    return jsonify({'success': True, 'message': f'N° {numero_imprime}' + (f' ({printed} copies)' if printed > 1 else ''), 'compteur': poste['compteur'] + 1, 'numero_imprime': numero_imprime})


@app.route('/api/poste/<poste_id>/history', methods=['GET'])
def api_poste_history(poste_id):
    return jsonify(get_poste_history(poste_id))


@app.route('/api/poste/<poste_id>/series', methods=['GET'])
def api_poste_series(poste_id):
    history = get_poste_history(poste_id, limit=500)
    series = {}
    for row in history:
        serie = str(row.get('Série', ''))
        numero = str(row.get('Numéro', ''))
        if serie and numero:
            series.setdefault(serie, [])
            if numero not in series[serie]:
                series[serie].append(numero)
    for s in series:
        series[s].sort()
    return jsonify(series)


# ============================================================================
# API SYSTÈME
# ============================================================================

@app.route('/api/config', methods=['GET'])
def api_get_config():
    return jsonify(load_config())


@app.route('/api/update', methods=['POST'])
def api_update():
    import subprocess
    try:
        result = subprocess.run(['git', 'pull'], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            msg = 'Déjà à jour' if 'Already up to date' in result.stdout else 'Mise à jour OK - Redémarrez'
            return jsonify({'success': True, 'message': msg})
        return jsonify({'success': False, 'message': result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============================================================================
# INITIALISATION
# ============================================================================

if not CONFIG_FILE.exists():
    save_config(DEFAULT_CONFIG)

init_google_sheets()
init_reference_tables()

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  MALLO BOIS - WoodStock")
    print("=" * 50)
    _afficher_tableau_epaisseurs()
    
    PORT = 5001
    
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        import ssl
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.pem', 'key.pem')
        print(f"  🔒 https://localhost:{PORT}")
        print("=" * 50)
        app.run(host='0.0.0.0', port=PORT, debug=False, ssl_context=context)
    else:
        print(f"  http://localhost:{PORT}")
        print("=" * 50)
        app.run(host='0.0.0.0', port=PORT, debug=True)
