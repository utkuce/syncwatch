from sys import argv
import ssl
import json
import asyncio
import websockets

# last assigned id number
clientIdCounter = 0

# list of connected clients with a socket and id for each
clientList = set() # [ (ws1,id1), (ws2,id2) ... ]

# default example source
sourceURL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

defaultVideoState = json.dumps({ "videoState": { "position": 0, "paused": True} })
lastKnownState = defaultVideoState

async def handler(ws, path):

    global clientIdCounter
    global lastKnownState
    global sourceURL
    clientId = -1 # not assigned yet
    
    ### NEW CONNECTION

    # assign new client an id
    print (f"WS - Connection established to client {clientIdCounter}")
    welcomeMessage = {"connected": {"assignedId": clientIdCounter}}
    await ws.send(json.dumps(welcomeMessage))

    # send the video link and state to the new client
    print ("WS - Sending video source to new client")
    await ws.send(json.dumps({"sourceURL" : sourceURL}))
    print ("WS - Sending video state to new client")    
    await ws.send(lastKnownState)
            
    # send a list of already connected clients to the newcomer
    for peerId in [x[1] for x in clientList]:
        alreadyPeer = {"newPeer": {"id": peerId} }
        await ws.send(json.dumps(alreadyPeer))
            
    # notify other clients of the new peer
    for peer in [x[0] for x in clientList]:
        newPeerNotice = {"newPeer": {"id": clientIdCounter} }
        await peer.send(json.dumps(newPeerNotice))

    clientId = clientIdCounter
    clientIdCounter += 1
    clientList.add((ws,clientId))

    try:

        ### MESSAGING

        while True:

            messageFromClient = await ws.recv()

            print (f"WS - Message from client {clientId}: {messageFromClient}")

            if "newSource" in messageFromClient:

                messageJSON = json.loads(messageFromClient)
                sourceURL = messageJSON["newSource"]["url"]

            for peer in [x[0] for x in clientList]:
                if peer is not ws:
                    await peer.send(messageFromClient)

            lastKnownState = messageFromClient

    except websockets.exceptions.ConnectionClosed:

        print (f"WS - Connection to Client {clientId} is closed")

    finally:

        # END OF CONNECTION
        
        clientList.remove((ws,clientId))
        print (f"WS - Client {clientId} removed from list")

        for peer in [x[0] for x in clientList]:
            peerLeftNotice = {"peerLeft": {"id": clientId} }
            await peer.send(json.dumps(peerLeftNotice))

        # if nobody is left reset id counter
        if len(clientList) == 0:
            print ("WS - All clients left, resetting counter")
            clientIdCounter = 0


if __name__ == '__main__':

    print ("WS - Starting websocket server")

    if len(argv) > 1 and argv[1] == "--no-ssl":
    
        start_server = websockets.serve(handler, '', 8001)
    
    else:

        # certificate files for wss
        certDirs = open("cert_dirs.txt", "r").read()
        # { "certFile" : "/path/to/cert", "keyFile" : "/path/to/key" }
        certFile = json.loads(certDirs)["certFile"]
        keyfile = json.loads(certDirs)["keyFile"]

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certFile, keyfile)

        start_server = websockets.serve(handler, '', 8001, ssl=ssl_context)        
    

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()