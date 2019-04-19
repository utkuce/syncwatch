var url = new URL(window.location.href);

var roomId;
if (roomId = url.searchParams.get("r")) {

    document.getElementById("room_link").innerHTML = window.location + ' <i class="far fa-copy"></i>';

} else {

    // if there is no room in url create one
    roomId = makeId(5);
    url.searchParams.append("r", roomId);
    window.location.replace(url);
}

log("Joining room " + roomId);

// client id given by server, -1 if not assigned
var client_id = -1;

// set video source
var vid = document.getElementById("video1");

// set inital text
setText();

// initialize websockets
var ws;

if ("WebSocket" in window) { // if the browser is supported

    // connect to websocket
    var prefix = "wss"
    var address = window.location.hostname;
    var port = "8001";

    // non ssl for local development
    prefix = address === "localhost" ? "ws" : prefix;
    prefix = address.startsWith("192.168.") ? "ws" : prefix;
    prefix = address.startsWith("172.16.") ? "ws" : prefix;
    prefix = address.startsWith("10.") ? "ws" : prefix;

    ws = new WebSocket(prefix + "://" + address + ":" + port);
    var ws_text = document.getElementById("ws_text");

    ws.onopen = function (event) {

        ws_text.innerHTML = "Websocket connected"
        log("Connected to websocket server");
    };

    ws.onclose = function (event) {
        ws_text.innerHTML = "<span class=error>Websocket disconnected</span>"
    };

} else {

    // The browser doesn't support WebSocket
    alert("WebSocket NOT supported by your Browser!");
}

function sendName(username) {

    log("Sending own name " + username + " to peers");
    ws.send(JSON.stringify({"peerName": {"name": username, "peerId": client_id}}));
}

function getCookie(cname) {

    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }

    return "";
}

function setText() {

    document.getElementById("video_state").innerHTML = 
        "Seconds: " + Math.floor(vid.currentTime) +
        ", Paused: " + vid.paused +
        ", Ready state: " + vid.readyState;
        //"<br>Seeking: " + vid.seeking;
    //", Can play through: " + vid.canplaythrough;

    document.getElementById("client_id").innerHTML = "Client ID: " + client_id;
}

function hideLog() {
    document.getElementById("logbox").style.display = "none";
}

function log(text) {

    console.log(text);
    document.getElementById("logs").innerHTML += "<br>" + text;
}

function makeId(length) {
    return Math.random().toString(36).substring(length);
  }