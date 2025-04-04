from flask_socketio import SocketIO

#creates a Socket.IO instance
#the `cors_allowed_origins="*"` setting allows connections from any origin - for the socket.io server separate from the flash server
socketio = SocketIO(cors_allowed_origins="*")