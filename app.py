#!/usr/bin/env python3
"""
Serveur d'impression Zebra ZPL pour Raspberry Pi
MALLO BOIS - Système d'étiquetage industriel v3
Architecture: Postes de travail dynamiques
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

app = Flask(__name__)
app.secret_key = 'mallo-bois-simple-wood-2024'

CONFIG_FILE = Path(__file__).parent / 'config.json'
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'

SPREADSHEET_ID = '1dSPJFr8Nq5RwanZBKszpFwXXvacHROG_9MAD8FRgiOk'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

gs_client = None
spreadsheet = None


# ============== DECORATEURS ==============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('user_droits') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ============== GOOGLE SHEETS ==============

def init_google_sheets():
    global gs_client, spreadsheet
    try:
        if CREDENTIALS_FILE.exists():
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            gs_client = gspread.authorize(creds)
            spreadsheet = gs_client.open_by_key(SPREADSHEET_ID)
            print("✓ Google Sheets connecté")
            init_sheet_headers()
        else:
            print("⚠ credentials.json non trouvé")
    except Exception as e:
        print(f"⚠ Erreur Google Sheets: {e}")


def init_sheet_headers():
    """Initialise l'onglet Utilisateurs"""
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        all_values = sheet.get_all_values()
        if len(all_values) <= 1:
            print("→ Ajout utilisateurs par défaut...")
            sheet.append_row(['admin', '123456', 'Administrateur', 'AD', 'admin', ''])
            sheet.append_row(['operateur', '111111', 'Opérateur', 'OP', 'operateur', ''])
    except gspread.WorksheetNotFound:
        print("→ Création onglet Utilisateurs...")
        sheet = spreadsheet.add_worksheet(title='Utilisateurs', rows=100, cols=10)
        sheet.append_row(['Identifiant', 'Mot de passe', 'Nom', 'Initiales', 'Droits', 'Postes'])
        sheet.append_row(['admin', '123456', 'Administrateur', 'AD', 'admin', ''])
        sheet.append_row(['operateur', '111111', 'Opérateur', 'OP', 'operateur', ''])


def get_or_create_poste_sheet(poste_id: str, poste_config: dict):
    """Crée ou récupère l'onglet Google Sheets pour un poste"""
    sheet_name = f"Poste_{poste_id}"
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        # En-têtes: Date, Heure, Numéro, champs dynamiques..., Copies, Opérateur
        headers = ['Date', 'Heure', 'Série', 'Numéro']
        for field in poste_config.get('champs', []):
            headers.append(field['nom'])
        headers.extend(['Copies', 'Opérateur'])
        sheet.append_row(headers)
        return sheet


def log_to_poste_sheet(poste_id: str, poste_config: dict, data: dict, copies: int, operateur: str):
    """Enregistre une impression dans le Google Sheet du poste"""
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
        sheet_name = f"Poste_{poste_id}"
        sheet = spreadsheet.worksheet(sheet_name)
        records = sheet.get_all_records()
        return list(reversed(records[-limit:]))
    except:
        return []


# ============== TABLES DE REFERENCE ==============

def get_or_create_table_sheet(table_id: str, table_config: dict):
    """Crée ou récupère l'onglet Google Sheets pour une table"""
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
        print(f"✓ Table {table_config.get('nom', table_id)} créée")
        return sheet


def get_table_values(table_id: str, table_config: dict = None) -> list:
    """Récupère les valeurs d'une table"""
    if spreadsheet is None:
        return []
    try:
        sheet_name = f"Table_{table_id}"
        sheet = spreadsheet.worksheet(sheet_name)
        records = sheet.get_all_records()
        return records
    except:
        return []


def add_table_value(table_id: str, table_config: dict, data: dict) -> bool:
    """Ajoute une valeur à une table"""
    if spreadsheet is None:
        return False
    try:
        sheet_name = f"Table_{table_id}"
        sheet = spreadsheet.worksheet(sheet_name)
        records = sheet.get_all_records()
        new_id = len(records) + 1
        
        colonnes = table_config.get('colonnes', [])
        row = [new_id]
        for col in colonnes:
            row.append(data.get(col['id'], ''))
        
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Erreur ajout table: {e}")
        return False


def update_table_value(table_id: str, table_config: dict, row_id: int, data: dict) -> bool:
    """Met à jour une valeur dans une table"""
    if spreadsheet is None:
        return False
    try:
        sheet_name = f"Table_{table_id}"
        sheet = spreadsheet.worksheet(sheet_name)
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
        print(f"Erreur update table: {e}")
        return False


