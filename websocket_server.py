from sys import argv
import json
from eventlet import wsgi, websocket, listen, wrap_ssl

# last assigned id number
clientIdCounter = 0

# list of connected clients with a socket and id for each
clientList = set() # [ (ws1,id1), (ws2,id2) ... ]

# default example src
sourceURL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

defaultVideoState = json.dumps({ "videoState": { "position": 0, "paused": True} })
lastKnownState = defaultVideoState

@websocket.WebSocketWSGI
def serve(ws):

    global clientIdCounter
    global lastKnownState
    global sourceURL
    ownId = -1 # not assigned yet

    while True:
    
        # wait for data from the client
        messageFromClient = ws.wait()

        # client disconnected
        if messageFromClient == None:

            clientList.remove((ws,ownId))
            print (f"ws - Client {ownId} left")

            for peer in [x[0] for x in clientList]:
                peerLeftNotice = {"peerLeft": {"id": ownId} }
                peer.send(json.dumps(peerLeftNotice))

            # if nobody is left reset id counter
            if len(clientList) == 0:
                clientIdCounter = 0

            break

        print (f"ws - Message from client {ownId}: {messageFromClient}")

        if messageFromClient == "Hello from new client": # new client connected
           
            # assign new client an id
            print (f"ws - Connection established to client {clientIdCounter}")
            helloBack = {"connected": {"assignedId": clientIdCounter}}
            ws.send(json.dumps(helloBack))

            # send the video link and state to the new client
            ws.send(json.dumps({"sourceURL" : sourceURL}))
            ws.send(lastKnownState)
            
            # send a list of already connected clients to the newcomer
            for peerId in [x[1] for x in clientList]:
                alreadyPeer = {"newPeer": {"id": peerId} }
                ws.send(json.dumps(alreadyPeer))
            
            # notify other clients of the new peer
            for peer in [x[0] for x in clientList]:
                newPeerNotice = {"newPeer": {"id": clientIdCounter} }
                peer.send(json.dumps(newPeerNotice))

            ownId = clientIdCounter
            clientIdCounter += 1
            clientList.add((ws,ownId))

        else: # pass the data to other clients

            if "newSource" in messageFromClient:

                print ("ws - Sending new video source to peers")
                messageJSON = json.loads(messageFromClient)
                sourceURL = messageJSON["newSource"]["url"]

            else:
            
                print (f"ws - Sending new video state to peers (originated from client {ownId})")

            for peer in [x[0] for x in clientList]:
                if peer is not ws:
                    peer.send(messageFromClient)

            lastKnownState = messageFromClient

if __name__ == '__main__':

    # websocket server
    # wait for connections in a loop
    while True:
    
        if len(argv) > 1 and argv[1] == "--no-ssl":
    
            wsgi.server(listen(('', 8001)), serve)
    
        else:
    
            # certificate files for wss
            certDirs = open("cert_dirs.txt", "r").read()
            # { "certFile" : "/path/to/cert", "keyFile" : "/path/to/key" }

            certFile = json.loads(certDirs)["certFile"]
            keyfile = json.loads(certDirs)["keyFile"]

            print ("Cert file: " + certFile)
            print ("Key file: " + keyfile)
            
            wsgi.server( wrap_ssl(  listen(('', 8001)),
                                    certfile= certFile,
                                    keyfile= keyfile,
                                    server_side=True ) ,serve)

