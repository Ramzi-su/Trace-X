#!/usr/bin/env python3

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from network_scanner import scan_network
from port_scanner import port_scan
from utils import get_network_range, identify_device_type

class Colors:
    """Classe pour les codes de couleur ANSI pour le terminal."""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

def print_banner():
    """Affiche la bannière de l'application."""
    banner = f"""
  {Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗
  ║ {Colors.BOLD}   ████████╗██████╗  █████╗  ██████╗███████╗    ██╗  ██╗          {Colors.CYAN}║
  ║ {Colors.BOLD}   ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝    ╚██╗██╔╝          {Colors.CYAN}║
  ║ {Colors.BOLD}      ██║   ██████╔╝███████║██║     █████╗       ╚███╔╝           {Colors.CYAN}║
  ║ {Colors.BOLD}      ██║   ██╔══██╗██╔══██║██║     ██╔══╝       ██╔██╗           {Colors.CYAN}║
  ║ {Colors.BOLD}      ██║   ██║  ██║██║  ██║╚██████╗███████╗    ██╔╝ ██╗          {Colors.CYAN}║
  ║ {Colors.BOLD}      ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝    ╚═╝  ╚═╝          {Colors.CYAN}║
  ║                                                                   ║
  ║      {Colors.YELLOW}📡  A Network Discovery & Port Scanning Tool 💻{Colors.CYAN}              ║
  ║                       {Colors.RED}By Moulahi Ramzi{Colors.CYAN}                            ║
  ╚═══════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)

def scan_hosts_ports(host_ips):
    """Lance le scan de ports sur une liste d'hôtes en parallèle."""
    print(f"\n{Colors.YELLOW}[*] Lancement du scan de ports sur les hôtes découverts...{Colors.RESET}")
    results = []
    # Utilise ThreadPoolExecutor avec as_completed pour une meilleure stabilité
    # que d'envelopper directement executor.map avec tqdm.
    with ThreadPoolExecutor(max_workers=40) as executor:
        # Soumet chaque tâche de scan de port et crée une barre de progression
        future_to_host = {executor.submit(port_scan, ip): ip for ip in host_ips}
        
        for future in tqdm(as_completed(future_to_host), total=len(host_ips), desc=f"{Colors.GREEN}Scanning Hosts{Colors.RESET}"):
            # Récupère le résultat dès qu'une tâche est terminée
            results.append(future.result())
    return results

def display_results(clients, port_scan_results):
    """Affiche les résultats finaux de manière organisée."""
    # Crée un mapping IP -> MAC pour un accès facile
    mac_map = {client['ip']: client['mac'] for client in clients}
    
    # Récupère l'IP de la passerelle pour une identification plus précise du routeur
    try:
        import netifaces
        gateway_ip = netifaces.gateways()['default'][netifaces.AF_INET][0]
    except Exception:
        gateway_ip = None

    print(f"\n{Colors.BOLD}{Colors.GREEN}[*] Scan terminé. Affichage des résultats :{Colors.RESET}")
    for host_result in port_scan_results:
        # Vérifie si le scan a retourné un résultat et si la liste des ports n'est pas vide
        if host_result and host_result.get('ports'):
            ip = host_result['ip']
            mac = mac_map.get(ip, 'N/A')
            device_type = identify_device_type(mac, host_result['ports'], ip, gateway_ip)

            print(f"\n{Colors.GREEN}[+]{Colors.RESET} Hôte: {Colors.BOLD}{Colors.BLUE}{ip}{Colors.RESET} ({Colors.CYAN}{device_type}{Colors.RESET})")
            for port_info in host_result['ports']:
                print(f"    - Port {Colors.YELLOW}{port_info['port']:<5}{Colors.RESET} | Service: {port_info['service']}")

def run_scan(clients, host_ips):
    """Exécute le scan de ports et affiche les résultats."""
    if not clients:
        print(f"{Colors.RED}[!] Aucun hôte actif trouvé à scanner.{Colors.RESET}")
        return

    print(f"{Colors.GREEN}[*] {len(clients)} hôte(s) à scanner.{Colors.RESET}")
    port_scan_results = scan_hosts_ports(host_ips)
    display_results(clients, port_scan_results)

def main():
    """Fonction principale."""
    print_banner()

    # Vérifie si le script est exécuté avec les privilèges root (UID 0)
    if os.geteuid() != 0:
        print(f"{Colors.RED}[!] Ce script nécessite des privilèges root. Veuillez l'exécuter avec 'sudo'.{Colors.RESET}")
        return

    while True:
        print(f"\n{Colors.BOLD}--- MENU PRINCIPAL ---{Colors.RESET}")
        print("1. Scanner le réseau local (Détection automatique)")
        print("2. Scanner une cible spécifique (IP ou réseau CIDR)")
        print("3. Quitter")
        choice = input(f"{Colors.YELLOW}>> Votre choix : {Colors.RESET}")

        if choice == '1':
            print(f"\n{Colors.YELLOW}[*] Lancement du scan automatique du réseau...{Colors.RESET}")
            network_range = get_network_range()
            if not network_range:
                print(f"{Colors.RED}[!] Impossible de déterminer la plage réseau automatiquement.{Colors.RESET}")
                continue
            
            clients = scan_network(network_range)
            host_ips = [client['ip'] for client in clients]
            run_scan(clients, host_ips)

        elif choice == '2':
            target = input(f"{Colors.YELLOW}>> Entrez l'IP ou la plage CIDR (ex: 192.168.1.50 ou 192.168.1.0/24) : {Colors.RESET}")
            if not target:
                print(f"{Colors.RED}[!] Cible invalide.{Colors.RESET}")
                continue

            print(f"\n{Colors.YELLOW}[*] Lancement du scan sur la cible : {target}{Colors.RESET}")
            if "/" in target: # C'est une plage CIDR
                clients = scan_network(target)
                host_ips = [client['ip'] for client in clients]
            else: # C'est une IP unique
                clients = [{'ip': target, 'mac': 'N/A'}]
                host_ips = [target]
            run_scan(clients, host_ips)

        elif choice == '3':
            print(f"{Colors.CYAN}Au revoir !{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}[!] Choix invalide, veuillez réessayer.{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Scan interrompu par l'utilisateur. Arrêt du programme.{Colors.RESET}")
        os._exit(0)