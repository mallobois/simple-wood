#!/usr/bin/env python3
"""
Serveur d'impression Zebra ZPL pour Raspberry Pi
MALLO BOIS - Système d'étiquetage industriel v2
"""

import os
import json
import socket
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Google Sheets
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
            print("⚠ credentials.json non trouvé - Google Sheets désactivé")
    except Exception as e:
        print(f"⚠ Erreur Google Sheets: {e}")


def init_sheet_headers():
    headers = {
        'Tronçons': ['Date', 'Heure', 'Série', 'Numéro', 'Code complet', 'Copies', 'Opérateur'],
        'Paquets': ['Date', 'Heure', 'Série', 'Numéro', 'Essence', 'Qualité', 'Épaisseur', 'Largeur', 'Longueur', 'Volume', 'Copies', 'Opérateur'],
        'Colis': ['Date', 'Heure', 'Série', 'Numéro', 'Client', 'Référence', 'Destination', 'Poids', 'Volume', 'Nb paquets', 'Copies', 'Opérateur'],
        'Utilisateurs': ['Identifiant', 'Mot de passe', 'Nom', 'Initiales', 'Droits']
    }
    
    for sheet_name, header_row in headers.items():
        try:
            sheet = spreadsheet.worksheet(sheet_name)
            first_row = sheet.row_values(1)
            if not first_row:
                sheet.append_row(header_row)
            
            # Pour Utilisateurs: vérifier s'il y a des données (au-delà des en-têtes)
            if sheet_name == 'Utilisateurs':
                all_values = sheet.get_all_values()
                if len(all_values) <= 1:  # Seulement les en-têtes ou vide
                    print("→ Ajout des utilisateurs par défaut...")
                    sheet.append_row(['admin', 'admin', 'Administrateur', 'admin'])
                    sheet.append_row(['operateur', '1234', 'Opérateur', 'operateur'])
                    print("✓ Utilisateurs ajoutés: admin, operateur")
                else:
                    print(f"✓ {len(all_values)-1} utilisateur(s) trouvé(s)")
                    
        except gspread.WorksheetNotFound:
            print(f"→ Création onglet {sheet_name}...")
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            sheet.append_row(header_row)
            if sheet_name == 'Utilisateurs':
                sheet.append_row(['admin', 'admin', 'Administrateur', 'admin'])
                sheet.append_row(['operateur', '1234', 'Opérateur', 'operateur'])
                print("✓ Utilisateurs ajoutés: admin, operateur")


def log_to_sheets(sheet_name: str, data: list):
    if spreadsheet is None:
        return
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        sheet.append_row(data)
    except Exception as e:
        print(f"Erreur log Google Sheets: {e}")


