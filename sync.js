var receivedState = "";
var stopSending = false;

// add event listeners for the video state sync and text updates
var syncEvents = ["seeked", "play", "pause"]
var textEvents = ["timeupdate", "seeking", "readyState", "canplaythrough"]

syncEvents.forEach(function (entry) {
    vid.addEventListener(entry, sendSync);
});

textEvents.forEach(function (entry) {
    vid.addEventListener(entry, setText);
});


// when message received
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
            addClientFigure(client_id);

            var username = getCookie("username");
            if (username === "") {

                log("No username set, using default");
                document.getElementById("username").innerHTML = "Connected as Guest " + client_id;
            
            } else {

                
                log("Username set: " + username);
                document.getElementById("username").innerHTML = "Connected as " + username;
                document.getElementById("figure" + client_id).getElementsByTagName("figcaption")[0].innerHTML = username;
                sendName(username);
            } 

            break;

        case "newPeer":

            // {"newPeer": {"id": peerId}}

            var peerId = message["newPeer"]["id"];
            log("New peer joined with id " + peerId);

            addClientFigure(peerId);


            break;

        case "peerLeft":
            
            // {"peerLeft: {"id": peerId}
            
            var peerId = message["peerLeft"]["id"];
            log("Peer " + peerId + " left");

            removeClientFigure(peerId);

            break;

        case "videoState":

            // { "videoState": { "position": vid.currentTime, "paused": vid.paused } }

            receivedState = event.data;

            // unless it's the start of a video and event will be fired 
            //and we dont want to send it back and cause a loop
            stopSending = true;

            if (message["videoState"]["paused"]) {
            
                vid.pause();
            
            } else {
                
                vid.play().catch(error => {
                    if (error.name === "NotAllowedError") {
                        document.getElementById("mute_warning").innerHTML = 
                            "<span class=warning>WARNING:</span> Have no permission to autoplay sound, muted video"
                        vid.muted = true;
                        vid.play();
                    }  
                });                    
            }
            
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

        case "peerName":

            // {"peerName" : {"name": username, "peerId": id}}
            var peerId = message["peerName"]["peerId"];
            var peerName = message["peerName"]["name"];
            log("peer id " + peerId + " is called " + peerName);
            document.getElementById("figure" + peerId).getElementsByTagName("figcaption")[0].innerHTML = peerName;
    }
};

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