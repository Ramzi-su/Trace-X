#!/usr/bin/env python3

import os
import signal
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio
import google.generativeai as genai
from dotenv import load_dotenv

# Importe la logique de scan existante
# Assurez-vous que ces fichiers existent bien dans votre dossier
from network_scanner import scan_network
from port_scanner import port_scan
from utils import get_network_range, identify_device_type, get_vendor

# Définit le répertoire de base du projet
BASE_DIR = Path(__file__).resolve().parent

# --- 1. Initialisation unique de l'application ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# --- 2. Montage des fichiers statiques (CSS/JS) ---
# C'est ici que la magie opère pour que /static/style.css fonctionne
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# --- 3. Configuration des Templates (HTML) ---
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Montage de SocketIO sur FastAPI
app.mount("/socket.io", socketio.ASGIApp(sio))

# --- Configuration de l'IA ---
load_dotenv()
chat_histories = {} 
api_key = None

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print("[Info] API Gemini configurée avec succès.")
    else:
        print("[Avertissement] GOOGLE_API_KEY non trouvée.")
except Exception as e:
    print(f"[Erreur] Config Gemini : {e}")

# --- 4. LA ROUTE PRINCIPALE ---
@app.get("/")
async def read_root(request: Request):
    """
    Sert le fichier HTML en utilisant le moteur de template.
    Ceci permet de transformer {{ url_for(...) }} en liens réels.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------------------------------------------------------
# --- LOGIQUE SOCKET.IO (Scan & Chat) ---
# ------------------------------------------------------------------

@sio.on('connect')
async def handle_connect(sid, environ):
    print(f'Client connecté: {sid}')
    await sio.emit('status_update', {'msg': 'Prêt à démarrer le scan.'}, to=sid)

@sio.on('disconnect')
async def handle_disconnect(sid):
    print(f'Client déconnecté: {sid}')
    if sid in chat_histories:
        del chat_histories[sid]

async def run_network_scan_task(sid):
    if os.geteuid() != 0:
        await sio.emit('status_update', {'msg': 'Erreur: Root requis (sudo).', 'level': 'error'}, to=sid)
        return

    await sio.emit('status_update', {'msg': 'Détection de la plage réseau...'}, to=sid)
    network_range = await asyncio.to_thread(get_network_range)
    
    if not network_range:
        await sio.emit('status_update', {'msg': 'Impossible de déterminer la plage réseau.', 'level': 'error'}, to=sid)
        return

    await sio.emit('status_update', {'msg': f'Découverte des hôtes sur {network_range}...'}, to=sid)
    clients = await asyncio.to_thread(scan_network, network_range)
    
    if not clients:
        await sio.emit('status_update', {'msg': 'Aucun hôte découvert.', 'level': 'warning'}, to=sid)
        return
    
    await sio.emit('status_update', {'msg': f'{len(clients)} hôtes découverts.', 'level': 'success'}, to=sid)
    
    for client in clients:
        vendor = await asyncio.to_thread(get_vendor, client['mac'])
        await sio.emit('host_discovered', {
            'ip': client['ip'],
            'mac': client['mac'],
            'vendor': vendor or 'N/A',
        }, to=sid)

async def run_single_host_scan_task(sid, ip_target):
    if os.geteuid() != 0:
        await sio.emit('status_update', {'msg': 'Erreur: Root requis.', 'level': 'error'}, to=sid)
        return

    await sio.emit('status_update', {'msg': f'Vérification de {ip_target}...'}, to=sid)
    clients = await asyncio.to_thread(scan_network, ip_target)
    
    if not clients:
        await sio.emit('status_update', {'msg': f'Hôte {ip_target} introuvable.', 'level': 'error'}, to=sid)
        await sio.emit('port_scan_complete', {})
        return
    
    client = clients[0]
    vendor = await asyncio.to_thread(get_vendor, client['mac'])
    await sio.emit('host_discovered', {
        'ip': client['ip'],
        'mac': client['mac'],
        'vendor': vendor or 'N/A',
    }, to=sid)

    await run_port_scan_task(sid, [client])

async def run_port_scan_task(sid, hosts):
    try:
        import netifaces
        gateway_ip = netifaces.gateways()['default'][netifaces.AF_INET][0]
    except Exception:
        gateway_ip = None

    async def scan_one_host(host, index, total):
        ip, mac = host['ip'], host['mac']
        await sio.emit('status_update', {'msg': f'Scan ports {ip} ({index+1}/{total})...'}, to=sid)
        port_result = await asyncio.to_thread(port_scan, ip)
        open_ports = port_result.get('ports', []) if port_result else []
        device_type = await asyncio.to_thread(identify_device_type, mac, open_ports, ip, gateway_ip)
        await sio.emit('scan_result', {'ip': ip, 'device_type': device_type, 'ports': open_ports}, to=sid)

    tasks = [scan_one_host(host, i, len(hosts)) for i, host in enumerate(hosts)]
    await asyncio.gather(*tasks)

    await sio.emit('status_update', {'msg': 'Analyse terminée.', 'level': 'success'}, to=sid)
    await sio.emit('port_scan_complete', {}, to=sid)

@sio.on('start_network_scan')
async def handle_start_network_scan(sid):
    sio.start_background_task(run_network_scan_task, sid)

@sio.on('start_port_scan')
async def handle_start_port_scan(sid, data):
    hosts = data.get('hosts', [])
    if hosts:
        sio.start_background_task(run_port_scan_task, sid, hosts)

@sio.on('start_single_host_port_scan')
async def handle_single_host_port_scan(sid, data):
    ip_target = data.get('target')
    if ip_target:
        sio.start_background_task(run_single_host_scan_task, sid, ip_target)

@sio.on('chat_message')
async def handle_chat_message(sid, data):
    if not api_key:
        await sio.emit('ai_response', {'error': "Clé API manquante."}, to=sid)
        return

    user_input = data.get('message')
    scan_context_str = data.get('scan_context')
    
    if not user_input: 
        return

    try:
        # On ne recrée la session que si elle n'existe pas
        if sid not in chat_histories:
            
            # --- Consigne : Expert Cyber + Adaptation à la langue ---
            system_instruction = (
                "Tu es Trace-X, un expert en cybersécurité et réseaux. "
                "Voici tes directives strictes : "
                "1. ADAPTATION LANGUISTIQUE : Réponds TOUJOURS dans la même langue que celle utilisée par l'utilisateur dans son message (Français, Anglais, Arabe, Espagnol, etc.). "
                "2. SUJET : Tu ne dois répondre QU'AUX questions liées à l'informatique, au réseau, à la sécurité ou au hacking éthique. "
                "3. HORS-SUJET : Si l'utilisateur te parle d'un autre sujet (cuisine, sport, politique...), refuse poliment d'intervenir en expliquant que ce n'est pas ton domaine (dans la langue de l'utilisateur). "
                "4. DONNÉES : Si des données de scan sont fournies ci-dessous, utilise-les pour répondre, sinon réponds aux questions théoriques."
            )

            # On joint le contexte technique
            full_prompt = (
                f"{system_instruction}\n\n"
                f"DONNÉES DU SCAN (JSON) : {scan_context_str}"
            )

            model = genai.GenerativeModel('gemini-flash-latest')
            chat_session = model.start_chat(history=[
                {'role': 'user', 'parts': [full_prompt]},
                {'role': 'model', 'parts': ["Compris. Je répondrai dans la langue de l'utilisateur et uniquement sur la cybersécurité."]}
            ])
            chat_histories[sid] = chat_session

        chat_session = chat_histories[sid]
        
        # Envoi du message utilisateur
        response = await asyncio.to_thread(chat_session.send_message, user_input)
        await sio.emit('ai_response', {'response': response.text}, to=sid)

    except Exception as e:
        print(f"Erreur IA: {e}")
        await sio.emit('ai_response', {'error': "Erreur de communication avec l'IA."}, to=sid)
@sio.on('shutdown_server')
async def handle_shutdown(sid):
    print(f"Demande d'arrêt reçue de {sid}")
    
    # 1. Prévenir l'utilisateur que c'est fini
    await sio.emit('status_update', {
        'msg': 'Arrêt du serveur en cours... Vous pouvez fermer cet onglet.', 
        'level': 'error' # Rouge pour signaler l'arrêt
    }, to=sid)

    # 2. Fonction pour tuer le processus
    def kill_server():
        print("Arrêt du système (SIGINT)...")
        os.kill(os.getpid(), signal.SIGINT) # Simule le CTRL+C

    # 3. On attend 1 seconde pour que le message 'status_update' ait le temps de partir
    loop = asyncio.get_running_loop()
    loop.call_later(1, kill_server)
if __name__ == '__main__':
    print("Lancez avec : sudo .venv/bin/uvicorn app:app --host 127.0.0.1 --port 5000")