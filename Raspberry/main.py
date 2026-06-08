# main.py
import threading
import time
from mqtt_client import MqttGateway
from mavlink_client import connect_mavlink, deconnexion_mavlink, listen_mavlink

PORT = 1883
BROKER = "localhost"
TOPIC_SUB = "projet/drone/#"  # Le '#' permet de s'abonner à tous les sous-topics de projet/drone

# Variable globale pour stocker l'accès au drone depuis le main
vehicle = None

def traiter_message_mqtt(topic, payload):
    """Cette fonction est exécutée quand un message arrive de MQTT."""
    global vehicle
    print(f"📥 [MQTT Reçu] Topic: {topic} ➡️ Payload: {payload}")
    


def main():
    global vehicle
    print("=== DÉMARRAGE DE LA PASSERELLE DRONEKIT / MQTT ===")

    # 1. Initialisation MQTT
    passerelle_mqtt = MqttGateway(broker=BROKER, topic_sub=TOPIC_SUB)
    # Attribution du callback pour intercepter les messages MQTT reçus
    passerelle_mqtt.on_message_received_callback = traiter_message_mqtt
    passerelle_mqtt.connecter()
    
    # 2. Connexion physique au drone (MAVLink)
    try:
        vehicle = connect_mavlink()
    except Exception as e:
        print(f"❌ Impossible de se connecter au drone : {e}")
        passerelle_mqtt.arreter()
        return

    # 3. Création du Thread pour écouter le drone en arrière-plan
    stop_event = threading.Event()
    thread_mavlink = threading.Thread(
        target=listen_mavlink,
        args=(vehicle, passerelle_mqtt, stop_event),
        daemon=True
    )
    thread_mavlink.start()

    # 4. Boucle principale de surveillance
    try:
        while True:
            # Le main ne fait plus rien d'autre que maintenir le script en vie
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[Main] Arrêt du programme par l'utilisateur (Ctrl+C)...")
        
    finally:
        # Nettoyage ordonné à la fermeture
        print("[Main] Nettoyage des connexions...")
        stop_event.set()            # Arrête la boucle du thread MAVLink
        thread_mavlink.join(timeout=2)
        deconnexion_mavlink(vehicle) # Ferme la connexion DroneKit
        passerelle_mqtt.arreter()    # Ferme la connexion MQTT
        print("[Main] Tout est proprement arrêté.")

if __name__ == "__main__":
    main()
