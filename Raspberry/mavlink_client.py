import collections.abc
import collections
collections.MutableMapping = collections.abc.MutableMapping
collections.Mapping = collections.abc.Mapping
collections.Sequence = collections.abc.Sequence

from dronekit import connect, VehicleMode, LocationGlobalRelative
import math
from gpiozero import AngularServo
import time

servo = AngularServo(17, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0024)

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

def calculer_distance_metres(loc1, loc2):
	dlat = loc2.lat - loc1.lat
	dlong = loc2.lon - loc1.lon
	return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5
	

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
            
            time.sleep(30)

        except Exception as e:
            print(f"Erreur dans la boucle MAVLink/DroneKit : {e}")
            time.sleep(1)
            
    print("Thread MAVLink : Boucle d'écoute arrêtée.")
    
   
def armer_drone(vehicle):
    print("Passage en mode GUIDED...")
    vehicle.mode = VehicleMode("GUIDED")
    while vehicle.mode.name != "GUIDED":
        time.sleep(0.5)
    print("Attente pre-arm checks...")
    while not vehicle.is_armable:
        time.sleep(1)
    print("Armement...")
    vehicle.armed = True
    while not vehicle.armed:
        print("attente d'armement")
        time.sleep(0.5)
    return True
    
def desarmer_drone(vehicle):
    print("\n[Sécurité] Demande de désarmement des moteurs...")
    vehicle.armed = False
    timeout = 10 
    while vehicle.armed and timeout > 0:
        print(" -> En attente du désarmement...")
        time.sleep(0.5)
        timeout -= 0.5
    if not vehicle.armed:
        print("[Sécurité] Les moteurs sont DÉSARMÉS avec succès.")
        return True
    else:
        print("[ALERTE] Le Pixhawk a refusé de désarmer les moteurs !")
        return False
        
   
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
			timeout -= 0.5
		if vehicle.mode.name != "GUIDED":
			print("Erreur : le Pixhawk a refusé de passer en mode GUIDED")
			return False 
			
	print(f"Envoi : Lat: {latitude}, Lon: {longitude}, Alt: {altitude}m")
	cible = LocationGlobalRelative(latitude, longitude, altitude)
	vehicle.simple_goto(cible)
	print("Commande MAVlink envoyée avec succès")
	return True
	
	
def executer_mission_livraison(vehicle, latitude, longitude, altitude):
    print("\n==== DÉBUT DE LA MISSION DE LIVRAISON ====")
    
    # ÉTAPE 1 : Sauvegarder la position de départ 
    while vehicle.gps_0.fix_type < 3 or vehicle.location.global_relative_frame.lat == 0.0:
        print(f" -> Attente signal GPS 3D stable... État actuel : {vehicle.gps_0.fix_type} (Besoin de 3+)")
        time.sleep(2)
    print("[Mission] Signal GPS validé. Stabilisation de la position...")
    time.sleep(3)
    point_depart = vehicle.location.global_relative_frame
    print(f"[Mission] Point de départ enregistré : Lat {point_depart.lat}, Lon {point_depart.lon}")
    
    # armer et décoller 
    if armer_drone(vehicle):
        print(f"[Mission] Décollage automatique à {altitude} mètres...")
        vehicle.simple_takeoff(altitude)
        
        # Boucle d'attente : on vérifie que le drone monte bien à l'altitude demandée
        while True:
            alt_actuelle = vehicle.location.global_relative_frame.alt
            print(f" -> Altitude de décollage actuelle : {alt_actuelle:.2f}m")
            if alt_actuelle >= altitude * 0.95: # Arrivé à 95% de l'altitude cible
                print("[Mission] Altitude de sécurité atteinte. Prêt pour le déplacement.")
                break
            time.sleep(1)
    else:
        print("[ALERTE] Échec de l'armement initial. Mission annulée.")
        return False

    # ÉTAPE 2 : Aller aux coordonnées cibles
    cible = LocationGlobalRelative(latitude, longitude, altitude)
    print(f"[Mission] En route vers la cible...")
    vehicle.simple_goto(cible)
    
    # Attendre que le drone arrive à moins de 2 mètres de la cible
    while True:
        pos_actuelle = vehicle.location.global_relative_frame
        distance = calculer_distance_metres(pos_actuelle, cible)
        print(f" -> Distance restante : {distance:.2f} mètres")
        
        if distance <= 2.0: # Arrivé à moins de 2 mètres
            print("[Mission] Cible atteinte ! Le drone est sur zone.")
            break
        time.sleep(1)

    # ÉTAPE 3 : Atterrissage sur zone
