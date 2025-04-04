from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb+srv://BeaVert:UtxyMWFV1jcLeOUd@birmanbank.wvqrnfl.mongodb.net/?retryWrites=true&w=majority&appName=BirmanBank"
DB_NAME = "chat_system"

client = MongoClient(MONGO_URI) 
db = client[DB_NAME]

#initialize the database (in this case mongoDB) and create the collections
#called when the server starts
def initialize_db():
    """Initialize the database with required collections and indexes."""
    users_collection = db["users"] # Create users collection
    users_collection.create_index("username", unique=True) # sets username to be unique
    
    conversations_collection = db["conversations"] #conversations collection
    conversations_collection.create_index("conversation_id", unique=True) # sets conversation_id to be unique
    conversations_collection.create_index("participants") 

#gets the user from the database by username returning none if not found
def get_user(username):
    return db["users"].find_one({"username": username})

#adds a new user to the database called when a new user registers
def add_user(username, password):
    #add a new user to the database
    db["users"].insert_one({ 
        "username": username,
        "password": password,
    })

#retrieve or create a conversation between participants.
def get_or_create_conversation(participants):
    participants = sorted(participants) #sorts to ensure consistent order
    conversation_id = f"{participants[0]}_{participants[1]}"
    
    conversation = db["conversations"].find_one({"conversation_id": conversation_id})
    
    # check if the conversation already exists if not it creates it
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
        # Get or create a private conversation
        participants = sorted([sender, recipient])
        conversation_id = f"{participants[0]}_{participants[1]}"
    else:
        # Room conversation
        conversation_id = recipient
    
    message_data = {
        "sender": sender,
        "message": message,
        "timestamp": datetime.now()
    }
    
    db["conversations"].update_one(
        {"conversation_id": conversation_id},
        {"$push": {"messages": message_data}},
        upsert=True  # Create the conversation if it doesn't exist
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