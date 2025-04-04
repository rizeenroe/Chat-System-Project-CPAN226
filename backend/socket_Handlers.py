from flask import request
from flask_socketio import join_room, leave_room, emit
from datetime import datetime
import threading
from database import save_message, get_room_messages
from auth import verify_token
from socket_Initializer import socketio

# Data structures for tracking users
users = {}          # {username: {room: str, sid: str}}
authenticated_sids = {}  # {sid: username}
connected_users = {}     # {username: sid}
users_lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    print(f"New connection attempt: {request.sid}")
    token = request.args.get('token')
    if not token:
        emit('error', {'message': 'No token provided'})
        return False
    
    if not verify_token(token):
        emit('error', {'message': 'Authentication failed'})
        return False
    
    with users_lock:
        authenticated_sids[request.sid] = token
        connected_users[token] = request.sid
    print(f"User connected: {token} (SID: {request.sid})")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    with users_lock:
        if sid in authenticated_sids:
            username = authenticated_sids.pop(sid)
            if username in connected_users:
                del connected_users[username]
            
            if username in users:
                room = users[username]['room']
                leave_room(room)
                del users[username]
                
                emit('system_message', {
                    'type': 'leave',
                    'username': username,
                    'message': f'{username} disconnected',
                    'timestamp': datetime.now().isoformat()
                }, room=room)
    print(f"User disconnected: {sid}")

@socketio.on('join')
def handle_join(data):
    sid = request.sid
    token = request.args.get('token')
    
    if not verify_token(token):
        emit('error', {'message': 'Not authenticated'})
        return
    
    room = data.get('room')
    if not room:
        emit('error', {'message': 'Room name required'})
        return
    
    with users_lock:
        # Leave previous room if exists
        if token in users:
            old_room = users[token]['room']
            leave_room(old_room)
            emit('system_message', {
                'type': 'leave',
                'username': token,
                'message': f'{token} left the room',
                'timestamp': datetime.now().isoformat()
            }, room=old_room)
        
        # Join new room
        join_room(room)
        users[token] = {'room': room, 'sid': sid}
        
        # Retrieve and send chat history
        chat_history = get_room_messages(room)
        emit('chat_history', {
            'room': room,
            'messages': [
                {
                    'sender': msg['sender'],
                    'message': msg['message'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'type': 'room'
                } for msg in chat_history
            ]
        }, to=sid)
        
        emit('joined_room', {'room': room})
        emit('system_message', {
            'type': 'join',
            'username': token,
            'message': f'{token} joined the room',
            'timestamp': datetime.now().isoformat()
        }, room=room)
    
    print(f"{token} joined room: {room}")
    
    print(f"{token} joined room: {room}")

@socketio.on('room_message')
def handle_room_message(data):
    sid = request.sid
    if sid not in authenticated_sids:
        emit('error', {'message': 'Not authenticated'})
        return
    
    message = data.get('message')
    if not message or not message.strip():
        emit('error', {'message': 'Message cannot be empty'})
        return
    
    sender = authenticated_sids[sid]
    
    with users_lock:
        if sender not in users:
            emit('error', {'message': 'You must join a room first'})
            return
        
        room = users[sender]['room']
        timestamp = datetime.now().isoformat()
        
        # Save to database first
        save_message(sender, room, message.strip())
        
        # Then emit to room (including sender)
        emit('room_message', {
            'sender': sender,
            'message': message.strip(),
            'timestamp': timestamp,
            'type': 'room'
        }, room=room)
    
    print(f"Room message from {sender} in {room}: {message}")

@socketio.on('private_message')
def handle_private_message(data):
    sid = request.sid
    if sid not in authenticated_sids:
        emit('error', {'message': 'Not authenticated'})
        return
    
    sender = authenticated_sids[sid]
    recipient = data.get('recipient')
    message = data.get('message')
    
    if not recipient or not message or not message.strip():
        emit('error', {'message': 'Recipient and message are required'})
        return
    
    # Save to database
    save_message(sender, recipient, message.strip())
    print(f"Saved private message: {sender} -> {recipient}: {message}")
    
    with users_lock:
        if recipient not in connected_users:
            emit('error', {'message': f'{recipient} is not online'})
            return
        
        # Send to recipient
        emit('private_message', {
            'sender': sender,
            'message': message.strip(),
            'timestamp': datetime.now().isoformat(),
            'type': 'private'
        }, to=connected_users[recipient])
        
        # Send delivery confirmation to sender
        emit('private_message_delivered', {
            'recipient': recipient,
            'message': message.strip(),
            'timestamp': datetime.now().isoformat()
        }, to=sid)
    
    print(f"Private message delivered: {sender} -> {recipient}")