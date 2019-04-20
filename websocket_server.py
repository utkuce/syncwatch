import ssl
import json
import asyncio
import websockets

from sys import argv # for --no-ssl
from time import gmtime, strftime # for log timestamps
import secrets # for random room id

def log(message):
    time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    print(f"WS - {time} - {message}")

roomsList = dict()

class Room: 

    def __init__(self, id):
       
        self.id = id

        # last assigned id number
        self.clientIdCounter = 0

        # list of connected clients with a socket and id for each
        self.clientList = set() # [ (ws1,id1), (ws2,id2) ... ]
        self.clientNames = dict()

        # default example source
        self.sourceURL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

        self.defaultVideoState = json.dumps({ "videoState": { "position": 0, "paused": True} })
        self.lastKnownState = self.defaultVideoState


# everything in the handler function is the bidirectional 
# communication of a single client with the ws server
async def handler(ws, path):

    clientId = -1 # not assigned yet
    clientRoom = None

    ### NEW CONNECTION

    # wait until client requests room
    while clientRoom is None:
        firstMessage = await ws.recv()
        if "roomId" in firstMessage:
            
            roomId = json.loads(firstMessage)["roomId"]
            log (f"Room id received {roomId}")

            if roomId == "request":
                # create new room
                
                while True:
                    roomId = secrets.token_hex(3)
                    # make sure the random id doesnt already exist
                    if roomId not in roomsList:
                        break

                log(f"Creating new room: {roomId}")
                roomsList[roomId] = Room(id=roomId)
                await ws.send(json.dumps({"roomId" : roomId}))

            elif roomId not in roomsList:
                # client requested nonexistent room
                await ws.send(json.dumps({"error": "no_room"}))
                continue

            # add client to room
            clientRoom = roomsList[roomId]

    # assign new client an id
    log(f"Connection established to client {clientRoom.clientIdCounter} (Room: {clientRoom.id})")
    welcomeMessage = {"connected": {"assignedId": clientRoom.clientIdCounter}}
    await ws.send(json.dumps(welcomeMessage))

    # send the video link and state to the new client
    log("Sending video source to new client")
    await ws.send(json.dumps({"sourceURL" : clientRoom.sourceURL}))
    log(f"Sending video state to new client {clientRoom.lastKnownState}")    
    await ws.send(clientRoom.lastKnownState)
            
    # send a list of already connected clients to the newcomer
    if (len(clientRoom.clientList) is not 0):
        log(f"Sending a list of clients to new client ({clientRoom.clientNames})")    
        for peerId in [x[1] for x in clientRoom.clientList]:
            alreadyPeer = {"newPeer": {"id": peerId, "name": clientRoom.clientNames[peerId]} }
            await ws.send(json.dumps(alreadyPeer))

    # notify other clients of the new peer
    for peer in [x[0] for x in clientRoom.clientList]:
        newPeerNotice = {"newPeer": {"id": clientRoom.clientIdCounter} }
        await peer.send(json.dumps(newPeerNotice))

    # add new client to the list
    clientId = clientRoom.clientIdCounter
    clientRoom.clientIdCounter += 1
    clientRoom.clientList.add((ws,clientId))
    
    # new client is referred to as a guest with client id
    # until it sends its username
    clientRoom.clientNames[clientId] = "Guest " + str(clientId)

    try:

        ### MESSAGING

        while True:

            messageFromClient = await ws.recv()

            log(f"Message from client {clientId}: {messageFromClient}")

            if "newSource" in messageFromClient:
            # client changed video source, forward info to peers

                messageJSON = json.loads(messageFromClient)
                clientRoom.sourceURL = messageJSON["newSource"]["url"]

            if "peerName" in messageFromClient:
            # client changed their username, forward info to peers

                messageJSON = json.loads(messageFromClient)
                name = messageJSON["peerName"]["name"]
                peerId = messageJSON["peerName"]["peerId"]

                # update client with the new name
                log(f"Saving the name \"{name}\" for client {clientId}")
                clientRoom.clientNames[clientId] = name

            for peer in [x[0] for x in clientRoom.clientList]:
                if peer is not ws:
                    await peer.send(messageFromClient)

            # client changed video state, forward info to peers
            if "videoState" in messageFromClient:
                clientRoom.lastKnownState = messageFromClient

    except websockets.exceptions.ConnectionClosed:

        log(f"Connection to Client {clientId} is closed")

    finally:

        # END OF CONNECTION
    
        log(f"Removing Client {clientId} ({clientRoom.clientNames[clientId]}) from list")
        clientRoom.clientList.remove((ws,clientId))
        del clientRoom.clientNames[clientId]    

        for peer in [x[0] for x in clientRoom.clientList]:
            peerLeftNotice = {"peerLeft": {"id": clientId} }
            await peer.send(json.dumps(peerLeftNotice))

        # if nobody is left reset id counter
        if len(clientRoom.clientList) == 0:
            log("All clients left, resetting counter")
            clientRoom.clientIdCounter = 0
            clientRoom.clientNames.clear()


if __name__ == '__main__':

    log("Starting websocket server")

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