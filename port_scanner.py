import nmap

def port_scan(ip):
    """Scanne les ports ouverts sur une IP spécifique."""
    print(f"\n[*] Début du scan de ports pour {ip}...")
    nm = nmap.PortScanner()
    # Scanne les 1024 ports les plus courants. 
    # Pour un scan plus rapide, on peut utiliser nm.scan(ip, '22,80,443')
    # L'argument -sS effectue un scan SYN, rapide et discret. Nécessite sudo.
    nm.scan(ip, '1-1024', '-sS')

    if ip not in nm.all_hosts():
        print(f"    [-] Hôte {ip} semble éteint ou ne répond pas.")
        return

    for host in nm.all_hosts():
        print(f"    [+] Hôte: {host} ({nm[host].hostname()})")
        print(f"    [+] État: {nm[host].state()}")
        
        for proto in nm[host].all_protocols():
            print(f"    [*] Protocole: {proto}")
            lport = nm[host][proto].keys()
            for port in sorted(lport):
                print (f"        - Port : {port}\tÉtat : {nm[host][proto][port]['state']}\tService : {nm[host][proto][port]['name']}")
