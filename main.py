#!/usr/bin/env python3

from network_scanner import scan_network
from utils import get_network_range

def main():
    """Fonction principale."""
    print("[*] Lancement du scan automatique du réseau...")
    network_range = get_network_range()
    if network_range:
        scan_network(network_range)
    else:
        print("[!] Impossible de déterminer la plage réseau automatiquement.")

if __name__ == "__main__":
    main()
