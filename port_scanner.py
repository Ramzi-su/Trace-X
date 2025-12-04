import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_single_port(ip, port, timeout=0.5):
    """
    Tente de se connecter à un port unique sur une IP donnée.
    Retourne le numéro du port s'il est ouvert, sinon None.
    """
    try:
        # Crée un nouveau socket pour chaque thread
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            # connect_ex retourne 0 en cas de succès, indiquant un port ouvert
            if s.connect_ex((ip, port)) == 0:
                return port
    except (socket.timeout, socket.error):
        # Ignore les erreurs de connexion ou les timeouts
        pass
    return None

def port_scan(ip):
    """
    Scanne les ports 1 à 1024 sur une IP spécifique en utilisant des sockets et le multithreading.
    """
    open_ports_info = []
    ports_to_scan = range(1, 65536) # Étend la plage à tous les ports possibles

    # Utilise ThreadPoolExecutor pour scanner les ports en parallèle
    with ThreadPoolExecutor(max_workers=200) as executor:
        # Crée une tâche pour chaque port à scanner
        future_to_port = {executor.submit(scan_single_port, ip, port): port for port in ports_to_scan}

        for future in as_completed(future_to_port):
            result = future.result()
            if result is not None:
                port = result
                try:
                    service_name = socket.getservbyport(port, "tcp")
                except OSError:
                    service_name = "unknown"
                open_ports_info.append({'port': port, 'service': service_name})
    
    # Retourne un dictionnaire avec l'IP et la liste des ports/services trouvés
    return {'ip': ip, 'ports': sorted(open_ports_info, key=lambda x: x['port'])}
