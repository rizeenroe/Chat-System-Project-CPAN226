from pymongo import MongoClient

# MongoDB connection URI
MONGO_URI = "mongodb+srv://BeaVert:UtxyMWFV1jcLeOUd@birmanbank.wvqrnfl.mongodb.net/?retryWrites=true&w=majority&appName=BirmanBank"
DB_NAME = "chat_system"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def initialize_db():
    """Initialize the database with the required collections."""
    users_collection = db["users"]
    users_collection.create_index("username", unique=True)

def get_user(username):
    """Retrieve a user by username."""
    return db["users"].find_one({"username": username})

def add_user(username, password):
    """Add a new user to the database."""
    db["users"].insert_one({"username": username, "password": password, "ip": None, "port": None})

def update_user_ip_port(username, ip, port):
    """Update the IP and port of a user."""
    db["users"].update_one({"username": username}, {"$set": {"ip": ip, "port": port}})