import sqlite3, json
import pickle

defaultSource = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
defaultVideoState = json.dumps({ "videoState": { "position": 0, "paused": True} })

def initialize():

    global conn, cursor
    conn = sqlite3.connect('syncwatch.db')
    cursor = conn.cursor()
    conn.isolation_level = None # for autocommit

    # Create tables
    cursor.execute('''
                    
                    CREATE TABLE IF NOT EXISTS rooms (
                        id TEXT PRIMARY KEY, 
                        clientIdCounter INTEGER, 
                        sourceURL TEXT, 
                        videoState TEXT
                    )
                    
                    ''')

    cursor.execute('''
                
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY, 
                        room TEXT, 
                        name TEXT, 
                        avatar INTEGER
                    )
                    
                    ''')

    return cursor

def roomIdExists(roomId):
    return cursor.execute("SELECT EXISTS (SELECT 1 FROM rooms WHERE id=?)", 
                        (roomId,)).fetchone()[0] is 1

def createRoom(roomId):
    cursor.execute('''INSERT INTO rooms (id, clientIdCounter, sourceURL, videoState) 
                    VALUES (?,?,?,?)''', (roomId, 0, defaultSource, defaultVideoState))

def getNewClientId(roomId):

    newId = cursor.execute("SELECT clientIdCounter FROM rooms WHERE id=?", 
                        (roomId,)).fetchone()[0]
    cursor.execute("UPDATE rooms SET clientIdCounter=? WHERE id=?", (newId+1, roomId))
    return newId

def getCurrentVideo(roomId):
  
    q = cursor.execute("SELECT sourceURL, videoState FROM rooms WHERE id=?", 
                    (roomId,)).fetchone()
    sourceURL, videoState = q[0], q[1]
    return sourceURL, videoState

def setCurrentVideo(roomId, newSource):
    cursor.execute("UPDATE rooms SET sourceURL=?, videoState=? WHERE id=?", 
                    (newSource, defaultVideoState, roomId))

def setVideoState(roomId, videoState):
    cursor.execute("UPDATE rooms SET videoState=? WHERE id=?", (videoState, roomId))

def addUser(clientId ,roomId, avatar):
    
    name = f"Guest {clientId}"
    cursor.execute("INSERT INTO users (id, room, name, avatar) VALUES (?,?,?,?)", 
                (clientId, roomId, name, avatar))

def removeUser(clientId, roomId):
    
    cursor.execute("DELETE FROM users WHERE id=? AND room=?", (clientId, roomId))
    users = cursor.execute("SELECT * FROM users WHERE room=?", (roomId,)).fetchall()

    # if nobody is left in the room reset the id counter
    if len(users) is 0:
        cursor.execute("UPDATE rooms SET clientIdCounter=0 WHERE id=?", (roomId,))

def getUsers(roomId):
    return cursor.execute("SELECT * FROM users WHERE room=?", (roomId,)).fetchall()

def setName(clientId, name):
    cursor.execute("UPDATE users SET name=? WHERE id=?", (name, clientId))

def close():
    conn.close()