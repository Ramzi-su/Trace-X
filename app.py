#!/usr/bin/env python3

import os
import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
import socketio

# Importe la logique de scan existante
from network_scanner import scan_network
from port_scanner import port_scan
from utils import get_network_range, identify_device_type, get_vendor

# Définit le répertoire de base du projet pour des chemins de fichiers robustes
BASE_DIR = Path(__file__).resolve().parent

# Initialisation du serveur ASGI Socket.IO et de l'application FastAPI
sio = socketio.AsyncServer(async_mode='asgi')
app = FastAPI()
app.mount("/socket.io", socketio.ASGIApp(sio))

@app.get("/")
async def read_index():
    """Sert le fichier HTML principal."""
    # Utilise un chemin absolu pour éviter les erreurs de répertoire de travail
    return FileResponse(BASE_DIR / 'templates' / 'index.html')

@sio.on('connect')
async def handle_connect(sid, environ):
    """Gère la connexion d'un nouveau client web."""
    print(f'Client connecté: {sid}')
    await sio.emit('status_update', {'msg': 'Prêt à démarrer le scan.'}, to=sid)

async def run_network_scan_task():
    """
    Tâche de fond pour la découverte du réseau (ARP scan).
    Exécute le code synchrone dans un thread pour ne pas bloquer l'event loop.
    """
    if os.geteuid() != 0:
        await sio.emit('status_update', {'msg': 'Erreur: Le serveur doit être lancé avec les privilèges root (sudo).', 'level': 'error'})
        return

    await sio.emit('status_update', {'msg': 'Détection de la plage réseau...'})
    network_range = await asyncio.to_thread(get_network_range)
    if not network_range:
        await sio.emit('status_update', {'msg': 'Impossible de déterminer la plage réseau.', 'level': 'error'})
        return

    await sio.emit('status_update', {'msg': f'Découverte des hôtes sur {network_range}...'})
    clients = await asyncio.to_thread(scan_network, network_range)
    if not clients:
        await sio.emit('status_update', {'msg': 'Aucun hôte découvert.', 'level': 'warning'})
        return
    
    await sio.emit('status_update', {'msg': f'{len(clients)} hôtes découverts. Prêt pour l\'analyse des ports.', 'level': 'success'})
    
    for client in clients:
        vendor = await asyncio.to_thread(get_vendor, client['mac'])
        await sio.emit('host_discovered', {
            'ip': client['ip'],
            'mac': client['mac'],
            'vendor': vendor or 'N/A',
        })

async def run_port_scan_task(hosts):
    """
    Tâche de fond pour le scan de ports sur une liste d'hôtes fournie.
    """
    try:
        import netifaces
        gateway_ip = netifaces.gateways()['default'][netifaces.AF_INET][0]
    except Exception:
        gateway_ip = None

    async def scan_one_host(host, index, total):
        ip, mac = host['ip'], host['mac']
        await sio.emit('status_update', {'msg': f'Analyse des ports sur {ip} ({index+1}/{total})...'})
        
        port_result = await asyncio.to_thread(port_scan, ip)
        device_type = await asyncio.to_thread(identify_device_type, mac, port_result['ports'], ip, gateway_ip)
        
        await sio.emit('scan_result', {'ip': ip, 'device_type': device_type, 'ports': port_result['ports']})

    tasks = [scan_one_host(host, i, len(hosts)) for i, host in enumerate(hosts)]
    await asyncio.gather(*tasks)

    await sio.emit('status_update', {'msg': 'Analyse des ports terminée.', 'level': 'success'})

@sio.on('start_network_scan')
async def handle_start_network_scan(sid):
    """Démarre la découverte du réseau dans une tâche de fond."""
    print(f"Demande de scan réseau reçue de {sid}.")
    sio.start_background_task(run_network_scan_task)

@sio.on('start_port_scan')
async def handle_start_port_scan(sid, data):
    """Démarre le scan de ports sur les hôtes fournis par le client."""
    hosts = data.get('hosts', [])
    if not hosts:
        return
    print(f"Demande d'analyse de ports reçue pour {len(hosts)} hôtes.")
    sio.start_background_task(run_port_scan_task, hosts)

if __name__ == '__main__':
    print("[!] Ce script doit être lancé avec Uvicorn. Utilisez la commande :")
    print("[!] sudo .venv/bin/uvicorn app:app --host 0.0.0.0 --port 5000")