def delete_table_value(table_id: str, row_id: int) -> bool:
    """Supprime une valeur d'une table"""
    if spreadsheet is None:
        return False
    try:
        sheet_name = f"Table_{table_id}"
        sheet = spreadsheet.worksheet(sheet_name)
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if row.get('ID') == row_id:
                sheet.delete_rows(i + 2)
                return True
        return False
    except Exception as e:
        print(f"Erreur delete table: {e}")
        return False


# ============== UTILISATEURS ==============

def get_users_from_sheets() -> dict:
    default_users = {
        'admin': {'password': '123456', 'nom': 'Administrateur', 'initiales': 'AD', 'droits': 'admin', 'postes': []},
    }
    
    if spreadsheet is None:
        return default_users
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        if not records:
            return default_users
        
        users = {}
        for row in records:
            identifiant = row.get('Identifiant', '')
            if identifiant:
                nom = row.get('Nom', identifiant)
                postes_str = str(row.get('Postes', ''))
                postes = [p.strip() for p in postes_str.split(',') if p.strip()]
                users[identifiant] = {
                    'password': str(row.get('Mot de passe', '')),
                    'nom': nom,
                    'initiales': row.get('Initiales', nom[:2].upper()),
                    'droits': row.get('Droits', 'operateur'),
                    'postes': postes
                }
        return users if users else default_users
    except Exception as e:
        print(f"Erreur utilisateurs: {e}")
        return default_users


# ============== CONFIGURATION ==============

DEFAULT_CONFIG = {
    'printers': [
        {'id': 'zebra1', 'nom': 'Zebra 1', 'ip': '192.168.1.67', 'port': 9100}
    ],
    'postes': [
        {
            'id': 'troncons',
            'nom': 'Tronçons',
            'description': 'Étiquetage des tronçons de bois',
            'serie': '2501',
            'compteur': 0,
            'prefixe': 'TRO-',
            'printer': 'zebra1',
            'copies_defaut': 1,
            'champs': []
        }
    ],
    'tables': [
        {
            'id': 'essences',
            'nom': 'Essences',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text', 'width': 60},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text', 'width': 120},
                {'id': 'nom_latin', 'nom': 'Nom latin', 'type': 'text', 'width': 150},
                {'id': 'densite_frais', 'nom': 'Densité frais (kg/m³)', 'type': 'number', 'width': 100},
                {'id': 'densite_sec', 'nom': 'Densité sec (kg/m³)', 'type': 'number', 'width': 100}
            ]
        },
        {
            'id': 'forets',
            'nom': 'Forêts',
            'colonnes': [
                {'id': 'code', 'nom': 'Code', 'type': 'text', 'width': 60},
                {'id': 'nom', 'nom': 'Nom', 'type': 'text', 'width': 150},
                {'id': 'departement', 'nom': 'Département', 'type': 'text', 'width': 100}
            ]
        },
        {
            'id': 'lots',
            'nom': 'Lots',
            'colonnes': [
                {'id': 'numero', 'nom': 'Numéro', 'type': 'text', 'width': 80},
                {'id': 'foret', 'nom': 'Forêt', 'type': 'text', 'width': 120},
                {'id': 'date_achat', 'nom': 'Date achat', 'type': 'text', 'width': 100},
                {'id': 'volume', 'nom': 'Volume m³', 'type': 'number', 'width': 80}
            ]
        }
    ],
    'utilisateur': {'nom': 'Opérateur', 'site': 'MALLO BOIS'}
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'printers' not in config:
                    config['printers'] = DEFAULT_CONFIG['printers']
                if 'postes' not in config:
                    config['postes'] = DEFAULT_CONFIG['postes']
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


# ============== IMPRESSION ==============

def send_zpl_to_printer(zpl_code: str, printer: dict) -> dict:
    ip = printer.get('ip', '192.168.1.67')
    port = printer.get('port', 9100)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((ip, port))
            sock.sendall(zpl_code.encode('utf-8'))
        return {'success': True, 'message': f'Envoyé à {ip}:{port}'}
    except socket.timeout:
        return {'success': False, 'message': 'Timeout'}
    except ConnectionRefusedError:
        return {'success': False, 'message': 'Connexion refusée'}
    except OSError as e:
        return {'success': False, 'message': str(e)}


