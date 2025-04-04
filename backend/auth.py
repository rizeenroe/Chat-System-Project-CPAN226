from flask import Blueprint, request, jsonify
from database import get_user, db

#creates a blueprint for the conversations
#makes and instance of blueprint
auth_bp = Blueprint('auth', __name__)

# TO MAKE IT SIMPLIER / TO HAVE LESS CODE TO MAKE
# WE ARE JUST USING THE USERNAME AS THE TOKEN
#ˡᵒᵒᵏᶦⁿᵍ ᵇᵃᶜᵏ ᵃᵗ ᶦᵗ ᶦ ᵗʰᶦⁿᵏ ᶦ ʲᵘˢᵗ ʰᵃᵈ ᵗᵒ ᵃᵈᵈ ᵗʰᵉ ᵗᵒᵏᵉⁿ ᶜᵒᵈᵉ....ᵉᵛᵉʳʸᵗʰᶦⁿᵍ ᵉˡˢᵉ ᶦˢ ᵃˡʳᵉᵃᵈʸ ˢᵉᵗᵘᵖ ᶠᵒʳ ᶦᵗ ᶦᵐ ᵖʳᵉᵗᵗʸ ˢᵘʳᵉ

@auth_bp.route('/login', methods=['POST'])
def login():
    #parses the json data from the incoming request
    data = request.get_json()
    
    #extracts the username and password from the request data
    username = data.get('username')
    password = data.get('password')

    #cheks if both username and password are provided
    if not username or not password:
        #if not it returns an error
        return jsonify({"error": "Username and password are required"}), 400 #400 (Bad Request)

    #retrieves the user from the database using the provided username
    user = get_user(username)
    
    #checks if the user exists and the password matches
    if user and user["password"] == password:
        #returns a success response with the username and token (the username again)
        return jsonify({
            "username": username,
            "token": username
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401

#used to verify the token returning the username
def verify_token(token):
    user = get_user(token)
    return user["username"] if user else None