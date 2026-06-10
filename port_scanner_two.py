from concurrent.futures import ThreadPoolExecutor
import socket
import concurrent.futures
import time
from tqdm import tqdm
import argparse

# Fonction de scan d'un port
def scan(host, port, timeout = 0.5):

    try:
        # Crée un socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Définit un timeout pour éviter d'attendre indéfiniment (ex: port bloqué)
        sock.settimeout(timeout)
        # Tente de se connecter au port et on récupère le service associé au port
        result = sock.connect_ex((host, port))
        service = socket.getservbyport(port, 'tcp') 
        # Ferme le socket
        sock.close()

        if result == 0:
            # Si le port est ouvert (connexino réussie)
            # On renvoie le port le type de service associé
            return (port, service)
        return None
    

    # Gestion des exceptions courantes
    except socket.timeout:
        # En cas de timeout
        return None
    except ConnectionRefusedError:
        # En cas de refus de connexion
        return None
    except OSError:
        # En cas d'erreur réseau (ex: hôte inaccessible)
        return None

# Script principal
if __name__ == "__main__":

    # On utilise argparse pour permettre à l'utilisateur de spécifier:
    #   - l'adresse IP ou hostname à scanner via la ligne de commande.
    #   - la plage de ports à scanner via la ligne de commande.
    #   - le nombre de threads à utiliser pour le scan (optionnel, par défaut 48).
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', metavar='str', required=True,
                        help='Host to scan')
    parser.add_argument('--ports', metavar='str', required=True,
                        help='port range to scan (ex: "1-1024")')
    parser.add_argument('--threads', metavar='int', required=False, default=48,
                        help='Number of threads to use')
    args = parser.parse_args()

    # On parse la plage de ports fournie par l'utilisateur
    try:
        startPort, endPort = map(int, args.ports.split('-'))

        # On verifie que l;utilisateur n'entre pas de port impossible (negatif ou audela de 65534)
        # ou de port de debut plus grand que le port de fin
        if startPort < 1 or endPort > 65535 or startPort > endPort:
            raise ValueError
        ports = range(startPort, endPort + 1)
    except ValueError:
        print("Invalid port range. Please provide a valid range (ex: '1-1024').")
        exit(1)

    # On récupère l'host depuis les arguments
    target = args.host
    threads = int(args.threads)

    portsOuverts = {}

    print("-"*40)
    print(f"Scan du port {min(ports)} à {max(ports)} en cours sur l'hote {target}...")
    startTime = time.time()

    # Utilisation d'un ThreadPoolExecutor pour scanner les ports en parallèle 
    # Solution native de Python pour gérer un pool de threads et exécuter des tâches de manière simultanée.
    # https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor-example

    # Note: ThreadPoolExecutor inclu de facon native une queue et un lock, il ne sont donc pas explicités
    # mais bien utilisés en interne pour gérer la synchronisation des threads.
    with ThreadPoolExecutor(max_workers=threads) as executor:
        
        # On soumet une tache de scan pour chaque port à l'executor et on garde une référence future_to_port pour associer les résultats aux ports scannés.
        future_to_port = {executor.submit(scan, target, port): port for port in ports}
        
        # On utilise tqdm pour afficher une barre de progression.
        for future in tqdm(concurrent.futures.as_completed(future_to_port), total=len(ports), desc=f"Scan de l'adresse {target}"):
            port = future_to_port[future]
            try:
                (port, service) = future.result()
                if port is not None and service is not None:
                    # Si le port est ouvert, on ajoute le port et le service
                    # associé au dictionnaire des ports ouverts.
                    portsOuverts[port] = service
            except Exception as exc:
                pass
    
    # On affiche le resultat du scan
    print("-"*40)
    print("\nScan terminé.")
    print("-"*40)
    if portsOuverts:
        print("Ports ouverts:")
        for port, service in sorted(portsOuverts.items()):
            print(f"  Port {port} ({service})")
    else:
        print("Aucun port ouvert trouvé.")

    # Affichage du temps de scan
    endTime = time.time()
    print(f"Temps de scan: {endTime - startTime:.2f} secondes.")