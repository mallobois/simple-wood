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
# DONNÉES DE RÉFÉRENCE - ESSENCES
# ============================================================================
# PSF = Point de Saturation des Fibres (%)
# retrait_t = Retrait tangentiel total PSF → 0% (%)
# Sources: CIRAD, Wood Handbook, FCBA, CTBA

ESSENCES_DATA = [
    # Feuillus - Bois nerveux (retrait élevé)
    {"code": "HET", "nom": "Hêtre", "nom_latin": "Fagus sylvatica", "densite_frais": 950, "densite_sec": 650, "psf": 32, "retrait_t": 11.8},
    {"code": "CHA", "nom": "Charme", "nom_latin": "Carpinus betulus", "densite_frais": 1000, "densite_sec": 750, "psf": 30, "retrait_t": 11.5},
    # Feuillus - Chênes
    {"code": "CHE", "nom": "Chêne indigène", "nom_latin": "Quercus", "densite_frais": 1070, "densite_sec": 720, "psf": 29, "retrait_t": 10.0},
    {"code": "CHS", "nom": "Chêne sessile", "nom_latin": "Quercus petraea", "densite_frais": 1070, "densite_sec": 720, "psf": 29, "retrait_t": 9.8},
    {"code": "CHP", "nom": "Chêne pédonculé", "nom_latin": "Quercus robur", "densite_frais": 1070, "densite_sec": 720, "psf": 29, "retrait_t": 10.2},
    # Feuillus - Frênes
    {"code": "FRE", "nom": "Frêne", "nom_latin": "Fraxinus", "densite_frais": 920, "densite_sec": 680, "psf": 28, "retrait_t": 8.0},
    {"code": "FRC", "nom": "Frêne commun", "nom_latin": "Fraxinus excelsior", "densite_frais": 920, "densite_sec": 680, "psf": 28, "retrait_t": 8.0},
    # Feuillus - Divers
    {"code": "CHT", "nom": "Châtaignier", "nom_latin": "Castanea sativa", "densite_frais": 950, "densite_sec": 590, "psf": 30, "retrait_t": 6.5},
    {"code": "MER", "nom": "Merisier", "nom_latin": "Prunus avium", "densite_frais": 900, "densite_sec": 620, "psf": 29, "retrait_t": 7.5},
    {"code": "NOY", "nom": "Noyer", "nom_latin": "Juglans regia", "densite_frais": 900, "densite_sec": 680, "psf": 27, "retrait_t": 7.5},
    {"code": "ROB", "nom": "Robinier", "nom_latin": "Robinia pseudoacacia", "densite_frais": 950, "densite_sec": 770, "psf": 26, "retrait_t": 5.0},
    # Feuillus - Érables
    {"code": "ERP", "nom": "Érable plane", "nom_latin": "Acer platanoides", "densite_frais": 900, "densite_sec": 650, "psf": 29, "retrait_t": 8.0},
    {"code": "ERC", "nom": "Érable champêtre", "nom_latin": "Acer campestre", "densite_frais": 900, "densite_sec": 650, "psf": 29, "retrait_t": 7.8},
    {"code": "ERS", "nom": "Érable sycomore", "nom_latin": "Acer pseudoplatanus", "densite_frais": 900, "densite_sec": 650, "psf": 29, "retrait_t": 8.5},
    # Feuillus - Bois blancs
    {"code": "BOU", "nom": "Bouleau", "nom_latin": "Betula", "densite_frais": 850, "densite_sec": 650, "psf": 28, "retrait_t": 7.5},
    {"code": "TRE", "nom": "Tremble", "nom_latin": "Populus tremula", "densite_frais": 800, "densite_sec": 500, "psf": 29, "retrait_t": 8.5},
    {"code": "PEU", "nom": "Peuplier", "nom_latin": "Populus", "densite_frais": 800, "densite_sec": 450, "psf": 29, "retrait_t": 8.5},
    {"code": "TIL", "nom": "Tilleul", "nom_latin": "Tilia", "densite_frais": 800, "densite_sec": 530, "psf": 31, "retrait_t": 9.5},
    {"code": "AUN", "nom": "Aulne glutineux", "nom_latin": "Alnus glutinosa", "densite_frais": 850, "densite_sec": 530, "psf": 29, "retrait_t": 7.3},
    # Feuillus - Fruitiers et Sorbus
    {"code": "ALT", "nom": "Alisier torminal", "nom_latin": "Sorbus torminalis", "densite_frais": 950, "densite_sec": 750, "psf": 30, "retrait_t": 10.0},
    {"code": "ALB", "nom": "Alisier blanc", "nom_latin": "Sorbus aria", "densite_frais": 950, "densite_sec": 750, "psf": 30, "retrait_t": 9.5},
    {"code": "COR", "nom": "Cormier", "nom_latin": "Sorbus domestica", "densite_frais": 950, "densite_sec": 750, "psf": 30, "retrait_t": 10.5},
    {"code": "ORM", "nom": "Orme", "nom_latin": "Ulmus", "densite_frais": 950, "densite_sec": 680, "psf": 28, "retrait_t": 8.0},
    # Résineux
    {"code": "EPC", "nom": "Épicéa commun", "nom_latin": "Picea abies", "densite_frais": 860, "densite_sec": 470, "psf": 30, "retrait_t": 8.0},
    {"code": "DOU", "nom": "Douglas", "nom_latin": "Pseudotsuga menziesii", "densite_frais": 850, "densite_sec": 530, "psf": 26, "retrait_t": 7.6},
    {"code": "MEE", "nom": "Mélèze d'Europe", "nom_latin": "Larix decidua", "densite_frais": 900, "densite_sec": 590, "psf": 28, "retrait_t": 7.8},
    {"code": "PIS", "nom": "Pin sylvestre", "nom_latin": "Pinus sylvestris", "densite_frais": 850, "densite_sec": 520, "psf": 28, "retrait_t": 7.5},
    {"code": "PIM", "nom": "Pin maritime", "nom_latin": "Pinus pinaster", "densite_frais": 900, "densite_sec": 530, "psf": 29, "retrait_t": 8.0},
    {"code": "PIN", "nom": "Pin noir", "nom_latin": "Pinus nigra", "densite_frais": 900, "densite_sec": 550, "psf": 28, "retrait_t": 7.5},
    {"code": "SAP", "nom": "Sapin pectiné", "nom_latin": "Abies alba", "densite_frais": 850, "densite_sec": 450, "psf": 30, "retrait_t": 7.5},
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
EPAISSEURS_CIBLES = [27, 32, 45, 50, 80]  # mm sec


def _calculer_epaisseurs():
    """Calcule les épaisseurs frais pour chaque essence et épaisseur sèche cible"""
    result = []
    for ess in ESSENCES_DATA:
        code = ess["code"]
        psf = ess["psf"]
        retrait_t = ess["retrait_t"]
        # Retrait effectif de PSF → 8%
        retrait_eff = (retrait_t / 100) * (psf - HUMIDITE_CIBLE) / psf
        for ep_sec in EPAISSEURS_CIBLES:
            ep_frais = round(ep_sec / (1 - retrait_eff))
            result.append({"essence": code, "ep_frais": ep_frais, "ep_sec": ep_sec})
    return result


EPAISSEURS_DATA = _calculer_epaisseurs()


def _afficher_tableau_epaisseurs():
    """Affiche le tableau des épaisseurs au démarrage"""
    print("\n" + "=" * 85)
    print("  📐 TABLEAU DES ÉPAISSEURS (frais → sec à 8%)")
    print("=" * 85)
    print(f"{'Essence':<8} {'PSF':>4} {'Ret.T':>6} │ " + " │ ".join(f"{e:>2}mm" for e in EPAISSEURS_CIBLES))
    print("-" * 85)
    for ess in ESSENCES_DATA:
        code = ess["code"]
        psf = ess["psf"]
        rt = ess["retrait_t"]
        eps = [e for e in EPAISSEURS_DATA if e["essence"] == code]
        vals = " │ ".join(f"{e['ep_frais']:>4}" for e in eps)
        print(f"{code:<8} {psf:>3}% {rt:>5.1f}% │ {vals}")
    print("=" * 85)
    print(f"  Légende: épaisseur frais (mm) pour obtenir {EPAISSEURS_CIBLES} mm sec à {HUMIDITE_CIBLE}%")
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
            'id': 'troncons',
            'nom': 'Tronçons',
            'description': 'Étiquetage des tronçons',
            'serie': '2501',
            'compteur': 0,
            'prefixe': 'TRO-',
            'printer': 'zebra1',
            'copies_defaut': 1,
            'type_produit': 'TRO',
            'champs': []
        },
        {
            'id': 'sciage',
            'nom': 'Sciage',
            'description': 'Découpe et mise en paquets',
            'serie': '2501',
            'compteur': 0,
            'prefixe': 'SCI-',
            'printer': 'zebra1',
            'copies_defaut': 1,
            'type_produit': 'PQT',
            'source_poste': 'troncons',
            'champs': []
        }
    ],
    'tables': [
        {
            'id': 'essences',
            'nom': 'Essences',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'},
                {'id': 'nom_latin', 'nom': 'Nom latin', 'type': 'text'},
                {'id': 'densite_frais', 'nom': 'Densité frais', 'type': 'number'},
                {'id': 'densite_sec', 'nom': 'Densité sec', 'type': 'number'},
                {'id': 'psf', 'nom': 'PSF %', 'type': 'number'},
                {'id': 'retrait_t', 'nom': 'Retrait T %', 'type': 'number'}
            ]
        },
        {
            'id': 'produits',
            'nom': 'Produits',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'}
            ]
        },
        {
            'id': 'qualites',
            'nom': 'Qualités',
            'colonnes': [
                {'id': 'essence', 'nom': 'Essence', 'type': 'ref', 'ref_table': 'essences', 'ref_col': 'Code'},
                {'id': 'produit', 'nom': 'Produit', 'type': 'ref', 'ref_table': 'produits', 'ref_col': 'Code'},
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'}
            ]
        },
        {
            'id': 'epaisseurs',
            'nom': 'Épaisseurs',
            'colonnes': [
                {'id': 'essence', 'nom': 'Essence', 'type': 'ref', 'ref_table': 'essences', 'ref_col': 'Code'},
                {'id': 'ep_frais', 'nom': 'Ép. frais (mm)', 'type': 'number'},
                {'id': 'ep_sec', 'nom': 'Ép. sec (mm)', 'type': 'number'}
            ]
        },
        {
            'id': 'forets',
            'nom': 'Forêts',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text'},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text'},
                {'id': 'departement', 'nom': 'Département', 'type': 'text'}
            ]
        },
        {
            'id': 'lots',
            'nom': 'Lots',
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
    """Initialise la connexion Google Sheets"""
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
    """Crée l'onglet Utilisateurs si nécessaire"""
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
    """Initialise les tables de référence si vides"""
    if spreadsheet is None:
        return
    
    config = load_config()
    tables_to_init = [
        ('essences', ESSENCES_DATA),
        ('produits', PRODUITS_DATA),
        ('epaisseurs', EPAISSEURS_DATA),
    ]
    
    for table_id, data in tables_to_init:
        table_cfg = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
        if table_cfg:
            existing = get_table_values(table_id)
            if len(existing) == 0:
                print(f"  → Initialisation {table_id}...")
                get_or_create_table_sheet(table_id, table_cfg)
                for item in data:
                    add_table_value(table_id, table_cfg, item)
                print(f"    {len(data)} entrées ajoutées")


def get_or_create_poste_sheet(poste_id: str, poste_config: dict):
    """Crée ou récupère l'onglet d'un poste"""
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
    """Enregistre une impression"""
    if spreadsheet is None:
        return
    try:
        sheet = get_or_create_poste_sheet(poste_id, poste_config)
        now = datetime.now()
        row = [
            now.strftime('%d/%m/%Y'),
            now.strftime('%H:%M:%S'),
            poste_config.get('serie', '2501'),
            data.get('numero', '')
        ]
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
    """Récupère l'historique d'un poste"""
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
    """Crée ou récupère l'onglet d'une table"""
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
    """Récupère les valeurs d'une table"""
    if spreadsheet is None:
        return []
    try:
        sheet = spreadsheet.worksheet(f"Table_{table_id}")
        return sheet.get_all_records()
    except:
        return []


def add_table_value(table_id: str, table_config: dict, data: dict) -> bool:
    """Ajoute une valeur à une table"""
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
    """Met à jour une valeur"""
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
    """Supprime une valeur"""
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
    """Récupère les utilisateurs depuis Google Sheets"""
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
    """Charge la configuration"""
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
    """Sauvegarde la configuration"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")


def get_poste(config: dict, poste_id: str) -> dict:
    """Récupère un poste par son ID"""
    for p in config.get('postes', []):
        if p['id'] == poste_id:
            return p
    return None


def get_printer(config: dict, printer_id: str) -> dict:
    """Récupère une imprimante par son ID"""
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
    """Envoie du code ZPL à l'imprimante"""
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
    """Formate un numéro sur 6 chiffres"""
    s = f"{n:06d}"
    return f"{s[0:2]} {s[2:4]} {s[4:6]}" if spaced else s


def generate_zpl(poste: dict, data: dict, source: str = '') -> str:
    """Génère le code ZPL pour une étiquette"""
    serie = poste.get('serie', '2501')
    compteur = poste.get('compteur', 0)
    prefixe = poste.get('prefixe', '')
    numero = format_numero(compteur)
    qr_data = f"{prefixe}{serie}-{format_numero(compteur, spaced=False)}"
    
    lines = []
    y = 180
    
    # Essence / Qualité / Épaisseur
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
    
    # Source
    if source:
        lines.append(f"^FO400,{y}^A0N,22,22^FDSource: {source}^FS")
        y += 30
    
    # Champs personnalisés
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
    
    if is_admin or not user_postes:
        postes = config.get('postes', [])
    else:
        postes = [p for p in config.get('postes', []) if p['id'] in user_postes]
    
    return render_template('index.html', 
                           user=session.get('user_nom', ''),
                           droits=session.get('user_droits', 'operateur'),
                           postes=postes)


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
    if not is_admin and user_postes and poste_id not in user_postes:
        return redirect(url_for('index'))
    
    return render_template('poste_tache.html', poste=poste, printers=config.get('printers', []))


@app.route('/poste/<poste_id>/parametres')
@admin_required
def page_poste_params(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    return render_template('poste_parametres.html', 
                           poste=poste, 
                           printers=config.get('printers', []),
                           all_postes=config.get('postes', []))


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
    return jsonify([{
        'id': uid, 
        'nom': d['nom'], 
        'initiales': d['initiales'],
        'droits': d.get('droits', 'operateur'),
        'postes': d.get('postes', [])
    } for uid, d in users.items()])


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
    uid = data.get('id', '').strip().lower()
    password = data.get('password', '')
    
    if password and (len(password) < 6 or len(password) > 8 or not password.isdigit()):
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        
        for i, row in enumerate(records):
            if row.get('Identifiant') == uid:
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
            if row.get('Identifiant') == uid:
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
    
    config['printers'].append({
        'id': pid,
        'nom': data.get('nom', '').strip(),
        'ip': data.get('ip', '').strip(),
        'port': int(data.get('port', 9100))
    })
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
    
    test_zpl = f"""^XA
^CI28
^PW812
^LL203
^FO50,30^A0N,40,40^FDTEST {printer.get('nom', 'Imprimante')}^FS
^FO50,80^A0N,25,25^FDMALLO BOIS - WoodStock^FS
^FO50,120^A0N,20,20^FD{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}^FS
^FO50,160^A0N,18,18^FDIP: {printer.get('ip')}:{printer.get('port')}^FS
^XZ"""
    
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
    
    config['postes'].append({
        'id': pid,
        'nom': data.get('nom', pid),
        'description': data.get('description', ''),
        'serie': data.get('serie', '2501'),
        'compteur': 0,
        'prefixe': data.get('prefixe', ''),
        'printer': data.get('printer', config['printers'][0]['id'] if config['printers'] else 'zebra1'),
        'copies_defaut': int(data.get('copies_defaut', 1)),
        'champs': data.get('champs', [])
    })
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
    
    table_cfg = {
        'id': tid, 
        'nom': nom, 
        'colonnes': data.get('colonnes', [{'id': 'valeur', 'nom': 'Valeur', 'type': 'text'}])
    }
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
    """Qualités filtrées par essence et produit"""
    all_qualites = get_table_values('qualites')
    filtered = [q for q in all_qualites 
                if q.get('Essence', '').upper() == essence_code.upper()
                and q.get('Produit', '').upper() == produit_code.upper()]
    return jsonify(filtered)


@app.route('/api/epaisseurs/<essence_code>', methods=['GET'])
def api_get_epaisseurs_filtrees(essence_code):
    """Épaisseurs filtrées par essence"""
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
            return jsonify({
                'success': False,
                'message': result.get('message', 'Erreur impression'),
                'compteur': poste['compteur']
            })
    
    # Log
    log_data = {**data, 'numero': format_numero(poste['compteur'], spaced=False), 'source': source}
    log_to_poste_sheet(poste_id, poste, log_data, copies if imprimer else 0, session.get('user_nom', 'Inconnu'))
    
    # Incrémenter compteur
    for p in config['postes']:
        if p['id'] == poste_id:
            p['compteur'] = (p['compteur'] + 1) % 1000000
            break
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': f'N° {numero_imprime}' + (f' ({printed} copies)' if printed > 1 else ''),
        'compteur': poste['compteur'] + 1,
        'numero_imprime': numero_imprime
    })


@app.route('/api/poste/<poste_id>/history', methods=['GET'])
def api_poste_history(poste_id):
    return jsonify(get_poste_history(poste_id))


@app.route('/api/poste/<poste_id>/series', methods=['GET'])
def api_poste_series(poste_id):
    """Séries et numéros disponibles pour un poste source"""
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
    print("  http://localhost:5000")
    print("=" * 50)
    _afficher_tableau_epaisseurs()
    app.run(host='0.0.0.0', port=5000, debug=True)
