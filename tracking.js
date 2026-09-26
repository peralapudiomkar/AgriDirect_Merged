let map;
let driverMarker;
let farmerMarker;
let buyerMarker;

let currentDriverLocation = null;


// Default map position - Andhra Pradesh
const defaultLocation = [16.3067, 80.4365];


// ================================
// INITIALIZE MAP
// ================================

function initializeMap() {

    map = L.map("map").setView(defaultLocation, 12);

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

}


// ================================
// LOAD ORDER GPS LOCATION
// ================================

async function loadOrderLocation() {

    try {

        document.getElementById("trackingMessage").innerText =
            "Getting latest GPS location...";

        const response = await fetch(
            `/api/order/${ORDER_ID}/location`
        );

        if (!response.ok) {
            throw new Error("Unable to get location");
        }

        const data = await response.json();

        if (!data.success) {

            document.getElementById("trackingMessage").innerText =
                data.message || "GPS location unavailable.";

            return;
        }


        // Driver location
        const driverLat = data.driver.lat;
        const driverLng = data.driver.lng;

        currentDriverLocation = [
            driverLat,
            driverLng
        ];


        // ================================
        // DRIVER MARKER
        // ================================

        if (!driverMarker) {

            driverMarker = L.marker(
                [driverLat, driverLng]
            ).addTo(map);

            driverMarker.bindPopup(
                "🚚 Transporter Location"
            );

        } else {

            driverMarker.setLatLng(
                [driverLat, driverLng]
            );

        }


        // ================================
        // FARMER LOCATION
        // ================================

        if (data.farmer) {

            const farmerLocation = [
                data.farmer.lat,
                data.farmer.lng
            ];

            if (!farmerMarker) {

                farmerMarker = L.marker(
                    farmerLocation
                ).addTo(map);

                farmerMarker.bindPopup(
                    "🌾 Farmer Location"
                );

            } else {

                farmerMarker.setLatLng(
                    farmerLocation
                );

            }

        }


        // ================================
        // BUYER LOCATION
        // ================================

        if (data.buyer) {

            const buyerLocation = [
                data.buyer.lat,
                data.buyer.lng
            ];

            if (!buyerMarker) {

                buyerMarker = L.marker(
                    buyerLocation
                ).addTo(map);

                buyerMarker.bindPopup(
                    "🏠 Buyer Location"
                );

            } else {

                buyerMarker.setLatLng(
                    buyerLocation
                );

            }

        }


        // ================================
        // STATUS
        // ================================

        if (data.status) {

            document.getElementById("orderStatus").innerText =
                data.status;

        }


        // ================================
        // LAST UPDATED
        // ================================

        document.getElementById("lastUpdate").innerText =
            new Date().toLocaleTimeString();


        document.getElementById("trackingMessage").innerText =
            "✅ GPS location updated successfully.";


        map.setView(
            [driverLat, driverLng],
            14
        );


    } catch (error) {

        console.error(error);

        document.getElementById("trackingMessage").innerText =
            "❌ Unable to connect to GPS tracking.";

    }

}


// ================================
// CENTER MAP ON TRANSPORTER
// ================================

function centerOnDriver() {

    if (!currentDriverLocation) {

        alert("Transporter location is not available yet.");

        return;
    }

    map.setView(
        currentDriverLocation,
        16
    );

    driverMarker.openPopup();

}


// ================================
// AUTO REFRESH
// ================================

setInterval(
    loadOrderLocation,
    10000
);


// ================================
// START
// ================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        initializeMap();

        loadOrderLocation();

    }
);