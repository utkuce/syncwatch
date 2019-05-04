// webtorrent
var client = new WebTorrent()
var torrentProgress = document.getElementById("downloading");

function setTorrentSource(torrentId) {

    log ("Getting video source from magnet link");

    client.add(torrentId, function (torrent) {

        var file = torrent.files.find(function (file) {
            return file.name.endsWith('.mp4');
        });
    
        file.renderTo("video#video1");
        /*
      
        file.getBlobURL(function (err, url) {
          if (err) return log(err.message);
          log('File ready: ' + url);
          vid.setAttribute("src", url);
          vid.load();
        }); */
    
        var interval = setInterval(function () {
            torrentProgress.innerHTML = "Downloading: " + (torrent.progress * 100).toFixed(1) + "%";
        }, 1000);
    
        torrent.on("done", function () {
            torrentProgress.innerHTML = "File ready. (" + file.name + ")";
            clearInterval(interval);
        });
    })
}

var pc_config = {"iceServers": 
    [{url:'stun:stun.1.google.com:19302'},
     {url:'turn:numb.viagenie.ca',credential: 'muazkh', username: 'webrtc@live.com'}]};

pc = new RTCPeerConnection(pc_config);

function seedFile(fileSelector) {

    if ('files' in fileSelector && fileSelector.files.length != 0) {
        var path = fileSelector.files[0].name;
    }

    log ("Selected file: " + path);

    let client = new WebTorrent()
    client.seed(fileSelector.files[0], function (torrent) {
        log("Seeding file");
        log(torrent.magnetURI) // a buffer of the .torrent file
        // host it at the url you put after &xs=
    });
}