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
import org.osmdroid.config.Configuration
import org.osmdroid.events.MapEventsReceiver
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.MapEventsOverlay
import org.osmdroid.views.overlay.Marker
import java.io.File

class DroneCoordsActivity : AppCompatActivity() {

    private val mqttManager = MqttManager()
    private lateinit var mapView: MapView
    private var selectedMarker: Marker? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val ctx = applicationContext
        val prefs = androidx.preference.PreferenceManager.getDefaultSharedPreferences(ctx)
        Configuration.getInstance().load(ctx, prefs)

        Configuration.getInstance().userAgentValue = packageName

        val basePath = File(ctx.cacheDir, "osmdroid")
        Configuration.getInstance().osmdroidBasePath = basePath
        val tileCache = File(basePath, "tiles")
        Configuration.getInstance().osmdroidTileCache = tileCache

        enableEdgeToEdge()
        setContentView(R.layout.activity_drone_coords)

        val coordonnees = findViewById<EditText>(R.id.editTextCoords)
        val rootView = findViewById<View>(android.R.id.content)
        mapView = findViewById(R.id.mapView)

        // Configuration de la carte
        mapView.setMultiTouchControls(true)
        val mapController = mapView.controller
        mapController.setZoom(15.0)
        val startPoint = GeoPoint(48.8566, 2.3522) // Paris par défaut
        mapController.setCenter(startPoint)

        // Gestion du clic sur la Map
        val mapEventsReceiver = object : MapEventsReceiver {
            override fun singleTapConfirmedHelper(p: GeoPoint?): Boolean {
                p?.let { point ->
                    val coordsString = "${point.latitude},${point.longitude}"
                    coordonnees.setText(coordsString)

                    if (selectedMarker == null) {
                        selectedMarker = Marker(mapView)
                        selectedMarker?.title = "Position du drone"
                        mapView.overlays.add(selectedMarker)
                    }
                    selectedMarker?.position = point
                    selectedMarker?.showInfoWindow()

                    mapView.invalidate()
                }
                return true
            }

            override fun longPressHelper(p: GeoPoint?): Boolean {
                return false
            }
        }

        val mapEventsOverlay = MapEventsOverlay(mapEventsReceiver)
        mapView.overlays.add(mapEventsOverlay)

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

    override fun onResume() {
        super.onResume()
        mapView.onResume()
    }

    override fun onPause() {
        super.onPause()
        mapView.onPause()
    }
}