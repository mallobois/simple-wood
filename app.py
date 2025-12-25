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
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Chemin du fichier de configuration persistant
CONFIG_FILE = Path(__file__).parent / 'config.json'

# Configuration par défaut
DEFAULT_CONFIG = {
    'printer': {
        'ip': '192.168.1.67',
        'port': 9100,
    },
    'troncons': {
        'serie': '2601',      # Format AANN (année + série)
        'compteur': 0,
        'prefixe': 'TRO-',    # Préfixe avec tiret inclus
        'copies_defaut': 1,
    },
    'paquet': {
        'serie': '2601',
        'compteur': 0,
        'copies_defaut': 1,
    },
    'colis': {
        'serie': '2601',
        'compteur': 0,
        'copies_defaut': 1,
    },
    'utilisateur': {
        'nom': 'Opérateur',
        'site': 'MALLO BOIS',
    }
}


def load_config() -> dict:
    """Charge la configuration depuis le fichier JSON"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Fusion avec les valeurs par défaut (pour les nouvelles clés)
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
    """Sauvegarde la configuration dans le fichier JSON"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde config: {e}")


def send_zpl(zpl_code: str, config: dict) -> dict:
    """Envoie le code ZPL à l'imprimante via réseau TCP/IP"""
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
    """Formate le numéro en 'XX XX XX' (6 chiffres avec espaces)"""
    s = f"{n:06d}"
    return f"{s[0:2]} {s[2:4]} {s[4:6]}"


def format_numero_compact(n: int) -> str:
    """Formate le numéro en '000000' (6 chiffres sans espaces)"""
    return f"{n:06d}"


def generate_zpl_troncons(config: dict) -> str:
    """
    Génère le code ZPL pour une étiquette tronçons 4x2 pouces
    QR code 44x44mm à gauche, numéro XX XX XX à droite (49mm, aligné droite)
    """
    prefixe = config['troncons'].get('prefixe', 'TRO-')
    serie = config['troncons']['serie']
    compteur = config['troncons']['compteur']
    
    # Code QR: TRO-2601-000000 (préfixe inclut déjà le tiret)
    qr_data = f"{prefixe}{serie}-{format_numero_compact(compteur)}"
    
    # Numéro affiché: 00 00 00
    numero_affiche = format_numero(compteur)
    
    # ZPL pour étiquette 4x2 pouces (812x406 dots à 203dpi)
    # QR code 44x44mm (magnification 18) à gauche
    # Série en haut droite (5mm)
    # Numéro XX XX XX à droite (15mm)
    # MALLO BOIS en bas droite (4mm)
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
    """
    Génère le code ZPL pour une étiquette paquet
    """
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
^FDMA{qr_data}^FS

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
    """
    Génère le code ZPL pour une étiquette colis/expédition
    Format 4x6 pouces (100x150mm)
    """
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
^FDMA{qr_data}^FS

^FO400,600^A0N,70,70^FD{numero}^FS
^FO400,700^A0N,28,28^FDColis N°^FS

^FO30,900^GB750,2,2^FS

^FO30,930^A0N,24,24^FDDate: {datetime.now().strftime('%d/%m/%Y %H:%M')}^FS

^XZ"""
    
    return zpl


# ============== ROUTES ==============

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/troncons')
def page_troncons():
    """Page étiquettes tronçons"""
    config = load_config()
    return render_template('troncons.html', config=config)


@app.route('/paquets')
def page_paquets():
    """Page étiquettes paquets"""
    config = load_config()
    return render_template('paquets.html', config=config)


@app.route('/colis')
def page_colis():
    """Page étiquettes colis"""
    config = load_config()
    return render_template('colis.html', config=config)


@app.route('/parametres')
def page_parametres():
    """Page paramètres"""
    config = load_config()
    return render_template('parametres.html', config=config)


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Récupère la configuration complète"""
    config = load_config()
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def api_save_config():
    """Sauvegarde la configuration"""
    data = request.json
    config = load_config()
    
    # Mise à jour sélective
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
    
    if 'utilisateur' in data:
        config['utilisateur']['nom'] = data['utilisateur'].get('nom', config['utilisateur']['nom'])
        config['utilisateur']['site'] = data['utilisateur'].get('site', config['utilisateur']['site'])
    
    save_config(config)
    return jsonify({'success': True, 'config': config})


@app.route('/api/print/troncons', methods=['POST'])
def api_print_troncons():
    """Imprime une ou plusieurs étiquettes tronçons (même numéro)"""
    config = load_config()
    data = request.json or {}
    
    # Nombre de copies (même numéro pour toutes)
    copies = int(data.get('copies', config['troncons']['copies_defaut']))
    copies = min(max(copies, 1), 50)
    
    # Générer le ZPL une seule fois (même numéro)
    zpl = generate_zpl_troncons(config)
    numero_imprime = format_numero(config['troncons']['compteur'])
    
    # Envoyer X fois le même ZPL
    results = []
    for i in range(copies):
        result = send_zpl(zpl, config)
        results.append(result)
        if not result['success']:
            break
    
    success = all(r['success'] for r in results)
    printed = len([r for r in results if r['success']])
    
    # Incrémenter le compteur UNE SEULE FOIS après impression
    if printed > 0:
        config['troncons']['compteur'] = (config['troncons']['compteur'] + 1) % 1000000
        save_config(config)
    
    return jsonify({
        'success': success,
        'message': f'{printed}/{copies} copie(s) imprimée(s) - N° {numero_imprime}',
        'zpl_preview': zpl,
        'compteur': config['troncons']['compteur'],
        'numero_imprime': numero_imprime
    })


@app.route('/api/print/paquet', methods=['POST'])
def api_print_paquet():
    """Imprime une ou plusieurs étiquettes paquet (même numéro)"""
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
        config['paquet']['compteur'] = (config['paquet']['compteur'] + 1) % 1000000
        save_config(config)
    
    return jsonify({
        'success': success,
        'message': f'{printed}/{copies} copie(s) imprimée(s) - N° {numero_imprime}',
        'zpl_preview': zpl,
        'compteur': config['paquet']['compteur'],
        'numero_imprime': numero_imprime
    })


@app.route('/api/print/colis', methods=['POST'])
def api_print_colis():
    """Imprime une ou plusieurs étiquettes colis (même numéro)"""
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
        config['colis']['compteur'] = (config['colis']['compteur'] + 1) % 1000000
        save_config(config)
    
    return jsonify({
        'success': success,
        'message': f'{printed}/{copies} copie(s) imprimée(s) - N° {numero_imprime}',
        'zpl_preview': zpl,
        'compteur': config['colis']['compteur'],
        'numero_imprime': numero_imprime
    })


@app.route('/api/preview/<label_type>', methods=['POST'])
def api_preview(label_type):
    """Prévisualise une étiquette sans imprimer ni incrémenter"""
    config = load_config()
    data = request.json or {}
    
    if label_type == 'troncons':
        zpl = generate_zpl_troncons(config)
    elif label_type == 'paquet':
        zpl = generate_zpl_paquet(data, config)
    elif label_type == 'colis':
        zpl = generate_zpl_colis(data, config)
    else:
        return jsonify({'success': False, 'message': 'Type inconnu'}), 400
    
    return jsonify({'success': True, 'zpl': zpl})


@app.route('/api/test', methods=['POST'])
def api_test():
    """Test de connexion à l'imprimante"""
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


if __name__ == '__main__':
    # Créer le fichier config s'il n'existe pas
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