def get_users_from_sheets() -> dict:
    default_users = {
        'admin': {'password': 'admin', 'nom': 'Administrateur', 'initiales': 'AD', 'droits': 'admin'},
        'operateur': {'password': '1234', 'nom': 'Opérateur', 'initiales': 'OP', 'droits': 'operateur'},
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
                users[identifiant] = {
                    'password': str(row.get('Mot de passe', '')),
                    'nom': nom,
                    'initiales': row.get('Initiales', nom[:2].upper()),
                    'droits': row.get('Droits', 'operateur')
                }
        return users if users else default_users
    except Exception as e:
        print(f"Erreur lecture utilisateurs: {e}")
        return default_users


DEFAULT_CONFIG = {
    'printer': {'ip': '192.168.1.67', 'port': 9100},
    'troncons': {'serie': '2601', 'compteur': 0, 'prefixe': 'TRO-', 'copies_defaut': 1},
    'paquet': {'serie': '2601', 'compteur': 0, 'copies_defaut': 1},
    'colis': {'serie': '2601', 'compteur': 0, 'copies_defaut': 1},
    'utilisateur': {'nom': 'Opérateur', 'site': 'MALLO BOIS'}
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
        except Exception as e:
            print(f"Erreur lecture config: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde config: {e}")


def send_zpl(zpl_code: str, config: dict) -> dict:
    ip = config['printer']['ip']
    port = config['printer']['port']
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((ip, port))
            sock.sendall(zpl_code.encode('utf-8'))
        return {'success': True, 'message': f'Envoyé à {ip}:{port}'}
    except socket.timeout:
        return {'success': False, 'message': 'Timeout - Imprimante non accessible'}
    except ConnectionRefusedError:
        return {'success': False, 'message': 'Connexion refusée - Vérifiez IP et port'}
    except OSError as e:
        return {'success': False, 'message': f'Erreur réseau: {str(e)}'}


def format_numero(n: int) -> str:
    s = f"{n:06d}"
    return f"{s[0:2]} {s[2:4]} {s[4:6]}"


def format_numero_compact(n: int) -> str:
    return f"{n:06d}"


def generate_zpl_troncons(config: dict) -> str:
    prefixe = config['troncons'].get('prefixe', 'TRO-')
    serie = config['troncons']['serie']
    compteur = config['troncons']['compteur']
    qr_data = f"{prefixe}{serie}-{format_numero_compact(compteur)}"
    numero_affiche = format_numero(compteur)
    
    zpl = f"""^XA
^CI28
^PW812
^LL406
^LH0,0
~SD25
^FO392,20
^A0N,40,40
^FB396,1,0,R
^FD{serie}^FS
^FO30,28
^BQN,2,16
^FDQA,{qr_data}^FS
^FO392,165
^A0N,128,128
^FB396,1,0,R
^FD{numero_affiche}^FS
^FO392,360
^A0N,32,32
^FB396,1,0,R
^FDMALLO BOIS^FS
^XZ"""
    return zpl


def generate_zpl_paquet(data: dict, config: dict) -> str:
    serie = config['paquet']['serie']
    compteur = config['paquet']['compteur']
    essence = data.get('essence', 'HETRE')
    epaisseur = data.get('epaisseur', '')
    largeur = data.get('largeur', '')
    longueur = data.get('longueur', '')
    qualite = data.get('qualite', 'A')
    volume = data.get('volume', '')
    numero = format_numero(compteur)
    qr_data = f"PAQ-{serie}-{format_numero_compact(compteur)}"
    
    zpl = f"""^XA
^CI28
^PW812
^LL406
^LH0,0
~SD25
^FO30,30
^BQN,2,6
^FDQA,{qr_data}^FS
^FO280,30^A0N,40,40^FD{essence}^FS
^FO280,80^A0N,28,28^FDQualité: {qualite}^FS
^FO280,130^A0N,24,24^FD{epaisseur} x {largeur} x {longueur} mm^FS
^FO280,165^A0N,24,24^FDVolume: {volume} m³^FS
^FO280,220^GB500,2,2^FS
^FO280,250^A0N,50,50^FD{numero}^FS
^FO30,360^A0N,18,18^FDMALLO BOIS^FS
^FO650,360^A0N,18,18^FD{datetime.now().strftime('%d/%m/%Y')}^FS
^XZ"""
    return zpl


def generate_zpl_colis(data: dict, config: dict) -> str:
    serie = config['colis']['serie']
    compteur = config['colis']['compteur']
    client = data.get('client', '')
    reference = data.get('reference', '')
    destination = data.get('destination', '')
    poids = data.get('poids', '')
    volume = data.get('volume', '')
    nb_paquets = data.get('nb_paquets', '')
    numero = format_numero(compteur)
    qr_data = f"COL-{serie}-{format_numero_compact(compteur)}"
    
    zpl = f"""^XA
^CI28
^PW812
^LL1218
^LH0,0
~SD25
^FO30,30^A0N,50,50^FDMALLO BOIS SAS^FS
^FO30,90^A0N,24,24^FDRéguisheim - France^FS
^FO30,140^GB750,3,3^FS
^FO30,170^A0N,45,45^FD{client}^FS
^FO30,230^A0N,28,28^FDRéf: {reference}^FS
^FO30,290^A0N,28,28^FDDestination:^FS
^FO30,330^A0N,35,35^FD{destination}^FS
^FO30,400^GB750,2,2^FS
^FO30,430^A0N,28,28^FDPoids: {poids} kg^FS
^FO300,430^A0N,28,28^FDVolume: {volume} m³^FS
^FO550,430^A0N,28,28^FDPaquets: {nb_paquets}^FS
^FO30,500^GB750,2,2^FS
^FO50,550
^BQN,2,10
^FDQA,{qr_data}^FS
^FO400,600^A0N,70,70^FD{numero}^FS
^FO400,700^A0N,28,28^FDColis N°^FS
^FO30,900^GB750,2,2^FS
^FO30,930^A0N,24,24^FDDate: {datetime.now().strftime('%d/%m/%Y %H:%M')}^FS
^XZ"""
    return zpl


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
            config = load_config()
            config['utilisateur']['nom'] = users[username]['nom']
            save_config(config)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Identifiants incorrects'})
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_nom', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html', user=session.get('user_nom', ''), droits=session.get('user_droits', 'operateur'))


@app.route('/troncons')
@login_required
def page_troncons():
    config = load_config()
    return render_template('troncons.html', config=config)


@app.route('/paquets')
@login_required
def page_paquets():
    config = load_config()
    return render_template('paquets.html', config=config)


@app.route('/colis')
@login_required
def page_colis():
    config = load_config()
    return render_template('colis.html', config=config)


@app.route('/parametres')
@admin_required
def page_parametres():
    config = load_config()
    return render_template('parametres.html', config=config)


@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Retourne la liste des utilisateurs (sans mots de passe)"""
    users = get_users_from_sheets()
    result = []
    for uid, data in users.items():
        result.append({
            'id': uid,
            'nom': data.get('nom', uid),
            'initiales': data.get('initiales', uid[:2].upper())
        })
    return jsonify(result)


@app.route('/api/users/full', methods=['GET'])
def api_get_users_full():
    """Retourne la liste complète des utilisateurs (sans mots de passe)"""
    users = get_users_from_sheets()
    result = []
    for uid, data in users.items():
        result.append({
            'id': uid,
            'nom': data.get('nom', uid),
            'initiales': data.get('initiales', uid[:2].upper()),
            'droits': data.get('droits', 'operateur')
        })
    return jsonify(result)


@app.route('/api/users', methods=['POST'])
def api_create_user():
    """Crée un nouvel utilisateur"""
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    
    data = request.json
    uid = data.get('id', '').strip().lower()
    nom = data.get('nom', '').strip()
    initiales = data.get('initiales', '').strip().upper()
    droits = data.get('droits', 'operateur')
    password = data.get('password', '')
    
    if not uid or not nom or not initiales or not password:
        return jsonify({'success': False, 'message': 'Champs manquants'})
    
    if len(password) < 6 or len(password) > 8 or not password.isdigit():
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    
    # Vérifier si l'utilisateur existe déjà
    users = get_users_from_sheets()
    if uid in users:
        return jsonify({'success': False, 'message': 'Identifiant déjà utilisé'})
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        sheet.append_row([uid, password, nom, initiales, droits])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/users', methods=['PUT'])
def api_update_user():
    """Met à jour un utilisateur"""
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    
    data = request.json
    uid = data.get('id', '').strip().lower()
    nom = data.get('nom', '').strip()
    initiales = data.get('initiales', '').strip().upper()
    droits = data.get('droits', 'operateur')
    password = data.get('password', '')
    
    if not uid or not nom or not initiales:
        return jsonify({'success': False, 'message': 'Champs manquants'})
    
    if password and (len(password) < 6 or len(password) > 8 or not password.isdigit()):
        return jsonify({'success': False, 'message': 'PIN: 6 à 8 chiffres'})
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        
        for i, row in enumerate(records):
            if row.get('Identifiant') == uid:
                row_num = i + 2  # +1 pour en-tête, +1 car index commence à 1
                sheet.update_cell(row_num, 3, nom)
                sheet.update_cell(row_num, 4, initiales)
                sheet.update_cell(row_num, 5, droits)
                if password:
                    sheet.update_cell(row_num, 2, password)
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/users/<uid>', methods=['DELETE'])
def api_delete_user(uid):
    """Supprime un utilisateur"""
    if spreadsheet is None:
        return jsonify({'success': False, 'message': 'Google Sheets non connecté'})
    
    try:
        sheet = spreadsheet.worksheet('Utilisateurs')
        records = sheet.get_all_records()
        
        for i, row in enumerate(records):
            if row.get('Identifiant') == uid:
                row_num = i + 2
                sheet.delete_rows(row_num)
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/config', methods=['GET'])
def api_get_config():
    config = load_config()
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def api_save_config():
    data = request.json
    config = load_config()
    
    if 'printer' in data:
        config['printer']['ip'] = data['printer'].get('ip', config['printer']['ip'])
        config['printer']['port'] = int(data['printer'].get('port', config['printer']['port']))
    
    if 'troncons' in data:
        config['troncons']['serie'] = data['troncons'].get('serie', config['troncons']['serie'])
        config['troncons']['prefixe'] = data['troncons'].get('prefixe', config['troncons']['prefixe'])
        if 'compteur' in data['troncons']:
            config['troncons']['compteur'] = int(data['troncons']['compteur']) % 1000000
        if 'copies_defaut' in data['troncons']:
            config['troncons']['copies_defaut'] = max(1, min(50, int(data['troncons']['copies_defaut'])))
    
    if 'paquet' in data:
        config['paquet']['serie'] = data['paquet'].get('serie', config['paquet']['serie'])
        if 'compteur' in data['paquet']:
            config['paquet']['compteur'] = int(data['paquet']['compteur']) % 1000000
        if 'copies_defaut' in data['paquet']:
            config['paquet']['copies_defaut'] = max(1, min(50, int(data['paquet']['copies_defaut'])))
    
    if 'colis' in data:
        config['colis']['serie'] = data['colis'].get('serie', config['colis']['serie'])
        if 'compteur' in data['colis']:
            config['colis']['compteur'] = int(data['colis']['compteur']) % 1000000
        if 'copies_defaut' in data['colis']:
            config['colis']['copies_defaut'] = max(1, min(50, int(data['colis']['copies_defaut'])))
    
    save_config(config)
    return jsonify({'success': True, 'config': config})


@app.route('/api/print/troncons', methods=['POST'])
def api_print_troncons():
    config = load_config()
    data = request.json or {}
    
    imprimer = data.get('imprimer', True)
    copies = int(data.get('copies', 1)) if imprimer else 0
    copies = min(max(copies, 0), 50)
    
    zpl = generate_zpl_troncons(config)
    numero_imprime = format_numero(config['troncons']['compteur'])
    
    printed = 0
    if imprimer and copies > 0:
        results = []
        for i in range(copies):
            result = send_zpl(zpl, config)
            results.append(result)
            if not result['success']:
                break
        printed = len([r for r in results if r['success']])
        
        if printed == 0:
            return jsonify({
                'success': False,
                'message': results[-1]['message'] if results else 'Erreur impression',
                'compteur': config['troncons']['compteur']
            })
    
    now = datetime.now()
    log_to_sheets('Tronçons', [
        now.strftime('%d/%m/%Y'),
        now.strftime('%H:%M:%S'),
        config['troncons']['serie'],
        format_numero_compact(config['troncons']['compteur']),
        f"{config['troncons']['prefixe']}{config['troncons']['serie']}-{format_numero_compact(config['troncons']['compteur'])}",
        copies if imprimer else 0,
        config['utilisateur']['nom']
    ])
    
    config['troncons']['compteur'] = (config['troncons']['compteur'] + 1) % 1000000
    save_config(config)
    
    return jsonify({
        'success': True,
        'message': f'Validé et imprimé - N° {numero_imprime}' if imprimer else f'Validé - N° {numero_imprime}',
        'zpl_preview': zpl,
        'compteur': config['troncons']['compteur'],
        'numero_imprime': numero_imprime
    })


@app.route('/api/print/paquet', methods=['POST'])
def api_print_paquet():
    config = load_config()
    data = request.json or {}
    
    copies = int(data.get('copies', config['paquet']['copies_defaut']))
    copies = min(max(copies, 1), 50)
    
    zpl = generate_zpl_paquet(data, config)
    numero_imprime = format_numero(config['paquet']['compteur'])
    
    results = []
    for i in range(copies):
        result = send_zpl(zpl, config)
        results.append(result)
        if not result['success']:
            break
    
    success = all(r['success'] for r in results)
    printed = len([r for r in results if r['success']])
    
    if printed > 0:
        now = datetime.now()
        log_to_sheets('Paquets', [
            now.strftime('%d/%m/%Y'),
            now.strftime('%H:%M:%S'),
            config['paquet']['serie'],
            format_numero_compact(config['paquet']['compteur']),
            data.get('essence', ''),
            data.get('qualite', ''),
            data.get('epaisseur', ''),
            data.get('largeur', ''),
            data.get('longueur', ''),
            data.get('volume', ''),
            copies,
            config['utilisateur']['nom']
        ])
        
        config['paquet']['compteur'] = (config['paquet']['compteur'] + 1) % 1000000
        save_config(config)
    
    return jsonify({
        'success': success,
        'message': f'{printed}/{copies} copie(s) imprimée(s) - N° {numero_imprime}',
        'compteur': config['paquet']['compteur'],
        'numero_imprime': numero_imprime
    })


@app.route('/api/print/colis', methods=['POST'])
def api_print_colis():
    config = load_config()
    data = request.json or {}
    
    copies = int(data.get('copies', config['colis']['copies_defaut']))
    copies = min(max(copies, 1), 50)
    
    zpl = generate_zpl_colis(data, config)
    numero_imprime = format_numero(config['colis']['compteur'])
    
    results = []
    for i in range(copies):
        result = send_zpl(zpl, config)
        results.append(result)
        if not result['success']:
            break
    
    success = all(r['success'] for r in results)
    printed = len([r for r in results if r['success']])
    
    if printed > 0:
        now = datetime.now()
        log_to_sheets('Colis', [
            now.strftime('%d/%m/%Y'),
            now.strftime('%H:%M:%S'),
            config['colis']['serie'],
            format_numero_compact(config['colis']['compteur']),
            data.get('client', ''),
            data.get('reference', ''),
            data.get('destination', ''),
            data.get('poids', ''),
            data.get('volume', ''),
            data.get('nb_paquets', ''),
            copies,
            config['utilisateur']['nom']
        ])
        
        config['colis']['compteur'] = (config['colis']['compteur'] + 1) % 1000000
        save_config(config)
    
    return jsonify({
        'success': success,
        'message': f'{printed}/{copies} copie(s) imprimée(s) - N° {numero_imprime}',
        'compteur': config['colis']['compteur'],
        'numero_imprime': numero_imprime
    })


@app.route('/api/update', methods=['POST'])
def api_update():
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'pull'],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if 'Already up to date' in output:
                return jsonify({'success': True, 'message': 'Déjà à jour'})
            else:
                return jsonify({'success': True, 'message': 'Mise à jour effectuée. Redémarrez le serveur.'})
        else:
            return jsonify({'success': False, 'message': f'Erreur: {result.stderr}'})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout - vérifiez la connexion'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/test', methods=['POST'])
def api_test():
    config = load_config()
    test_zpl = f"""^XA
^CI28
^PW812
^LL203
^FO50,30^A0N,40,40^FDTEST IMPRIMANTE^FS
^FO50,80^A0N,25,25^FDMALLO BOIS - Raspberry Pi^FS
^FO50,120^A0N,20,20^FD{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}^FS
^XZ"""
    result = send_zpl(test_zpl, config)
    return jsonify(result)


# Initialisation au chargement du module
if not CONFIG_FILE.exists():
    save_config(DEFAULT_CONFIG)
init_google_sheets()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
