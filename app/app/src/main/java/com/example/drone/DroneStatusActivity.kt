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

    private lateinit var map: MapView
    private var droneMarker: Marker? = null
    private val mqttManager = MqttManager()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Configuration.getInstance().load(this, PreferenceManager.getDefaultSharedPreferences(this))
        Configuration.getInstance().userAgentValue = packageName

        setContentView(R.layout.activity_drone_status)

        map = findViewById(R.id.mapView)
        map.setTileSource(TileSourceFactory.MAPNIK)
        map.setMultiTouchControls(true)

        val rootView = findViewById<View>(android.R.id.content)
        val tvBatterie = findViewById<TextView>(R.id.tvBatterie)
        val tvTrajet = findViewById<TextView>(R.id.tvTrajet)

        val mapController = map.controller
        mapController.setZoom(17.0) // Zoom un peu plus serré pour voir le drone bouger
        val startPoint = GeoPoint(48.8566, 2.3522) // Paris par défaut
        mapController.setCenter(startPoint)

        mqttManager.connect(
            onConnected = {
                runOnUiThread {
                    Snackbar.make(rootView, "Connecté au Drone !", Snackbar.LENGTH_SHORT).show()
                }

                mqttManager.subscribe("projet/drone/map") { message1 ->
                    runOnUiThread {
                        updateDroneLocation(message1)
                    }
                }

                mqttManager.subscribe("projet/drone/batterie") { message2 ->
                    runOnUiThread {
                        tvBatterie.text = "Batterie : $message2 V"
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

    private fun updateDroneLocation(coordsString: String) {
        try {
            val parts = coordsString.split(",")
            if (parts.size == 2) {
                val lat = parts[0].toDouble()
                val lng = parts[1].toDouble()
                val dronePos = GeoPoint(lat, lng)

                if (droneMarker == null) {
                    droneMarker = Marker(map)
                    droneMarker?.title = "Drone"
                    map.overlays.add(droneMarker)
                }

                droneMarker?.position = dronePos
                map.controller.animateTo(dronePos)
                map.invalidate() // Rafraîchir la carte
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun onResume() {
        super.onResume()
        map.onResume()
    }

    override fun onPause() {
        super.onPause()
        map.onPause()
    }
}