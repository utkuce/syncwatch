var client_id = -1;
var receivedState = "";
var stopSending = false;

// set video source
var vid = document.getElementById("video1");

// get source from url
var url = new URL(window.location.href);
var video_src = url.searchParams.get("v"); // https://www.w3schools.com/html/mov_bbb.mp4

if (video_src != null) {

    // video source from url
    log("URL source: " + video_src);
    vid.setAttribute('src', video_src);

} else {

    // if no source in url
    log("No video source in url, will request from server");
}

// info text under the video
setText(); // initial text

// add event listeners for the video state sync and text updates
var syncEvents = ["seeked", "play", "pause"]
var textEvents = ["timeupdate", "seeking", "readyState", "canplaythrough"]

syncEvents.forEach(function (entry) {
    vid.addEventListener(entry, sendSync);
});

textEvents.forEach(function (entry) {
    vid.addEventListener(entry, setText);
});

// websockets
if ("WebSocket" in window) { // if the browser is supported

    // connect to websocket
    var prefix = "wss"
    var address = window.location.hostname;
    var port = "8001";

    // non ssl for local development
    prefix = address === "localhost" ? "ws" : prefix;

    var ws = new WebSocket(prefix + "://" + address + ":" + port);
    var ws_text = document.getElementById("ws_text");

    ws.onopen = function (event) {

        ws_text.innerHTML = "Websocket connected"
        log("Connecting to server");
        ws.send("Hello from new client");
    };

    ws.onclose = function (event) {
        ws_text.innerHTML = "Websocket disconnected"
    };

    ws.onmessage = function (event) {

        log("Data received: " + event.data);
        var message = JSON.parse(event.data);
        var messageType = Object.keys(message)[0];

        switch (messageType) {

            case "connected":

                // {"connected": {"assignedId": client_id}}

                client_id = message["connected"]["assignedId"];
                log("Client id set to " + client_id);
                setText();

                break;

            case "newPeer":

                // {"newPeer": {"id": peerId}}

                var peerId = message["newPeer"]["id"];
                log("New peer joined with id " + peerId);

                break;

            case "peerLeft":
                
                // {"peerLeft: {"id": peerId}
                
                var peerId = message["peerLeft"]["id"];
                log("Peer " + peerId + " left");

            case "videoState":

                // { "videoState": { "position": vid.currentTime, "paused": vid.paused } }

                receivedState = event.data;

                // unless it's the start of a video and event will be fired 
                //and we dont want to send it back and cause a loop
                stopSending = true;

                message["videoState"]["paused"] ? vid.pause() : vid.play();
                vid.currentTime = parseFloat(message["videoState"]["position"]);

                if (message["videoState"]["paused"] &&
                    message["videoState"]["position"] === 0) {
                    stopSending = false;
                }

                break;

            case "sourceURL":

                // { "sourceURL": url}
                vid.setAttribute("src", message["sourceURL"]);
                
                break;

            case "newSource":
                
                // { "newSource" : {"url": url} }
                vid.setAttribute("src", message["newSource"]["url"])
                
                break;
            }
    };

} else {

    // The browser doesn't support WebSocket
    alert("WebSocket NOT supported by your Browser!");
}

function setText() {

    document.getElementById("video_state").innerHTML = "Seconds: " + Math.floor(vid.currentTime) +
        ", Paused: " + vid.paused +
        ", Ready state: " + vid.readyState +
        ", Seeking: " + vid.seeking;
    //", Can play through: " + vid.canplaythrough;

    document.getElementById("client_id").innerHTML = "Client ID: " + client_id;
}

function getVideoState() {
    return JSON.stringify({ "videoState": { "position": vid.currentTime, "paused": vid.paused } });
}

function sendSync() {

    var currentState = getVideoState();

    if (!stopSending && (currentState !== receivedState)) { // don't send the received data back

        log("Sending data: " + currentState);
        ws.send(currentState);

    } /* else {

        if (stopSending) {
        
            log("Event occured but not sending");
            log ("Current state: " + currentState);
            log("Received state: " + receivedState); 
        }
    
    } */

    // can start sending again if current state caught up with the last received state
    if (currentState === receivedState) {
        stopSending = false;
    }

    setText();
}

var urlBox = document.getElementById("url");

urlBox.addEventListener("keyup", function(event) {    
    // Number 13 is the "Enter" key on the keyboard
    if (event.keyCode === 13) {
      document.getElementById("watchButton").click();
    };
}); 

function newSource() {

    var newSource = JSON.stringify({ "newSource": { "url": urlBox.value} });

    log ("Loading new video from source: " + urlBox.value);
    vid.setAttribute("src", urlBox.value);

    log("Sending data: " + newSource)
    ws.send(newSource);

    urlBox.value = "";
}

function log(text) {

    console.log(text);
    document.getElementById("logs").innerHTML += "<br>" + text;
}