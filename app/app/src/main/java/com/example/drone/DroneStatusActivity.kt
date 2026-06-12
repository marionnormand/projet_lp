package com.example.drone

import android.os.Bundle
import androidx.preference.PreferenceManager // Changement ici
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.drone.mqtt.MqttManager
import com.google.android.material.snackbar.Snackbar
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

class DroneStatusActivity : AppCompatActivity() {

    private val mqttManager = MqttManager()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Configuration.getInstance().load(this, PreferenceManager.getDefaultSharedPreferences(this))

        setContentView(R.layout.activity_drone_status)


        val rootView = findViewById<View>(android.R.id.content)
        val tvBatterie = findViewById<TextView>(R.id.tvBatterie)
        val tvTrajet = findViewById<TextView>(R.id.tvTrajet)


        mqttManager.connect(
            onConnected = {
                runOnUiThread {
                    Snackbar.make(rootView, "Connecté au Drone !", Snackbar.LENGTH_SHORT).show()
                }

                mqttManager.subscribe("projet/drone/batterie") { message2 ->
                    runOnUiThread {
                        tvBatterie.text = "Batterie : $message2 %"
                    }
                }

                mqttManager.subscribe("projet/drone/trajet") { message3 ->
                    runOnUiThread {
                        tvTrajet.text = "En trajet : $message3"
                    }
                }
            },
            onError = { erreur ->
                runOnUiThread {
                    Snackbar.make(rootView, "Erreur de liaison : $erreur", Snackbar.LENGTH_INDEFINITE)
                        .setAction("Fermer") {}
                        .show()
                }
            }
        )

        findViewById<Button>(R.id.btnBack).setOnClickListener {
            finish()
        }
    }
}