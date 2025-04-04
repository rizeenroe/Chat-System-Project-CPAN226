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
    conversation_id = f"{participants[0]}_{participants[1]}" #makes the conversation id with the two users (participants)
    
    #check if the conversation already exists
    conversation = db["conversations"].find_one({"conversation_id": conversation_id})
    #if conversation does not exist it creates it 
    if not conversation:
        db["conversations"].insert_one({
            "conversation_id": conversation_id,
            "participants": participants,
            "messages": []
        })
    return conversation_id

#saves a message in the database - called when a message is sent
def save_message(sender, recipient, message, is_private):
    print(f"Saving message from {sender} to {recipient}: {message} {is_private}")
    
    #cheks if the recipient is a room or a user 
    #if true then it makes the conversation id with the two users (participants)
    #if false then it makes the conversation id with the room name
    if is_private:
        #for private conversations sort the users (sender and recipient)
        #then set the conversation id as the sorted users
        participants = sorted([sender, recipient])
        conversation_id = f"{participants[0]}_{participants[1]}"
    else:
        #for room conversations, the first participant is the room id
        conversation_id = "Room Chat" + recipient
    
    #formates the data to be saved in the database
    message_data = {
        "sender": sender,
        "message": message,
        "timestamp": datetime.now() #used for the time stamp
    }
    
    #saves the message in the database with the conversation id
    #if the conversation does not exist it creates it
    db["conversations"].update_one(
        {"conversation_id": conversation_id},
        {"$push": {"messages": message_data}},
        upsert=True  #create the conversation if it doesn't exist
    )

def get_messages_between_users(user1, user2):
    participants = sorted([user1, user2])
    conversation_id = f"{participants[0]}_{participants[1]}"
    conversation = db["conversations"].find_one({"conversation_id": conversation_id})
    return conversation["messages"] if conversation else []