def format_numero(n: int) -> str:
    s = f"{n:06d}"
    return f"{s[0:2]} {s[2:4]} {s[4:6]}"


def format_numero_compact(n: int) -> str:
    return f"{n:06d}"


def generate_zpl(poste: dict, data: dict) -> str:
    """Génère le code ZPL pour un poste"""
    serie = poste.get('serie', '2501')
    compteur = poste.get('compteur', 0)
    prefixe = poste.get('prefixe', '')
    numero = format_numero(compteur)
    qr_data = f"{prefixe}{serie}-{format_numero_compact(compteur)}"
    
    # Construction des lignes de champs
    champs_zpl = ""
    y_pos = 180
    for field in poste.get('champs', []):
        value = data.get(field['id'], '')
        if value:
            champs_zpl += f"^FO400,{y_pos}^A0N,24,24^FD{field['nom']}: {value}^FS\n"
            y_pos += 30
    
    zpl = f"""^XA
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
    return zpl


# ============== ROUTES PRINCIPALES ==============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')
        users = get_users_from_sheets()
        
        if username in users and users[username]['password'] == password:
            session['user'] = username
            session['user_nom'] = users[username]['nom']
            session['user_droits'] = users[username].get('droits', 'operateur')
            session['user_postes'] = users[username].get('postes', [])
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Identifiants incorrects'})
    
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
    
    # Admin voit tous les postes, sinon seulement ceux affectés
    if is_admin or not user_postes:
        postes = config.get('postes', [])
    else:
        postes = [p for p in config.get('postes', []) if p['id'] in user_postes]
    
    return render_template('index.html', 
                           user=session.get('user_nom', ''),
                           droits=session.get('user_droits', 'operateur'),
                           postes=postes)


# ============== ROUTES POSTES ==============

@app.route('/poste/<poste_id>')
@login_required
def page_poste(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    
    # Vérifier accès
    user_postes = session.get('user_postes', [])
    is_admin = session.get('user_droits') == 'admin'
    if not is_admin and user_postes and poste_id not in user_postes:
        return redirect(url_for('index'))
    
    printers = config.get('printers', [])
    return render_template('poste_tache.html', poste=poste, printers=printers)


@app.route('/poste/<poste_id>/parametres')
@admin_required
def page_poste_params(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    printers = config.get('printers', [])
    return render_template('poste_parametres.html', poste=poste, printers=printers)


@app.route('/poste/<poste_id>/liste')
@admin_required
def page_poste_liste(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    if not poste:
        return redirect(url_for('index'))
    history = get_poste_history(poste_id)
    return render_template('poste_liste.html', poste=poste, history=history)


@app.route('/parametres')
@admin_required
def page_parametres():
    config = load_config()
    return render_template('parametres.html', config=config)


# ============== API UTILISATEURS ==============

@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = get_users_from_sheets()
    return jsonify([{
        'id': uid,
        'nom': data.get('nom', uid),
        'initiales': data.get('initiales', uid[:2].upper())
    } for uid, data in users.items()])


@app.route('/api/users/full', methods=['GET'])
def api_get_users_full():
    users = get_users_from_sheets()
    return jsonify([{
        'id': uid,
        'nom': data.get('nom', uid),
        'initiales': data.get('initiales', uid[:2].upper()),
        'droits': data.get('droits', 'operateur'),
        'postes': data.get('postes', [])
    } for uid, data in users.items()])


@app.route('/api/users', methods=['POST'])
def api_create_user():
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    
    data = request.json
    uid = data.get('id', '').strip().lower()
    nom = data.get('nom', '').strip()
    initiales = data.get('initiales', '').strip().upper()
    droits = data.get('droits', 'operateur')
    password = data.get('password', '')
    postes = data.get('postes', [])
    
    if not uid or not nom or not initiales or not password:
        return jsonify({'success': False, 'message': 'Champs manquants'})
    
    if len(password) < 6 or len(password) > 8 or not password.isdigit():
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    
    users = get_users_from_sheets()
    if uid in users:
        return jsonify({'success': False, 'message': 'Identifiant déjà utilisé'})
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        postes_str = ','.join(postes) if postes else ''
        sheet.append_row([uid, password, nom, initiales, droits, postes_str])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/users', methods=['PUT'])
def api_update_user():
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    
    data = request.json
    uid = data.get('id', '').strip().lower()
    nom = data.get('nom', '').strip()
    initiales = data.get('initiales', '').strip().upper()
    droits = data.get('droits', 'operateur')
    password = data.get('password', '')
    postes = data.get('postes', [])
    
    if not uid or not nom or not initiales:
        return jsonify({'success': False, 'message': 'Champs manquants'})
    
    if password and (len(password) < 6 or len(password) > 8 or not password.isdigit()):
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        
        for i, row in enumerate(records):
            if row.get('Identifiant') == uid:
                row_num = i + 2
                sheet.update_cell(row_num, 3, nom)
                sheet.update_cell(row_num, 4, initiales)
                sheet.update_cell(row_num, 5, droits)
                sheet.update_cell(row_num, 6, ','.join(postes))
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
        
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============== API IMPRIMANTES ==============

@app.route('/api/printers', methods=['GET'])
def api_get_printers():
    config = load_config()
    return jsonify(config.get('printers', []))


@app.route('/api/printers', methods=['POST'])
def api_create_printer():
    config = load_config()
    
    if len(config.get('printers', [])) >= 6:
        return jsonify({'success': False, 'message': 'Maximum 6 imprimantes'})
    
    data = request.json
    pid = data.get('id', '').strip().lower()
    
    for p in config.get('printers', []):
        if p['id'] == pid:
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
    pid = data.get('id')
    
    for p in config.get('printers', []):
        if p['id'] == pid:
            p['nom'] = data.get('nom', p['nom'])
            p['ip'] = data.get('ip', p['ip'])
            p['port'] = int(data.get('port', p['port']))
            save_config(config)
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Imprimante non trouvée'})


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
^FO50,80^A0N,25,25^FDMALLO BOIS^FS
^FO50,120^A0N,20,20^FD{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}^FS
^XZ"""
    
    return jsonify(send_zpl_to_printer(test_zpl, printer))


