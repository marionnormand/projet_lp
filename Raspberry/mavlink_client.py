import collections.abc
import collections
collections.MutableMapping = collections.abc.MutableMapping
collections.Mapping = collections.abc.Mapping
collections.Sequence = collections.abc.Sequence

import time
from dronekit import connect, VehicleMode

def connect_mavlink():
    connection_string = '/dev/ttyACM0'
    print(f"Connexion au drone sur {connection_string}...")
    vehicle = connect(connection_string, baud=921600, wait_ready=True, timeout=60)
    print("DroneKit : Connecté au drone !")
    return vehicle

def deconnexion_mavlink(vehicle):
    if vehicle:
        print("DroneKit : Déconnexion...")
        vehicle.close()

def listen_mavlink(vehicle, passerelle_mqtt, stop_event): 
    print("Thread MAVLink : Démarrage de la boucle d'écoute de télémétrie.")
    
    while not stop_event.is_set():
        try:
            # Récupération des données du drone
            tension = vehicle.battery.voltage
            pourcentage = vehicle.battery.level
            vitesse = vehicle.groundspeed
            mode = vehicle.mode.name
            arme = vehicle.armed
            location = vehicle.location.global_relative_frame
            lat = location.lat
            lon = location.lon
            alt = location.alt
            
            print(f"\n--- [TÉLÉMÉTRIE DRONE] ---")
            print(f"Version Firmware : {vehicle.version}")
            print(f"Batterie         : {tension}V ({pourcentage}%)")
            print(f"Vitesse          : {vitesse} m/s")
            print(f"Mode             : {mode} | Armé : {arme}")
            print(f"location         : Lat: {lat}, Lon: {lon}, alt: {alt}\n")
            
            passerelle_mqtt.publier("projet/drone/batterie", f"{tension}")
            if arme == True: 
            	passerelle_mqtt.publier("projet/drone/trajet", "Oui")
            else:
            	passerelle_mqtt.publier("projet/drone/trajet", "Non")

            if mode == "STABILIZE":
                print("Changement de mode détecté : Passage en GUIDED...")
                vehicle.mode = VehicleMode("GUIDED")
            
            time.sleep(2)

        except Exception as e:
            print(f"Erreur dans la boucle MAVLink/DroneKit : {e}")
            time.sleep(1)
            
    print("Thread MAVLink : Boucle d'écoute arrêtée.")
    
    
def send_mavlink(vehicle, latitude, longitude, altitude): 
	if not vehicle.armed:
		print("Erreur : Impossible d'envoyer la commande, le drone n'est pas en mode armé")
		return False
	if vehicle.mode.name != "GUIDED":
		print("Changement de mode forcé : Passage en mode GUIDED") 
		vehicle.mode = VehicleMode("GUIDED") 
		timout = 5
		while vehicle.mode.name != "GUIDED" and timout > 0: 
			time.sleep(0.5)
			timout -= 0.5
		if vehicle.mode.name != "GUIDED":
			print("Erreur : le Pixhawk a refusé de passer en mode GUIDED")
			return False 
			
	print(f"Envoi : Lat: {latitude}, Lon: {longitude}, Alt: {altitude}m")
	cible = LocationGlobalRelative(latitude, longitude, altitude)
	vehicle.simple_goto(cible)
	print("Commande MAVlink envoyée avec succès")
	return True
