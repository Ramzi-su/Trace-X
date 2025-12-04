import netifaces
import ipaddress
import requests
import os
import time
import scapy.all as scapy

OUI_FILE = "oui.txt"
OUI_DB = {}

def get_network_range(): # No changes to this function
    """
    Récupère la plage réseau de l'interface par défaut au format CIDR.
    """
    try:
        # Trouver la passerelle par défaut
        gws = netifaces.gateways()
        default_gateway = gws.get('default')
        if not default_gateway or not netifaces.AF_INET in default_gateway:
            raise Exception("Impossible de trouver la passerelle par défaut.")

        # Récupérer l'interface et l'IP de la passerelle
        gateway_ip, iface = default_gateway[netifaces.AF_INET]

        # Récupérer les adresses de l'interface
        addrs = netifaces.ifaddresses(iface)
        if not netifaces.AF_INET in addrs:
            raise Exception(f"Impossible de trouver les adresses AF_INET pour l'interface {iface}.")

        # Récupérer l'IP et le masque de sous-réseau
        ip_info = addrs[netifaces.AF_INET][0]
        ip = ip_info['addr']
        netmask = ip_info['netmask']

        # Calculer le réseau CIDR
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network.with_prefixlen)
        
    except Exception as e:
        print(f"[!] Erreur lors de la récupération de la plage réseau : {e}")
        # Fallback vers une autre méthode si netifaces échoue
        try:
            import scapy.all as scapy
            for iface_name in scapy.get_if_list():
                ip = scapy.get_if_addr(iface_name)
                # Scapy ne fournit pas de moyen direct et fiable pour le masque de sous-réseau sur toutes les plateformes
                # Cette partie reste donc une source potentielle de problèmes
                if ip and ip != '127.0.0.1':
                     # On suppose un masque /24 par défaut si on ne peut pas le trouver
                    return f"{ip.rsplit('.', 1)[0]}.0/24"
            return None
        except ImportError:
            print("[!] Scapy n'est pas installé, le fallback est impossible.")
            return None
        except Exception as scapy_e:
            print(f"[!] Erreur du fallback Scapy : {scapy_e}")
            return None

def _update_oui_database():
    """
    Télécharge la base de données OUI depuis le site de l'IEEE si le fichier local
    est absent ou date de plus de 30 jours.
    """
    needs_update = True
    if os.path.exists(OUI_FILE):
        file_age = time.time() - os.path.getmtime(OUI_FILE)
        if file_age < 30 * 86400: # 30 jours
            needs_update = False

    if needs_update:
        print("[*] Mise à jour de la base de données des fabricants (OUI)...")
        try:
            url = "http://standards-oui.ieee.org/oui/oui.txt"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(OUI_FILE, 'w') as f:
                f.write(response.text)
            print("[+] Base de données mise à jour avec succès.")
        except requests.RequestException as e:
            print(f"[!] Échec du téléchargement de la base de données OUI : {e}")

def _load_oui_database():
    """Charge la base de données OUI depuis le fichier local en mémoire."""
    global OUI_DB
    if OUI_DB: # Déjà chargée
        return

    _update_oui_database()

    if not os.path.exists(OUI_FILE):
        print("[!] Fichier OUI non trouvé, l'identification du fabricant sera limitée.")
        return

    with open(OUI_FILE, 'r') as f:
        for line in f:
            if "(base 16)" in line:
                parts = line.split("(base 16)")
                mac_prefix = parts[0].strip().replace('-', '')
                vendor = parts[1].strip()
                OUI_DB[mac_prefix] = vendor

def get_vendor(mac):
    """Récupère le fabricant à partir de l'adresse MAC en utilisant la base de données locale."""
    if not OUI_DB:
        _load_oui_database()
    
    mac_prefix = mac.replace(':', '').upper()[:6]
    try:
        return OUI_DB.get(mac_prefix)
    except Exception:
        return None

def identify_device_type(mac, open_ports, ip, gateway_ip):
    """
    Tente d'identifier le type d'appareil en se basant sur le fabricant de la carte réseau (MAC)
    et les ports ouverts.
    """
    # Si l'IP correspond à la passerelle, c'est le routeur principal.
    try:
        first_octet = int(mac.split(':')[0], 16)
        if (first_octet & 2) == 2:
            return "Device (Randomized MAC)"
    except (ValueError, IndexError):
        pass

    if ip == gateway_ip:
        return "Router (Gateway)"

    open_ports_set = {p['port'] for p in open_ports}

    # Heuristiques basées sur les ports
    if {53, 80, 443}.issubset(open_ports_set):
        return "Router/Gateway"
    if 3389 in open_ports_set or {135, 139, 445}.issubset(open_ports_set):
        return "Windows PC"
    if 631 in open_ports_set or 9100 in open_ports_set:
        return "Printer"
    if 22 in open_ports_set and len(open_ports_set) < 5:
        return "Network Device/Server (SSH)"

    # Heuristiques basées sur le fabricant (MAC)
    try:
        vendor = get_vendor(mac)
        if vendor:
            vendor_upper = vendor.upper()
            if any(name in vendor_upper for name in ["APPLE"]):
                return "Apple Device (iPhone/Mac)"
            if any(name in vendor_upper for name in ["SAMSUNG", "HUAWEI", "GOOGLE", "ONEPLUS", "GAO SHENG DA", "TP-LINK TECHNOLOGIES"]):
                return "Android/IoT/Router Device"
            if any(name in vendor_upper for name in ["NETGEAR", "ASUSTEK", "DLINK"]):
                return "Router/Switch"
            
            # Si un fabricant est trouvé mais non classifié, on l'affiche
            return f"Device (NIC: {vendor.title()})"
            
    except Exception: # Attrape toute autre exception potentielle
        pass # On continue vers les autres heuristiques

    return "Unknown"
