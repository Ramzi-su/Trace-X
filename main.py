#!/usr/bin/env python3

import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from network_scanner import scan_network
from port_scanner import port_scan
from utils import get_network_range

def scan_hosts_ports(host_ips):
    """Lance le scan de ports sur une liste d'hôtes en parallèle."""
    print("\n[*] Lancement du scan de ports sur les hôtes découverts...")
    results = []
    # Utilise un ThreadPoolExecutor pour scanner les hôtes en parallèle
    with ThreadPoolExecutor(max_workers=40) as executor:
        # Utilise tqdm pour afficher une barre de progression sur le scan des hôtes
        # executor.map retourne les résultats dans l'ordre où les tâches ont été soumises
        results = list(tqdm(executor.map(port_scan, host_ips), total=len(host_ips), desc="Scanning Hosts"))

    print("\n[*] Scan terminé. Affichage des résultats :")
    for host_result in results:
        # Vérifie si le scan a retourné un résultat et si la liste des ports n'est pas vide
        if host_result and host_result.get('ports'):
            print(f"\n[+] Ports ouverts trouvés pour {host_result['ip']}:")
            for port_info in host_result['ports']:
                print(f"    - Port {port_info['port']:<5} | Service: {port_info['service']}")
        elif host_result:
            # Affiche un message si aucun port ouvert n'a été trouvé pour un hôte
            print(f"\n[-] Aucun port ouvert trouvé pour {host_result['ip']}.")

def main():
    """Fonction principale."""
    # Vérifie si le script est exécuté avec les privilèges root (UID 0)
    if os.geteuid() != 0:
        print("[!] Ce script nécessite des privilèges root pour scanner le réseau.")
        print("[!] Veuillez l'exécuter avec sudo ou avec les capacités appropriées (ex: sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)).")
        return
    print("[*] Lancement du scan automatique du réseau...")
    network_range = get_network_range()
    if network_range:
        clients = scan_network(network_range)
        if clients:
            print(f"[*] {len(clients)} hôtes découverts.")
            for client in clients:
                print(f"    - IP: {client['ip']:<15} MAC: {client['mac']}")
            
            # Extrait les adresses IP pour le scan de ports
            host_ips = [client['ip'] for client in clients]
            scan_hosts_ports(host_ips)
    else:
        print("[!] Impossible de déterminer la plage réseau automatiquement.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Scan interrompu par l'utilisateur. Arrêt du programme.")
        os._exit(0)