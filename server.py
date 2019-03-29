from subprocess import Popen
import json
from eventlet import wsgi, websocket, listen

clientIdCounter = 0
clientList = set()

lastSource = open("url.txt", "r").read()

defaultVideoState = json.dumps({ "videoState": { "position": 0, "paused": True} })
lastSentState = defaultVideoState

@websocket.WebSocketWSGI
def serve(ws):

    global clientIdCounter
    global lastSentState
    global lastSource
    ownId = -1

    while True:
    
        # wait for data from the client
        messageFromClient = ws.wait()

        # client disconnected
        if messageFromClient == None:
            clientList.remove(ws)
            print (f"Client {ownId} left")
            break

        print (f"Message from client {ownId}: {messageFromClient}")

        if messageFromClient == "Hello from new client": # new client connected
           
            # assign new client an id
            print (f"Connection established to client {clientIdCounter}")
            helloBack = {"connected": {"assignedId": clientIdCounter}}
            ws.send(json.dumps(helloBack))

            # check if the source file changed
            newSource = open("url.txt", "r").read()

            if newSource != lastSource:
                lastSentState = defaultVideoState
                lastSource = newSource

            # send the video link and state to the new client
            ws.send(json.dumps({"sourceURL" : lastSource}))
            ws.send(lastSentState)

            # notify other clients of the new peer
            for peer in clientList:
                newPeerNotice = {"newPeer": {"id": clientIdCounter} }
                peer.send(json.dumps(newPeerNotice))

            ownId = clientIdCounter
            clientIdCounter += 1
            clientList.add(ws)

        else: # pass the data to other clients

            for peer in clientList:
                if peer is not ws:
                    print (f"Sending new video state originated from client {ownId}")
                    peer.send(messageFromClient)

            lastSentState = messageFromClient

if __name__ == '__main__':

    # http server
    Popen(["python", "-m", "http.server", "8000"])

    # websocket server
    # wait for connections in a loop
    while True:
        wsgi.server(listen(('', 8001)), serve)