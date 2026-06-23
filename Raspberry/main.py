# main.py
import threading
import time
from mqtt_client import MqttGateway
from mavlink_client import connect_mavlink, deconnexion_mavlink, listen_mavlink, send_mavlink, executer_mission_livraison

PORT = 1883
BROKER = "localhost"
TOPIC_SUB = "projet/drone/#" 

vehicle = None

def traiter_message_mqtt(topic, payload):
    global vehicle
    print(f"[MQTT Reçu] Topic: {topic} --> Payload: {payload}")
    
    if topic == "projet/drone":
    	if vehicle is None: 
    		print("[MQTT] Erreur : Le drone n'est pas connecté") 
    		return
    	try: 
    		coords = payload.split(",")
    		latitude = float(coords[0])
    		longitude = float(coords[1])
    		print(f"A ENVOYER AU DRONE : LAT: {latitude}, LON: {longitude}")
    		# send_mavlink(vehicle, latitude, longitude, 5) # 5 metres de haut 
    		thread_mission = threading.Thread(target=executer_mission_livraison, args=(vehicle, lat, lon, 2))
    		thread_mission.start()
    	except (ValueError, IndexError) as e: 
    		print(f"[MQTT] Erreur de formatage du payload ('{payload}') : {e}")
    


def main():
    global vehicle
    print("DÉMARRAGE DE LA PASSERELLE DRONEKIT / MQTT")

    passerelle_mqtt = MqttGateway(broker=BROKER, topic_sub=TOPIC_SUB)
    passerelle_mqtt.on_message_received_callback = traiter_message_mqtt
    passerelle_mqtt.connecter()
    
    try:
        vehicle = connect_mavlink()
    except Exception as e:
        print(f"Impossible de se connecter au drone : {e}")
        passerelle_mqtt.arreter()
        return

    stop_event = threading.Event()
    thread_mavlink = threading.Thread(
        target=listen_mavlink,
        args=(vehicle, passerelle_mqtt, stop_event),
        daemon=True
    )
    thread_mavlink.start()

    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[Main] Arrêt du programme par l'utilisateur")
        
    finally:
        print("[Main] Nettoyage des connexions...")
        stop_event.set()
        thread_mavlink.join(timeout=2)
        deconnexion_mavlink(vehicle)
        passerelle_mqtt.arreter()
        print("[Main] Tout est proprement arrêté.")

if __name__ == "__main__":
    main()
