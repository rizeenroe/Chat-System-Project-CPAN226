from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "DB-URL-HERE"
DB_NAME = "chat_system"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def initialize_db():
    """Initialize the database with required collections and indexes."""
    users_collection = db["users"]
    users_collection.create_index("username", unique=True)
    
    conversations_collection = db["conversations"]
    conversations_collection.create_index("conversation_id", unique=True)
    conversations_collection.create_index("participants")

def get_user(username):
    """Retrieve a user by username."""
    return db["users"].find_one({"username": username})

def add_user(username, password):
    """Add a new user."""
    db["users"].insert_one({
        "username": username,
        "password": password,
        "ip": None,
        "port": None
    })

def update_user_ip_port(username, ip, port):
    """Update user's IP and port."""
    db["users"].update_one({"username": username}, {"$set": {"ip": ip, "port": port}})

def get_or_create_conversation(participants):
    """Retrieve or create a conversation between participants."""
    participants = sorted(participants)  # Ensure consistent order
    conversation_id = f"{participants[0]}_{participants[1]}"
    
    conversation = db["conversations"].find_one({"conversation_id": conversation_id})
    if not conversation:
        db["conversations"].insert_one({
            "conversation_id": conversation_id,
            "participants": participants,
            "messages": []
        })
    return conversation_id

def save_message(sender, recipient, message):
    """Save a message in the appropriate conversation."""
    is_private = not recipient.startswith("room_")
    
    if is_private:
        participants = [sender, recipient]
        conversation_id = get_or_create_conversation(participants)
    else:
        conversation_id = recipient  # For rooms, use the room name as the conversation ID
    
    message_data = {
        "sender": sender,
        "message": message,
        "timestamp": datetime.now()
    }
    
    db["conversations"].update_one(
        {"conversation_id": conversation_id},
        {"$push": {"messages": message_data}}
    )

def get_room_messages(room):
    """Retrieve messages for a room."""
    conversation = db["conversations"].find_one({"conversation_id": room})
    return conversation["messages"] if conversation else []

def get_messages_between_users(user1, user2):
    """Retrieve messages between two users."""
    participants = sorted([user1, user2])
    conversation_id = f"{participants[0]}_{participants[1]}"
    conversation = db["conversations"].find_one({"conversation_id": conversation_id})
    return conversation["messages"] if conversation else []