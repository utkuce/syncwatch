from sys import argv
import json
from eventlet import wsgi, websocket, listen, wrap_ssl

clientIdCounter = 0
clientList = set()

sourceURL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"

defaultVideoState = json.dumps({ "videoState": { "position": 0, "paused": True} })
lastKnownState = defaultVideoState

@websocket.WebSocketWSGI
def serve(ws):

    global clientIdCounter
    global lastKnownState
    global sourceURL
    ownId = -1

    while True:
    
        # wait for data from the client
        messageFromClient = ws.wait()

        # client disconnected
        if messageFromClient == None:

            clientList.remove(ws)
            print (f"ws - Client {ownId} left")

            for peer in clientList:
                newPeerNotice = {"peerLeft": {"id": clientIdCounter} }
                peer.send(json.dumps(newPeerNotice))

            break

        print (f"ws - Message from client {ownId}: {messageFromClient}")

        if messageFromClient == "Hello from new client": # new client connected
           
            # assign new client an id
            print (f"ws - Connection established to client {clientIdCounter}")
            helloBack = {"connected": {"assignedId": clientIdCounter}}
            ws.send(json.dumps(helloBack))
            '''
            # check if the source file changed
            newSource = open("url.txt", "r").read()

            if newSource != sourceURL:
                lastKnownState = defaultVideoState
                sourceURL = newSource
            '''
            # send the video link and state to the new client
            ws.send(json.dumps({"sourceURL" : sourceURL}))
            ws.send(lastKnownState)

            # notify other clients of the new peer
            for peer in clientList:
                newPeerNotice = {"newPeer": {"id": clientIdCounter} }
                peer.send(json.dumps(newPeerNotice))

            ownId = clientIdCounter
            clientIdCounter += 1
            clientList.add(ws)

        else: # pass the data to other clients

            if "newSource" in messageFromClient:

                print ("ws - Sending new video source to peers")
                messageJSON = json.loads(messageFromClient)
                sourceURL = messageJSON["newSource"]["url"]

            else:
            
                print (f"ws - Sending new video state to peers (originated from client {ownId})")

            for peer in clientList:
                if peer is not ws:
                    peer.send(messageFromClient)

            lastKnownState = messageFromClient

if __name__ == '__main__':

    # certificate files for wss
    certDirs = open("cert_dirs.txt", "r").read()
    certFile = json.loads(certDirs)["certFile"]
    keyfile = json.loads(certDirs)["keyFile"]

    print ("Cert file: " + certFile)
    print ("Key file: " + keyfile)

    # websocket server
    # wait for connections in a loop
    while True:
        if len(argv) > 1 and argv[1] == "--no-ssl":
            wsgi.server(listen(('', 8001)), serve)
        else:
            wsgi.server( wrap_ssl(  listen(('', 8001)),
                                    certfile= certFile,
                                    keyfile= keyfile,
                                    server_side=True ) ,serve)


