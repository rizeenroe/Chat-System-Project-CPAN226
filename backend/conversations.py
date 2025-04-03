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

    # Fetch conversations where the user is a participant
    conversations = db["conversations"].find({"participants": token})
    user_conversations = []

    for conversation in conversations:
        other_user = [p for p in conversation["participants"] if p != token][0]
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