package com.example.drone.mqtt

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken
import org.eclipse.paho.client.mqttv3.MqttCallback
import org.eclipse.paho.client.mqttv3.MqttClient
import org.eclipse.paho.client.mqttv3.MqttConnectOptions
import org.eclipse.paho.client.mqttv3.MqttMessage
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence
import java.util.UUID
import kotlin.concurrent.thread

class MqttManager {
    private var client: MqttClient? = null
    private val broker = "tcp://192.168.0.10:1883"
    private val clientId = "AndroidDrone_" + UUID.randomUUID().toString().take(5)

    // CORRECTION : On stocke les écouteurs associés à chaque topic distinct
    private val topicCallbacks = HashMap<String, (String) -> Unit>()

    fun connect(onConnected: () -> Unit, onError: (String) -> Unit) {
        thread {
            try {
                client = MqttClient(broker, clientId, MemoryPersistence())

                val options = MqttConnectOptions().apply {
                    isCleanSession = true
                    connectionTimeout = 10
                    mqttVersion = MqttConnectOptions.MQTT_VERSION_3_1_1
                }

                // CORRECTION : On configure le routeur de messages global UNE SEULE FOIS ici
                client?.setCallback(object : MqttCallback {
                    override fun connectionLost(cause: Throwable?) {
                        println("MQTT : Connexion perdue avec le broker : ${cause?.message}")
                    }

                    override fun messageArrived(topic: String?, message: MqttMessage?) {
                        if (topic != null && message != null) {
                            val payload = message.toString()
                            // On cherche l'écouteur spécifique à CE topic précis et on lui donne le message
                            topicCallbacks[topic]?.invoke(payload)
                        }
                    }

                    override fun deliveryComplete(token: IMqttDeliveryToken?) {}
                })

                println("MQTT : Tentative de connexion à $broker avec l'ID $clientId...")
                client?.connect(options)

                if (client?.isConnected == true) {
                    println("MQTT : Connexion réussie ! Autorisée par le Broker.")
                    onConnected()
                } else {
                    onError("Échec : Client non connecté après tentative")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                println("MQTT ERREUR INITIALE : ${e.localizedMessage}")
                onError(e.localizedMessage ?: "Erreur de connexion inconnue")
            }
        }
    }

    fun publish(topic: String, message: String) {
        try {
            if (client?.isConnected == true) {
                val mqttMessage = MqttMessage(message.toByteArray())
                mqttMessage.qos = 1
                client?.publish(topic, mqttMessage)
            } else {
                println("MQTT : Impossible de publier, le client n'est pas connecté.")
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun subscribe(topic: String, onMessageReceived: (String) -> Unit) {
        try {
            // 1. On enregistre le bloc de code dans notre dictionnaire pour ce topic
            topicCallbacks[topic] = onMessageReceived

            // 2. On demande au broker de nous envoyer les messages de ce topic
            if (client?.isConnected == true) {
                client?.subscribe(topic)
                println("MQTT : Abonnement validé pour le topic [$topic]")
            } else {
                println("MQTT : Impossible de s'abonner au topic [$topic], le client n'est pas connecté.")
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}