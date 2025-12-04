import netifaces
import ipaddress

def get_network_range():
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
