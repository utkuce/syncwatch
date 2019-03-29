var client_id = -1;
var receivedVideoState = "";

// set video source
var vid = document.getElementById("video1");

// get source from url
var url = new URL(window.location.href);
var video_src = url.searchParams.get("v"); // https://www.w3schools.com/html/mov_bbb.mp4
var otaku_link = url.searchParams.get("o");

var source = document.createElement('source');


if (otaku_link != null) {

    mylog("Otaku link: " + otaku_link);
    printHTML(otaku_link);

} else if (video_src != null) {

    // video source from url
    mylog("URL source: " + video_src);
    source.setAttribute('src', video_src);

} else {

    // if no source in url
    mylog("No video source in url, will request from server");
}

// add source to the video object
vid.appendChild(source);

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
    var ws = new WebSocket("ws://" + window.location.hostname + ":8001/");
    var ws_text = document.getElementById("ws_text");

    ws.onopen = function (event) {

        ws_text.innerHTML = "Websocket connected"
        mylog("Connecting to server");
        ws.send("Hello from new client");
    };

    ws.onclose = function (event) {
        ws_text.innerHTML = "Websocket disconnected"
    };

    ws.onmessage = function (event) {

        mylog("Data received: " + event.data);
        var message = JSON.parse(event.data);
        var messageType = Object.keys(message)[0];
        
        switch (messageType) {

            case "connected":

                // {"connected": {"assignedId": client_id}}

                client_id = message["connected"]["assignedId"];
                mylog("Client id set to " + client_id);
                setText();
                
                break;
            
            case "newPeer":
            
                // {"newPeer": {"id": peerId}}

                var peerId = message["newPeer"]["id"];
                mylog("New peer joined with id " + peerId);
            
                break;
    
            case "videoState":

                // { "videoState": { "position": vid.currentTime, "paused": vid.paused } }
                
                receivedVideoState = event.data;

                message["videoState"]["paused"] ? vid.pause() : vid.play();
                vid.currentTime = parseFloat(message["videoState"]["position"]);

                break;

            case "sourceURL":

                // { "sourceURL": url}
                vid.setAttribute("src", message["sourceURL"]);
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

    var vp = getVideoState();

    if (vp !== receivedVideoState) { // don't send the received data back

        mylog("Sending data: " + vp);
        ws.send(vp);    
    }

    setText();
}

function mylog(text) {

    console.log(text);
    document.getElementById("logs").innerHTML += "<br>" + text;
}

function makeHttpObject() {
    
    try {return new XMLHttpRequest();}
    catch (error) {}
    try {return new ActiveXObject("Msxml2.XMLHTTP");}
    catch (error) {}
    try {return new ActiveXObject("Microsoft.XMLHTTP");}
    catch (error) {}
  
    throw new Error("Could not create HTTP request object.");
  }

function printHTML(url) {

    var request = makeHttpObject();
    request.open("GET", url, true);
    request.send(null);
    request.onreadystatechange = function() {
        if (request.readyState == 4) {
            
            console.log("HTML:" + request.responseText);
        }
    };
}