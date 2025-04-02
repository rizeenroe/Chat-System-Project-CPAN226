from database import initialize_db
from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS
from auth import auth_bp, verify_token
from datetime import datetime
import socket
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(auth_bp, url_prefix='/auth')

users = {}
authenticated_sids = {}
tcp_connections = {}
users_lock = threading.Lock()

def get_tcp_connection():
    thread_id = threading.get_ident()
    if thread_id not in tcp_connections:
        try:
            sock = socket.create_connection(('localhost', 5001))
            sock.send(b"websocket")
            tcp_connections[thread_id] = sock
        except Exception as e:
            print(f"TCP connection failed: {e}")
            return None
    return tcp_connections[thread_id]

def send_tcp_message(sender, recipient, message):
    try:
        sock = get_tcp_connection()
        if not sock:
            return "error"
            
        formatted_msg = f"send_message:{sender}:{recipient}:{message}"
        sock.sendall(formatted_msg.encode("utf-8"))
        return sock.recv(1024).decode("utf-8").strip()
    except Exception as e:
        print(f"TCP error: {e}")
        thread_id = threading.get_ident()
        if thread_id in tcp_connections:
            try:
                tcp_connections[thread_id].close()
            except:
                pass
            del tcp_connections[thread_id]
        return "error"

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    if not verify_token(token):
        emit('error', {'message': 'Authentication failed'})
        return False
    authenticated_sids[request.sid] = token
    print(f"User connected: {token}")

@socketio.on("join")
def handle_join(data):
    token = request.args.get('token')
    if not verify_token(token):
        emit("error", {"message": "Not authenticated"})
        return

    room = data.get("room")
    with users_lock:
        if token in users:
            old_room = users[token]["room"]
            leave_room(old_room)
            emit("system_message", {
                "type": "leave",
                "username": token,
                "room": old_room,
                "message": f"{token} left",
                "timestamp": datetime.now().isoformat()
            }, room=old_room)

        join_room(room)
        users[token] = {"room": room, "sid": request.sid}
        emit("system_message", {
            "type": "join",
            "username": token,
            "room": room,
            "message": f"{token} joined",
            "timestamp": datetime.now().isoformat()
        }, room=room)
        emit("joined_room", {"room": room})

@socketio.on("room_message")
def handle_room_message(data):
    sid = request.sid
    if sid not in authenticated_sids:
        emit("error", {"message": "Not authenticated"})
        return

    sender = authenticated_sids[sid]
    message = data.get("message")
    with users_lock:
        if sender in users:
            room = users[sender]["room"]
            emit("room_message", {
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "room"
            }, room=room, skip_sid=sid)

@socketio.on("private_message")
def handle_private_message(data):
    sid = request.sid
    if sid not in authenticated_sids:
        emit("error", {"message": "Not authenticated"})
        return

    sender = authenticated_sids[sid]
    recipient = data.get("recipient")
    message = data.get("message")

    if not all([recipient, message]):
        emit("error", {"message": "Recipient and message required"})
        return

    response = send_tcp_message(sender, recipient, message)

    if response == "ok":
        emit("private_message", {
            "sender": sender,
            "recipient": recipient,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "delivered"
        })
    elif "offline" in response.lower():
        with users_lock:
            if recipient in users:
                emit("private_message", {
                    "sender": sender,
                    "recipient": recipient,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "status": "delivered"
                }, room=users[recipient]["sid"])
                emit("private_message", {
                    "sender": sender,
                    "recipient": recipient,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "status": "delivered"
                })
            else:
                emit("message_error", {"message": f"{recipient} offline"})
    else:
        emit("message_error", {"message": f"Error: {response}"})

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    with users_lock:
        if sid in authenticated_sids:
            username = authenticated_sids.pop(sid)
            if username in users:
                room = users[username]["room"]
                del users[username]
                emit("system_message", {
                    "type": "leave",
                    "username": username,
                    "message": f"{username} disconnected",
                    "timestamp": datetime.now().isoformat()
                }, room=room)
                leave_room(room)

if __name__ == '__main__':
    initialize_db()  # Initialize the MongoDB database
    socketio.run(app, host='0.0.0.0', port=5000)