# ============== API POSTES ==============

@app.route('/api/postes', methods=['GET'])
def api_get_postes():
    config = load_config()
    return jsonify(config.get('postes', []))


@app.route('/api/postes', methods=['POST'])
def api_create_poste():
    config = load_config()
    data = request.json
    
    pid = data.get('id', '').strip().lower().replace(' ', '_')
    if not pid:
        return jsonify({'success': False, 'message': 'ID requis'})
    
    for p in config.get('postes', []):
        if p['id'] == pid:
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
            p['nom'] = data.get('nom', p['nom'])
            p['description'] = data.get('description', p.get('description', ''))
            p['serie'] = data.get('serie', p['serie'])
            p['prefixe'] = data.get('prefixe', p.get('prefixe', ''))
            p['printer'] = data.get('printer', p['printer'])
            p['copies_defaut'] = int(data.get('copies_defaut', p.get('copies_defaut', 1)))
            if 'compteur' in data:
                p['compteur'] = int(data['compteur']) % 1000000
            if 'champs' in data:
                p['champs'] = data['champs']
            save_config(config)
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Poste non trouvé'})


@app.route('/api/postes/<poste_id>', methods=['DELETE'])
def api_delete_poste(poste_id):
    config = load_config()
    
    if len(config.get('postes', [])) <= 1:
        return jsonify({'success': False, 'message': 'Au moins un poste requis'})
    
    config['postes'] = [p for p in config['postes'] if p['id'] != poste_id]
    save_config(config)
    return jsonify({'success': True})


# ============== API TABLES ==============

@app.route('/api/tables', methods=['GET'])
def api_get_tables():
    config = load_config()
    return jsonify(config.get('tables', []))


@app.route('/api/tables', methods=['POST'])
def api_create_table():
    config = load_config()
    data = request.json
    
    tid = data.get('id', '').strip().lower().replace(' ', '_')
    nom = data.get('nom', '').strip()
    colonnes = data.get('colonnes', [{'id': 'valeur', 'nom': 'Valeur', 'type': 'text'}])
    
    if not tid or not nom:
        return jsonify({'success': False, 'message': 'ID et nom requis'})
    
    for t in config.get('tables', []):
        if t['id'] == tid:
            return jsonify({'success': False, 'message': 'ID déjà utilisé'})
    
    if 'tables' not in config:
        config['tables'] = []
    
    table_config = {'id': tid, 'nom': nom, 'colonnes': colonnes}
    config['tables'].append(table_config)
    save_config(config)
    
    get_or_create_table_sheet(tid, table_config)
    
    return jsonify({'success': True})


