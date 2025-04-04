from flask import request
from flask_socketio import join_room, leave_room, emit
from datetime import datetime
from database import save_message, get_user
from auth import verify_token
from socket_Initializer import socketio
import threading #used to allow multiple users to connect to the server at the same time

#there is no actual token being made in this program, the token is just the username of the user

users = {} #used to store usersm, the room they might be in and there session id
authenticated_sids = {} #used to store authenticated users
connected_users = {} #used to track the users that are connected to the server

#threading is used to allow multiple users to connect to the server at the same time
#thread locking is used to prevent multiple threads from accessing the same resource at the same time
#prevents race conditions when multiple users connect or disconnect at the same time
users_lock = threading.Lock() 

#---------error messages---------#
ERROR_NO_TOKEN = {'message': 'No token provided'}
ERROR_AUTH_FAILED = {'message': 'Authentication Failed'}
ERROR_ROOM_REQUIRED = {'message': 'Room name required'}
ERROR_MESSAGE_EMPTY = {'message': 'Message cannot be empty'}
ERROR_JOIN_ROOM_FIRST = {'message': 'You must join a room first'}
ERROR_NOT_AUTHENTICATED = {'message': 'Not authenticated'}
ERROR_RECIPIENT_REQUIRED = {'message': 'Recipient and message are required'}

#---------Commonly used functions---------#
#used to emit error messages to the user
#emit is used to send a message to the user
def emit_error(message: dict, sid: str = None):
    emit('error', message, to=sid)

#used to check if the user is authenticated
#authenticates the user by checking if the token is valid
def authenticate_user() -> str:
    token = request.args.get('token') #get the users auth token from the request
    if not token or not verify_token(token): #check if the token is missing or is valid
        return None #returns None if the token is missing or invalid
    return token #returns the token if the user is authenticated

#used to get the current user
def get_current_user() -> str:
    #gets the username of the currently authenticated user
    sid = request.sid
    return authenticated_sids.get(sid)

#---------socketIO event handlers---------#

#part of the socketIO library
#this is used to handle the connection of the users to the server
#when a user connects to the server this function is called
@socketio.on('connect')
def handle_connect():
    #used to print to terminal when a user conencts - mainly used for debugging
    print(f"New connection attempt: {request.sid}") #debugging
    
    token = authenticate_user() #authenticates the user
    
    if not token:
        print ("Authentication failed - HANDLE_CONNECT METHOD") #debugging
        #in this case the frontend user that is trying to connect
        #sends "NO_TOKEN" message if the token is missing - if not then sends "AUTH_FAILED" message 
        emit_error(ERROR_NO_TOKEN if not request.args.get('token') else ERROR_AUTH_FAILED)
        return False #returnes false to stop the connection
        
    with users_lock:
        #assosiates the current websocket session id to the username
        #allows the server to know which user is connected to which session id
        authenticated_sids[request.sid] = token 
        
        #assosiates the username to the current session id
        #allows the server to know which session id is connected to which user
        #just makes it easier to send and manage connections for the user
        connected_users[token] = request.sid 
    print(f"User connected: {token} (SID: {request.sid})") #debugging

#this is used to handle the disconnection of the users from the server
#when a user disconnects from the server this function is called
@socketio.on('disconnect')
def handle_disconnect():
    
    sid = request.sid #gets the session id of the user that is disconnecting
    
    with users_lock:
        #checks if the session is is in the authenticated sids
        #if the session id is in the authenticated sids
        if sid in authenticated_sids:
            
            #removes the session id from the authenticated sids using pop 
            #pop is used to remove something from a list and return its value - in this case the associated username
            username = authenticated_sids.pop(sid)
            
            #if the user is in the connected users (checking if the user is connected to the server)
            if username in connected_users:
                #removes the username from the list
                del connected_users[username]
            
            #if the user is in the users list
            if username in users:
                room = users[username]['room'] #get the room the user is in
                leave_room(room) #removes the user from the room
                del users[username] #removes the user from the users list
                
                #sends a message to the room that the user has disconnected
                emit('system_message', {
                    'type': 'leave',
                    'username': username,
                    'message': f'{username} disconnected',
                    'timestamp': datetime.now().isoformat() #isoformat used to 'standardize' the time format
                }, room=room) #room room sets the room the message is sent to to the room the user was in
                
    print(f"User disconnected: {sid}") #debugging

