from database import initialize_db
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from auth import auth_bp
from conversations import conversations_bp
from socket_Handlers import socketio

def create_app():
    app = Flask(__name__)
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(conversations_bp, url_prefix='/api')

    # Initialize Socket.IO with the app
    socketio.init_app(app)

    return app

if __name__ == '__main__':
    app = create_app()
    initialize_db()
    print("Starting server...")
    socketio.run(app, 
                host='0.0.0.0', 
                port=5000, 
                debug=True, 
                use_reloader=True,
                log_output=True)