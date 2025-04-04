from database import initialize_db
from flask import Flask
from flask_cors import CORS
from auth import auth_bp
from conversations import conversations_bp
from socket_Handlers import socketio


def create_app():
    app = Flask(__name__)
    #enables CORS for the application to allow cross-origin requests (like the frontend) to communicate with the backend
    #frontend will always have a different origin (ip) because it will be running on other systems (users)
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    #register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(conversations_bp, url_prefix='/api')

    #initializes Socket.IO with the app
    socketio.init_app(app)

    return app

#starts the flask-socketio server
if __name__ == '__main__':
    app = create_app() #creates the Flask app instance
    initialize_db() #initializes the database
    print("Starting server...") #debugging
    socketio.run(app, 
                host='0.0.0.0', 
                port=5000, 
                use_reloader=True, #automaticlly restarts the project when changes are made
                )