package com.example.drone

import android.os.Bundle
import androidx.preference.PreferenceManager // Changement ici
import android.view.View
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import com.example.drone.mqtt.MqttManager
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

        // 1. IMPORTANT : Charger la config OSM
        Configuration.getInstance().load(this, PreferenceManager.getDefaultSharedPreferences(this))
        // Ajouter un User Agent pour éviter d'être bloqué par les serveurs OSM
        Configuration.getInstance().userAgentValue = packageName

        setContentView(R.layout.activity_drone_status)

        // 2. Initialiser la Map
        map = findViewById(R.id.mapView)
        map.setTileSource(TileSourceFactory.MAPNIK)
        map.setMultiTouchControls(true)

        val mapController = map.controller
        mapController.setZoom(15.0)
        val startPoint = GeoPoint(48.8566, 2.3522) // Paris par défaut
        mapController.setCenter(startPoint)

        // 3. Bouton retour
        findViewById<Button>(R.id.btnBack).setOnClickListener {
            finish()
        }

        // 4. Connexion MQTT
        mqttManager.connect {
            mqttManager.subscribe("projet/drone/map") { message ->
                runOnUiThread {
                    updateDroneLocation(message)
                }
            }
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
                    // Suppression de l'import compose.foundation.layout.add qui créait l'erreur
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