@app.route('/api/tables/<table_id>', methods=['PUT'])
def api_update_table(table_id):
    config = load_config()
    data = request.json
    
    for t in config.get('tables', []):
        if t['id'] == table_id:
            t['nom'] = data.get('nom', t['nom'])
            if 'colonnes' in data:
                t['colonnes'] = data['colonnes']
            save_config(config)
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Table non trouvée'})


@app.route('/api/tables/<table_id>', methods=['DELETE'])
def api_delete_table(table_id):
    config = load_config()
    config['tables'] = [t for t in config.get('tables', []) if t['id'] != table_id]
    save_config(config)
    return jsonify({'success': True})


@app.route('/api/tables/<table_id>/values', methods=['GET'])
def api_get_table_values(table_id):
    config = load_config()
    table_config = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
    if table_config:
        get_or_create_table_sheet(table_id, table_config)
    values = get_table_values(table_id, table_config)
    return jsonify(values)


@app.route('/api/tables/<table_id>/values', methods=['POST'])
def api_add_table_value(table_id):
    config = load_config()
    table_config = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
    
    if not table_config:
        return jsonify({'success': False, 'message': 'Table non trouvée'})
    
    get_or_create_table_sheet(table_id, table_config)
    
    data = request.json
    success = add_table_value(table_id, table_config, data)
    return jsonify({'success': success})


@app.route('/api/tables/<table_id>/values/<int:row_id>', methods=['PUT'])
def api_update_table_value(table_id, row_id):
    config = load_config()
    table_config = next((t for t in config.get('tables', []) if t['id'] == table_id), None)
    
    if not table_config:
        return jsonify({'success': False, 'message': 'Table non trouvée'})
    
    data = request.json
    success = update_table_value(table_id, table_config, row_id, data)
    return jsonify({'success': success})


@app.route('/api/tables/<table_id>/values/<int:row_id>', methods=['DELETE'])
def api_delete_table_value(table_id, row_id):
    success = delete_table_value(table_id, row_id)
    return jsonify({'success': success})


# ============== API IMPRESSION ==============

@app.route('/api/print/<poste_id>', methods=['POST'])
def api_print(poste_id):
    config = load_config()
    poste = get_poste(config, poste_id)
    
    if not poste:
        return jsonify({'success': False, 'message': 'Poste non trouvé'})
    
    data = request.json or {}
    imprimer = data.get('imprimer', True)
    copies = int(data.get('copies', poste.get('copies_defaut', 1)))
    copies = min(max(copies, 0), 50)
    
    numero_imprime = format_numero(poste['compteur'])
    zpl = generate_zpl(poste, data)
    printer = get_printer(config, poste.get('printer', 'zebra1'))
    
    printed = 0
    if imprimer and copies > 0:
        for _ in range(copies):
            result = send_zpl_to_printer(zpl, printer)
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
    
    # Log et incrément
    log_data = data.copy()
    log_data['numero'] = format_numero_compact(poste['compteur'])
    log_to_poste_sheet(poste_id, poste, log_data, copies if imprimer else 0, session.get('user_nom', 'Inconnu'))
    
    # Incrémenter compteur
    for p in config['postes']:
        if p['id'] == poste_id:
            p['compteur'] = (p['compteur'] + 1) % 1000000
            break
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': f'Imprimé - N° {numero_imprime}' if imprimer else f'Validé - N° {numero_imprime}',
        'compteur': poste['compteur'] + 1,
        'numero_imprime': numero_imprime
    })


@app.route('/api/poste/<poste_id>/history', methods=['GET'])
def api_poste_history(poste_id):
    history = get_poste_history(poste_id)
    return jsonify(history)


# ============== API SYSTEME ==============

@app.route('/api/config', methods=['GET'])
def api_get_config():
    return jsonify(load_config())


@app.route('/api/update', methods=['POST'])
def api_update():
    import subprocess
    try:
        result = subprocess.run(['git', 'pull'], cwd=Path(__file__).parent,
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            msg = 'Déjà à jour' if 'Already up to date' in result.stdout else 'Mise à jour OK. Redémarrez.'
            return jsonify({'success': True, 'message': msg})
        return jsonify({'success': False, 'message': result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============== INIT ==============

if not CONFIG_FILE.exists():
    save_config(DEFAULT_CONFIG)
init_google_sheets()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
