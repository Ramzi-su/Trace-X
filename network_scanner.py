import scapy.all as scapy

def scan_network(ip):
    """Scanne le réseau pour découvrir les hôtes actifs."""
    print(f"[*] Début de la découverte des hôtes sur {ip}...")
    arp_request = scapy.ARP(pdst=ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    clients = []
    for element in answered_list:
        clients.append({'ip': element[1].psrc, 'mac': element[1].hwsrc})

    print(f"[*] {len(clients)} hôtes découverts.")
    for client in clients:
        print(f"    - IP: {client['ip']}\tMAC: {client['mac']}")
    
    return [client['ip'] for client in clients]
