from concurrent.futures import ThreadPoolExecutor
import socket
import concurrent.futures
import time
from tqdm import tqdm

ports = range(1, 1024)

# Fonction de scan d'un port
def scan(host, port, timeout = 0.5):

    try:
        # Crée un socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Définit un timeout pour éviter d'attendre indéfiniment (ex: port bloqué)
        sock.settimeout(timeout)
        # Tente de se connecter au port
        result = sock.connect_ex((host, port))
        # Ferme le socket
        sock.close()

        if result == 0:
            return port # 0 = connexion réussie
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

    # On prompte l'utilisateur pour l'adresse IP ou hostname à scanner
    target = input("Entrez l'adresse IP ou hostname : ")

    portsOuverts = []

    startTime = time.time()

    # Utilisation d'un ThreadPoolExecutor pour scanner les ports en parallèle 
    # Solution native de Python pour gérer un pool de threads et exécuter des tâches de manière simultanée.
    # https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor-example
    with ThreadPoolExecutor(max_workers=128) as executor:
        
        # On soumet une tache de scan pour chaque port à l'executor et on garde une référence future_to_port pour associer les résultats aux ports scannés.
        future_to_port = {executor.submit(scan, target, port): port for port in ports}
        
        # On utilise tqdm pour afficher une barre de progression.
        for future in tqdm(concurrent.futures.as_completed(future_to_port), total=len(ports), desc=f"Scan de l'adresse {target}"):
            port = future_to_port[future]
            try:
                result = future.result()
                if result is not None:
                    portsOuverts.append(result)
            except Exception as exc:
                pass
    
    # On affiche le resultat du scan
    print("\nScan terminé.")
    if portsOuverts:
        print("Ports ouverts:")
        for port in sorted(portsOuverts):
            print(f"  Port {port}")
    else:
        print("Aucun port ouvert trouvé.")

    endTime = time.time()
    print(f"Temps de scan: {endTime - startTime:.2f} secondes.")