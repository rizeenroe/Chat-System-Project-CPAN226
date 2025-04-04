from flask import Blueprint, request, jsonify
from database import get_user, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = get_user(username)
    if user and user["password"] == password:
        # Handle legacy messages without conversation_id
        legacy_messages = db["messages"].find({
            "$or": [{"sender": username}, {"recipient": username}],
            "recipient": {"$not": {"$regex": "^room_"}},
            "conversation_id": {"$exists": False}
        })
        
        for msg in legacy_messages:
            sender = msg["sender"]
            recipient = msg["recipient"]
            participants = sorted([sender, recipient])
            conv_id = f"{participants[0]}_{participants[1]}"
            db["messages"].update_one(
                {"_id": msg["_id"]},
                {"$set": {"conversation_id": conv_id}}
            )
            db["users"].update_many(
                {"username": {"$in": participants}},
                {"$addToSet": {"conversations": conv_id}}
            )
        
        # Get updated user data
        user = get_user(username)
        private_conversations = []
        conversations = db["conversations"].find({"participants": username})
        
        for conversation in conversations:
            other_user = [p for p in conversation["participants"] if p != username][0]
            private_conversations.append({
                "conversation_id": conversation["conversation_id"],
                "with_user": other_user,
                "messages": [
                    {
                        "sender": msg["sender"],
                        "message": msg["message"],
                        "timestamp": msg["timestamp"].isoformat()
                    } for msg in conversation["messages"]
                ]
            })
        
        # Room chat handling remains the same
        room_chats = {}
        rooms = db["messages"].distinct("recipient", {"recipient": {"$regex": "^room_"}})
        for room in rooms:
            room_messages = db["messages"].find({"recipient": room}).sort("timestamp", 1)
            room_chats[room] = [
                {
                    "sender": msg["sender"],
                    "message": msg["message"],
                    "timestamp": msg["timestamp"].isoformat()
                } for msg in room_messages
            ]
        
        return jsonify({
            "username": username,
            "token": username,
            "private_conversations": private_conversations,
            "room_chats": room_chats
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

def verify_token(token):
    """Verify if token is valid and return the username."""
    user = get_user(token)
    return user["username"] if user else None