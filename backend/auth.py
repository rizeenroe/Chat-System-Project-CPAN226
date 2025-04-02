from flask import Blueprint, request, jsonify
from database import get_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = get_user(username)
    if user and user["password"] == password:
        return jsonify({
            "username": username,
            "token": username  # Using username as token for simplicity
        }), 200
    return jsonify({"error": "Invalid credentials"}), 401

def verify_token(token):
    user = get_user(token)
    return user is not None