# mqtt_client.py
import paho.mqtt.client as mqtt

PORT = 1883
BROKER = "localhost"
TOPIC = "projet/drone"

class MqttGateway:
    def __init__(self, broker=BROKER, port=PORT, topic_sub=TOPIC):
        self.broker = broker
        self.port = port
        self.topic_sub = topic_sub
        
        self.on_message_received_callback = None
        
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connecté au broker MQTT")
            self.client.subscribe(self.topic_sub)
            print(f"Client connecté au topic : {self.topic_sub}")
        else:
            print(f"Échec de connexion mqtt (code {rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            print(f"Message reçu de l'application : {payload}")
            
            if self.on_message_received_callback:
                self.on_message_received_callback(msg.topic, payload)
        
        except Exception as e:
            print(f"Erreur lors de la lecture du message : {e}") 
            
    def connecter(self):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()
        print("MQTT à l'écoute...")
        
    def publier(self, topic, message):
        self.client.publish(topic, message)
        
    def arreter(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT déconnecté")
