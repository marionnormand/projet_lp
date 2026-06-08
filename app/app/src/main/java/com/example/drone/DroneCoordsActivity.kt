package com.example.drone

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.example.drone.mqtt.MqttManager
import com.google.android.material.snackbar.Snackbar

class DroneCoordsActivity : AppCompatActivity() {

    private val mqttManager = MqttManager()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_drone_coords)

        val coordonnees = findViewById<EditText>(R.id.editTextCoords)
        val rootView = findViewById<View>(android.R.id.content)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }
        mqttManager.connect(
            onConnected = {
                runOnUiThread {
                    Snackbar.make(rootView, "Connecté au Broker Raspberry !", Snackbar.LENGTH_SHORT).show()
                }
            },
            onError = { erreur ->
                runOnUiThread {
                    // C'est ici qu'on va voir la vraie cause (ex: "MqttException: Malformed IPv4 address" ou "Connection timed out")
                    Snackbar.make(rootView, "Erreur MQTT : $erreur", Snackbar.LENGTH_INDEFINITE)
                        .setAction("Fermer") {}
                        .show()
                }
            }
        )

        findViewById<Button>(R.id.btnBack).setOnClickListener {
            finish()
        }

        findViewById<Button>(R.id.btnSend).setOnClickListener {
            val inputText = coordonnees.text.toString()

            if (inputText.isNotEmpty()) {
                mqttManager.publish("projet/drone", inputText)

                Snackbar.make(rootView, "Coordonnées envoyées : $inputText", Snackbar.LENGTH_LONG).show()
            } else {
                Snackbar.make(rootView, "Champ de texte vide", Snackbar.LENGTH_LONG).show()
            }
        }
    }
}