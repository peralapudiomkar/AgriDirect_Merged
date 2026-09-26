let trackingEnabled = false;
let watchId = null;


// ==========================================
// START GPS TRACKING
// ==========================================

function startTracking(orderId) {

    if (!navigator.geolocation) {

        alert(
            "GPS is not supported by this browser."
        );

        return;
    }


    trackingEnabled = true;


    watchId = navigator.geolocation.watchPosition(

        function(position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;


            console.log(
                "GPS:",
                latitude,
                longitude
            );


            sendLocation(
                orderId,
                latitude,
                longitude
            );

        },

        function(error) {

            console.error(
                "GPS Error:",
                error
            );

            alert(
                "Please allow location permission."
            );

        },

        {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 10000
        }
    );
}


// ==========================================
// SEND LOCATION TO FLASK
// ==========================================

async function sendLocation(
    orderId,
    latitude,
    longitude
) {

    try {

        const response = await fetch(
            "/api/update-location",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    order_id: orderId,

                    lat: latitude,

                    lng: longitude

                })
            }
        );


        const data =
            await response.json();


        console.log(
            "Server:",
            data
        );

    } catch (error) {

        console.error(
            "Location update failed:",
            error
        );

    }
}


// ==========================================
// STOP GPS
// ==========================================

function stopTracking() {

    if (watchId !== null) {

        navigator.geolocation.clearWatch(
            watchId
        );

        watchId = null;

    }

    trackingEnabled = false;

    console.log(
        "GPS tracking stopped."
    );
}