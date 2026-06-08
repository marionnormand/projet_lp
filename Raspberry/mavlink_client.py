# mavlink_client.py
import collections.abc
import collections
# Tes patchs indispensables pour DroneKit sur les Python récents :
collections.MutableMapping = collections.abc.MutableMapping
collections.Mapping = collections.abc.Mapping
collections.Sequence = collections.abc.Sequence

import time
from dronekit import connect, VehicleMode

def connect_mavlink():
    """Se connecte au drone et renvoie l'objet vehicle."""
    connection_string = '/dev/ttyACM0'
    print(f"Connexion au drone sur {connection_string}...")
    # Augmentation du timeout au cas où le démarrage est lent
    vehicle = connect(connection_string, baud=921600, wait_ready=True, timeout=60)
    print("✅ DroneKit : Connecté au drone !")
    return vehicle

def deconnexion_mavlink(vehicle):
    """Déconnecte proprement le drone s'il existe."""
    if vehicle:
        print("🔌 DroneKit : Déconnexion...")
        vehicle.close()

def listen_mavlink(vehicle, passerelle_mqtt, stop_event): 
    """Cette fonction va tourner en tâche de fond dans un Thread dédié."""
    print("🚀 Thread MAVLink : Démarrage de la boucle d'écoute de télémétrie.")
    
    while not stop_event.is_set():
        try:
            # Récupération des données du drone
            tension = vehicle.battery.voltage
            pourcentage = vehicle.battery.level
            vitesse = vehicle.groundspeed
            mode = vehicle.mode.name
            arme = vehicle.armed
            
            # Affichage console pour debug
            print(f"\n--- [TÉLÉMÉTRIE DRONE] ---")
            print(f"Version Firmware : {vehicle.version}")
            print(f"Batterie         : {tension}V ({pourcentage}%)")
            print(f"Vitesse          : {vitesse} m/s")
            print(f"Mode             : {mode} | Armé : {arme}")
            
            # --- ENVOI VERS MQTT ---
            # On publie les données vers MQTT (au format chaîne ou JSON)
            passerelle_mqtt.publier("projet/drone/batterie", f"{tension}")
            if arme == True: 
            	passerelle_mqtt.publier("projet/drone/trajet", "Oui")
            else:
            	passerelle_mqtt.publier("projet/drone/trajet", "Non")

            # Changement de mode automatique pour ton test
            if mode == "STABILIZE":
                print("🔄 Changement de mode détecté : Passage en GUIDED...")
                vehicle.mode = VehicleMode("GUIDED")
            
            # Fréquence de rafraîchissement (ex: toutes les 2 secondes)
            time.sleep(2)

        except Exception as e:
            print(f"⚠️ Erreur dans la boucle MAVLink/DroneKit : {e}")
            time.sleep(1)
            
    print("🔌 Thread MAVLink : Boucle d'écoute arrêtée.")
