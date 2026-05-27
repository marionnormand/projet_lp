package com.example.drone.mqtt

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken
import org.eclipse.paho.client.mqttv3.MqttCallback
import org.eclipse.paho.client.mqttv3.MqttClient
import org.eclipse.paho.client.mqttv3.MqttConnectOptions
import org.eclipse.paho.client.mqttv3.MqttMessage
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence
import kotlin.concurrent.thread

class MqttManager {
    private var client: MqttClient? = null
    private val broker = "tcp://broker.hivemq.com:1883" // Ton broker
    private val clientId = "AndroidDrone_${System.currentTimeMillis()}"

    fun connect(onConnected: () -> Unit) {
        // Important : La connexion doit se faire dans un Thread séparé
        // pour ne pas bloquer l'interface Android
        thread {
            try {
                client = MqttClient(broker, clientId, MemoryPersistence())
                val options = MqttConnectOptions().apply {
                    isCleanSession = true
                    connectionTimeout = 10
                }

                client?.connect(options)

                if (client?.isConnected == true) {
                    onConnected()
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun publish(topic: String, message: String) {
        try {
            val mqttMessage = MqttMessage(message.toByteArray())
            mqttMessage.qos = 1
            client?.publish(topic, mqttMessage)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun subscribe(topic: String, onMessageReceived: (String) -> Unit) {
        client?.setCallback(object : MqttCallback {
            override fun connectionLost(cause: Throwable?) {
                // Gérer la perte de connexion si besoin
            }

            override fun messageArrived(topic: String?, message: MqttMessage?) {
                // On renvoie le contenu du message à l'activité
                onMessageReceived(message.toString())
            }

            override fun deliveryComplete(token: IMqttDeliveryToken?) {}
        })

        try {
            client?.subscribe(topic)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}