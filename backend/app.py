from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)

# initialize SocketIO with CORS allowed for any origin (use a specific domain in production)
socketio = SocketIO(app, cors_allowed_origins="*")

# to store user sessions
users = {}

# handle user connection and room joining
@socketio.on("join")
def handle_join(data):
   username = data["username"]
   room = data["room"]
   users[username] = room
   join_room(room) 
   
   # debug
   print(f"User {username} joined room {room}")
   
   send(f"{username} has joined the chat.", room=room)

# handles the messages
@socketio.on("private_message")
def handle_private_message(data):
   sender = data["sender"]
   recipient = data["recipient"]
   message = data["message"]
   
   # debug
   print(f"Users: {users}") 
   
   # get the recipient's room
   room = users.get(recipient)
   
   if room:
      print(f"Message from {sender} to {recipient} in room: {room}")
      send(f"{sender}: {message}", room=room)
   else:
      print(f"Recipient {recipient} not found in users.")
      send("{recipient} User is not online", room=users.get(sender))
   
# handle disconnecting
@socketio.on("disconnect")   
def handle_disconnect():
   for username, room in users.items():
      leave_room(room)
      send(f"{username} has left the chat.", room=room)
      del users[username]
      break


# # handling incoming messages from clients
# @socketio.on("message")
# def handle_message(msg):
#    print(f"Received message {msg}")
#    send(msg, broadcast=True)
   
# run the Flask app with SocketIO support
if __name__ == "__main__":
   socketio.run(app, host="0.0.0.0", port=5000)
   
   