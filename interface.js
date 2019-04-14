// set video source
var vid = document.getElementById("video1");

// set inital text
setText();

function addClientFigure(clientNumber) {
  
    var figure = document.createElement("figure");
    figure.setAttribute("id", "figure" + clientNumber);
    
    var avatar = document.createElement("img");
    avatar.setAttribute("src", "avatars/avatar" + Math.floor((Math.random() * 28)) + ".svg");
    figure.setAttribute("width", "50px");
       
    var figcaption = document.createElement("figcaption");
    figcaption.innerHTML = "Guest " + clientNumber;
    figcaption.setAttribute("width", "50px");
    
    figure.appendChild(avatar);
    figure.appendChild(figcaption);
    
    document.getElementById("avatars").appendChild(figure);
}

function removeClientFigure(clientNumber) {
    log ("Removing avatar " + "figure" + clientNumber);
    document.getElementById("figure" + clientNumber).remove();
}

var urlBox = document.getElementById("url");

urlBox.addEventListener("keyup", function(event) {    
    // Number 13 is the "Enter" key on the keyboard
    if (event.keyCode === 13) {
      document.getElementById("watchButton").click();
    }
}); 

addEventListener("keyup", function(event) {    
    
    // "K" key
    if (event.keyCode === 75) {
        vid.paused ? vid.play() : vid.pause();
    }
}); 

function newSource() {

    if (urlBox.value !== "") {
    
        var newSource = JSON.stringify({ "newSource": { "url": urlBox.value} });

        log ("Loading new video from source: " + urlBox.value);
        vid.setAttribute("src", urlBox.value);
    
        log("Sending data: " + newSource)
        ws.send(newSource);
    
        urlBox.value = "";
    }
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