#this is used to handle the joining of the users to a room
#when a user joins a room this function is called
@socketio.on('join')
def handle_join(data):      
    token = authenticate_user() #authenticates the user
    
    if not token:
        print ("Authentication failed - HANDLE_JOIN METHOD") #debugging
        emit_error(ERROR_AUTH_FAILED)
        return #the blank returns are used to stop the function from running
    
    
    room = data.get('room') #get the room nae from the frontend (what the user inputted)
    
    #if the room name is not provided
    if not room:
        emit_error(ERROR_ROOM_REQUIRED)
        return #the blank returns are used to stop the function from running
    
    with users_lock:
        #if the user is already in a room
        if token in users:
            old_room = users[token]['room'] #gets the room the user is in
            leave_room(old_room) #removes the user from the room
            
            #sends a message to the room that the user has disconnected
            emit('system_message', {
                'type': 'leave',
                'username': token,
                'message': f'{token} left the room',
                'timestamp': datetime.now().isoformat()
            }, room=old_room)
        
        #joins the new room (adds the user to it)
        join_room(room)
        
        #updates the users list with the new room and session id
        users[token] = {'room': room, 'sid': request.sid}
         
        #sends a message to the room that the user has joined
        emit('joined_room', {'room': room})
        emit('system_message', {
            'type': 'join',
            'username': token,
            'message': f'{token} joined the room',
            'timestamp': datetime.now().isoformat()
        }, room=room)
    
    print(f"{token} joined room: {room}") #debugging

#this handles the messages sent to the room
#when a user sends a message to the room this function is called
@socketio.on('room_message')
def handle_room_message(data):
    
    #gets the username of the currently authenticated user
    sender = get_current_user() 

    if not sender:
        print ("Authentication failed - HANDLE_ROOM_MESSAGE METHOD") #debugging
        emit_error(ERROR_NOT_AUTHENTICATED)
        return #the blank returns are used to stop the function from running
    
    #gets the message from the frontend (sent by the user)
    message = data.get('message')
    
    #if the message is empty
    if not message or not message.strip():
        emit_error(ERROR_MESSAGE_EMPTY)
        return #the blank returns are used to stop the function from running
       
    with users_lock:
        #checks if the user is in the users list
        #if the user is not in the users list
        if sender not in users:
            emit_error(ERROR_JOIN_ROOM_FIRST)
            return #the blank returns are used to stop the function from running
        
        room = users[sender]['room'] #get the room the user is in
        timestamp = datetime.now().isoformat() #make a timestamp for the message
        
        #save the message to the database
        save_message(sender, room, message.strip(), is_private=False) #saying that the message is not private
        
        #sends the message to the room
        emit('room_message', {
            'sender': sender,
            'message': message.strip(),
            'timestamp': timestamp,
            'type': 'room'
        }, room=room)
    
    print(f"Room message from {sender} in {room}: {message}")

@socketio.on('private_message')
def handle_private_message(data):
    #gets the username of the currently authenticated user
    sender = get_current_user()
    if not sender:
        print ("Authentication failed - HANDLE_PRIVATE_MESSAGE METHOD") #debugging
        emit_error(ERROR_NOT_AUTHENTICATED)
        return #the blank returns are used to stop the function from running
    
    recipient = data.get('recipient')
    message = data.get('message')
    
    #if the recipient is not provided or not a registured user or the message is empty or blank
    if not recipient or not get_user(recipient) or not message or not message.strip():
        emit_error(ERROR_RECIPIENT_REQUIRED)
        return #the blank returns are used to stop the function from running
    
    #save the message to the database
    save_message(sender, recipient, message.strip(), is_private=True) #saying that the message is private
    
    print(f"Saved private message: {sender} -> {recipient}: {message}") #debugging
    
    with users_lock:
        if recipient not in connected_users:
            emit('error', {'message': f'{recipient} is not online'})
            return #the blank returns are used to stop the function from running
        
        #send to recipient
        emit('private_message', {
            'sender': sender,
            'message': message.strip(),
            'timestamp': datetime.now().isoformat(),
            'type': 'private'
        }, to=connected_users[recipient])
        
        #send delivery confirmation to sender
        emit('private_message_delivered', {
            'recipient': recipient,
            'message': message.strip(),
            'timestamp': datetime.now().isoformat()
        }, to=request.sid)
    
    print(f"Private message delivered: {sender} -> {recipient}") #debugging