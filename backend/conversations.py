from flask import Blueprint, request, jsonify
from database import db, get_user

conversations_bp = Blueprint('conversations', __name__)

@conversations_bp.route('/conversations', methods=['GET'])
def get_user_conversations():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is required"}), 401

    user = get_user(token)
    if not user:
        return jsonify({"error": "Invalid token"}), 401

    username = user["username"]

    # Search for conversations where the user is a participant
    conversations_cursor = db["conversations"].find({
        "conversation_id": {"$regex": f"^{username}_|_{username}$"}
    })

    user_conversations = []
    for conversation in conversations_cursor:
        # Extract the other participant from the conversation_id
        participants = conversation["conversation_id"].split("_")
        other_user = participants[0] if participants[1] == username else participants[1]

        user_conversations.append({
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

    return jsonify(user_conversations), 200
