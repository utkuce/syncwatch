

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
      document.getElementById("watch_button").click();
    }
}); 

/*
addEventListener("keyup", function(event) {    
    
    // "K" key
    if (event.keyCode === 75) {
        vid.paused ? vid.play() : vid.pause();
    }
}); 
*/

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

// username
var alreadyEditing = false;
function editUsername() {

    if (!alreadyEditing) {

        var usernameInput = document.createElement("input");
        usernameInput.setAttribute("id", "username_input");
        usernameInput.setAttribute("placeholder", "username");
    
        var usernameSetButton = document.createElement("button");
        usernameSetButton.innerHTML = "Set <i class='fas fa-check'></i>";
        usernameSetButton.setAttribute("id", "username_set");
        usernameSetButton.setAttribute("onclick", "setUsername()");

        usernameInput.addEventListener("keyup", function(event) {    
            // Number 13 is the "Enter" key on the keyboard
            if (event.keyCode === 13) {
                setUsername();
            }
        }); 
    
        var usernameArea = document.getElementById("username_area");
        usernameArea.appendChild(usernameInput);
        usernameArea.appendChild(usernameSetButton);

        usernameInput.focus();
    }

    alreadyEditing = true;
}

function setUsername() {
    
    var username = document.getElementById("username_input").value;
    
    if (username !== "") {

        document.getElementById("username").innerHTML = "Connected as <u>" + username + "</u>";
        document.getElementById("figure" + client_id).getElementsByTagName("figcaption")[0].innerHTML = username;
        document.cookie = "username=" + username;

        sendName(username);
    }

    document.getElementById("username_input").remove();
    document.getElementById("username_set").remove();

    alreadyEditing = false;
}

function copyRoomLink() {

    navigator.clipboard.writeText(url).then(function() {
        
        /* clipboard successfully set */
        log ("Room link copied to clipboard");
      
    }, function() {
        
        // clipboard write failed
        log ("Failed to the copy room link to clipboard");    
        document.getElementById("copy_warning").innerHTML = 
            "<span class=warning>WARNING:</span> Have no permission to write to clipboard"
    });

}

function newRoom() {

    window.location = window.location.href.split("?")[0];
}