import websockets, ssl, asyncio, json # for messages
from sys import argv # for --no-ssl
from time import gmtime, strftime # for log timestamps
import secrets # for random room id
from random import randint # for random avatar number
import database as db # for storing data

def log(message):
    time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    print(f"WS - {time} - {message}")

sockets = dict()

async def arrangeRoom(ws):

    roomId = -1
    # wait until client requests room
    while roomId is -1:

        firstMessage = await ws.recv()
        if "roomId" in firstMessage:
            
            roomId = json.loads(firstMessage)["roomId"]
            log (f"Room id request received: {roomId}")

            if roomId == "request":
                roomId = -1
                # create new room
                
                while True:
                    roomId = secrets.token_hex(3)
                    # make sure the random id doesnt already exist
                    if not db.roomIdExists(roomId):
                        break
                    
                log(f"Creating new room: {roomId}")
                db.createRoom(roomId)
                sockets[roomId] = set() # [ (ws1,id1), (ws2,id2) ... ]
                await ws.send(json.dumps({"roomId" : roomId}))

            elif not db.roomIdExists(roomId):
                roomId = -1
                # client requested nonexistent room, send error message
                await ws.send(json.dumps({"error": "no_room"}))
                # and wait for a valid request
                continue

    return roomId       

async def setupNewClient(roomId, ws):

    clientId = db.getNewClientId(roomId)
    log(f"Connection established to client {clientId} (Room: {roomId})")
    randomAvatar = randint(0, 27)
    log(f"Selected avatar {randomAvatar} for the new client")

    # add new client to database
    db.addUser(clientId, roomId, randomAvatar)
    # add user to room
    db.cursor.execute("UPDATE users SET room=? WHERE id=?", (roomId, clientId))

    welcomeMessage = {"connected": {"assignedId": clientId, "assignedAvatar": randomAvatar}}
    await ws.send(json.dumps(welcomeMessage))
    
    return clientId, randomAvatar

async def sendCurrentVideo(roomId, ws):

    log("Sending video source to new client")
    sourceURL, videoState = db.getCurrentVideo(roomId)
    await ws.send(json.dumps({"sourceURL" : sourceURL}))
    log(f"Sending video state to new client {videoState}")    
    await ws.send(videoState)

async def sendUsers(ownId, roomId, ws):
 
    usersInRoom = db.getUsers(roomId)
    if (len(usersInRoom) is not 0): # if the room is not empty
        log(f"Sending a list of clients to new client")    
        for user in usersInRoom : # user is (clientId, roomId, name, avatar, ws)
            if user[0] is not ownId: # if the user is not itself
                userAttributes = {"newPeer": {"id": user[0], "name": user[2], "avatar": user[3]} }
                await ws.send(json.dumps(userAttributes))

async def introduceClient(clientId, roomId, avatar, ws):

    newPeerNotice = {"newPeer": {"id": clientId, "avatar": avatar} }
    for peerWs in [x[0] for x in sockets[roomId]]:
        if peerWs is not ws:
            await peerWs.send(json.dumps(newPeerNotice))

# everything in the handler function is the bidirectional 
# communication of a single client with the ws server
async def handler(ws, path):

    ### NEW CONNECTION SETUP

    # add new user to the requested room or a new one
    roomId = await arrangeRoom(ws)
    # assign user an id and avatar within the room
    clientId, avatar = await setupNewClient(roomId, ws)
    # send the video source and state to the new client
    await sendCurrentVideo(roomId, ws)
    # send a list of already connected clients to the newcomer
    await sendUsers(clientId, roomId, ws)
    # notify other clients about the newcomer
    await introduceClient(clientId, roomId, avatar, ws)

    # add new clients websocket to the list
    sockets[roomId].add((ws,clientId))

    try:

        ### MESSAGING

        while True:

            messageFromClient = await ws.recv()

            log(f"Message from client {clientId}: {messageFromClient}")

            if "newSource" in messageFromClient:
            # client changed video source, forward info to peers

                messageJSON = json.loads(messageFromClient)
                newSource = messageJSON["newSource"]["url"]
                db.setCurrentVideo(roomId, newSource)

            if "peerName" in messageFromClient:
            # client changed their username, forward info to peers

                messageJSON = json.loads(messageFromClient)
                name = messageJSON["peerName"]["name"]

                # update client with the new name
                log(f"Saving the name \"{name}\" for client {clientId}")
                db.setName(clientId, name)

            # forwarding message
            for peerWs in [x[0] for x in sockets[roomId]]:
                if peerWs is not ws:
                    await peerWs.send(messageFromClient)

            # client changed video state, forward info to peers
            if "videoState" in messageFromClient:
                db.setVideoState(roomId, messageFromClient)

    except websockets.exceptions.ConnectionClosed:

        log(f"Connection to Client {clientId} is closed")

    finally:

        # END OF CONNECTION
    
        log(f"Removing Client {clientId} from room {roomId}")
        sockets[roomId].remove((ws,clientId))
        db.removeUser(clientId, roomId)

        # notify other users about the leaver
        for peerWs in [x[0] for x in sockets[roomId]]:
            if peerWs is not ws:
                peerLeftNotice = {"peerLeft": {"id": clientId} }
                await peerWs.send(json.dumps(peerLeftNotice))

if __name__ == '__main__':

    log("Starting websocket server")
    db.cursor = db.initialize()

    if len(argv) > 1 and argv[1] == "--no-ssl":
    
        start_server = websockets.serve(handler, '', 8001)
    
    else:

        certs = db.cursor.execute("SELECT * FROM ssl_certificates").fetchone()
        certFile, keyFile = certs[0], certs[1]

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certFile, keyFile)

        start_server = websockets.serve(handler, '', 8001, ssl=ssl_context)        
    
    try:

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    
    except KeyboardInterrupt as e:
    
        print(str(e))
        log("Stopping websocket server")
        db.close()