#    print("[Mission] Déclenchement de l'atterrissage (Mode LAND)...")
#    vehicle.mode = VehicleMode("LAND")
    print("[Mission] Déclenchement de l'atterrissage de livraison (Mode LAND)...")
    vehicle.mode = VehicleMode("LAND")

    timeout_atterrissage = 20  # 20 secondes max pour se poser
    while timeout_atterrissage > 0:
        alt_actuelle = vehicle.location.global_relative_frame.alt
        print(f" -> En cours d'atterrissage... altitude : {alt_actuelle:.2f}m (Timeout : {timeout_atterrissage}s)")
        
        # Sécurité : Si le drone est sous les 15cm, on considère qu'il est posé
        if alt_actuelle <= 0.05:
            print("[Mission] Marge d'altitude atteinte (< 5cm). Drone considéré comme posé.")
            break
            
        time.sleep(1)
        timeout_atterrissage -= 1

    print("[Sécurité] Passage en mode GUIDED pour maintenir les moteurs actifs...")
    vehicle.mode = VehicleMode("GUIDED")
    while vehicle.mode.name != "GUIDED":
        time.sleep(0.1)

    print("[Mission] Le drone est stabilisé au sol, moteurs tournants.")

    # Attendre que le drone soit complètement posé au sol
   # while vehicle.armed:
      #  print(" -> En cours d'atterrissage... altitude actuelle :", vehicle.location.global_relative_frame.alt)
     #   time.sleep(1)
    #print("[Mission] Le drone a atterri et s'est désarmé.")

    # ÉTAPE 4 : Actionner le servomoteur 
    servo.angle = 90	# ouverture trappe
    print("Ouverture trappe")
    time.sleep(1)
    servo.angle = 0	# fermeture trappe
    print("fermeture trappe")

    # ÉTAPE 5 : Réarmement et Retour à la base (RTL)
#    print("[Mission] Fin de la procédure au sol. Préparation du retour...")
#    if not vehicle.armed:
#        print("Rearmement du drone en cours ...")
#        armer_drone(vehicle)
    altitude_retour = 0.75
    print(f"[Mission] Décollage automatique à {altitude_retour} mètres...")
    vehicle.simple_takeoff(altitude_retour)
        # Attendre que le drone ait atteint l'altitude avant d'envoyer l'ordre de déplacement
    while True:
        alt_actuelle = vehicle.location.global_relative_frame.alt
        print(f" -> Altitude actuelle : {alt_actuelle:.2f}m")
        if alt_actuelle >= altitude_retour * 0.95: # Arrivé à 95% de l'altitude cible
            print("[Mission] Altitude de décollage atteinte.")
            break
        time.sleep(1)

        # Envoi de l'ordre de retour vers les coordonnées de l'Étape 1
        print(f"[Mission] Retour manuel vers la base -> Lat: {point_depart.lat}, Lon: {point_depart.lon}")
        vehicle.simple_goto(point_depart)

        # Attendre que le drone soit revenu au point de départ
        while True:
            pos_actuelle = vehicle.location.global_relative_frame
            distance_retour = calculer_distance_metres(pos_actuelle, point_depart)
            print(f" -> Distance du retour restante : {distance_retour:.2f} mètres")
            
            if distance_retour <= 1.0:
                print("[Mission] Le drone est revenu au point de départ !")
                break
            time.sleep(1)
            
        # Atterrissage final à la base
        print("[Mission] Atterrissage final (Mode LAND)...")
        vehicle.mode = VehicleMode("LAND")
        timeout_atterrissage = 30 # Sécurité : 30 secondes max pour atterrir
        while vehicle.armed and timeout_atterrissage > 0:
            alt = vehicle.location.global_relative_frame.alt
            print(f"-> Descente finale... altitue . {alt:.2f}m")
            if alt <= 0.10:
                print("[Mission] Marge d'altitude finale atteinte, drone au sol")
                break
            time.sleep(1)
            timeout_atterrissage -= 1
            
        # force le désarmement
        if vehicle.armed:
            print("[Sécurité] Le drone est au sol mais ne s'est pas désarmé tout seul. Force du désarmement...")
            vehicle.mode = VehicleMode("GUIDED")
            while vehicle.mode.name != "GUIDED":
                time.sleep(0.2)
            vehicle.armed = False
            while vehicle.armed:
                time.sleep(0.5)
        print("[Mission] MISSION TERMINÉE AVEC SUCCÈS ! Drone posé et désarmé.")
        
    else:
        print("[ALERTE] Échec du réarmement au sol. Le drone est bloqué sur zone.")

