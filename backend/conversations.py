# from flask import Blueprint, request, jsonify
# from database import db, get_user


# conversations_bp = Blueprint('conversations', __name__)

#route to get all conversations for a user using the endpoint /conversations
# @conversations_bp.route('/conversations', methods=['GET'])
# def get_user_conversations():
#     token = request.headers.get('Authorization') #gets the authorization token from the request headers
    
#     #checks if the token is present
#     if not token:
#         #if not present
#         return jsonify({"error": "Authorization token is required"}), 401 #401 (Unauthorized)

#     #validate the token and retrieve the associated user
#     user = get_user(token)     
#     if not user:
#         #if the token is invalid
#         return jsonify({"error": "Invalid token"}), 401 #401 (Unauthorized)

#     #get the username from the user object
#     username = user["username"]

#     #searchs for conversations where the user is a participant in using regex
#     conversations_cursor = db["conversations"].find({
#         "conversation_id": {"$regex": f"^{username}_|_{username}$"}
#     })


#     user_conversations = [] #list to store the conversations for the user
    
#     #initialize a list to store the user's conversations
#     for conversation in conversations_cursor:
        
#         participants = conversation["conversation_id"].split("_") #gets the other participants from the conversation_id
        
#         other_user = participants[0] if participants[1] == username else participants[1] #gets the other user in the conversation
        
        #appends the conversation details to the list, including:
        #the conversation ID
        #the other participants username
        #the list of messages in the conversation
#         user_conversations.append({
#             "conversation_id": conversation["conversation_id"],
#             "with_user": other_user,
#             "messages": [
#                 {
#                     "sender": msg["sender"],
#                     "message": msg["message"],
#                     "timestamp": msg["timestamp"].isoformat()
#                 } for msg in conversation["messages"]
#             ]
#         })

#     #return the list of user conversations as a JSON response with status 200 (OK)
#     return jsonify(user_conversations), 200

from flask import Blueprint, request, jsonify
from database import db, get_user

#creates a blueprint for the conversations
#makes and instance of blueprint
conversations_bp = Blueprint('conversations', __name__)

#used to format the conversation data for the user
def format_conversation(conversation, username):
    participants = conversation["conversation_id"].split("_")
    other_user = participants[0] if participants[1] == username else participants[1]
    #returns the appended conversation details - 
                                                #the conversation ID
                                                #the other participants username
                                                #the list of messages in the conversation
    return {
        "conversation_id": conversation["conversation_id"],
        "with_user": other_user,
        "messages": [
            {
                "sender": msg["sender"],
                "message": msg["message"],
                "timestamp": msg["timestamp"].isoformat()
            } for msg in conversation["messages"]
        ]
    }

#route to get all conversations for a user using the endpoint /conversations
@conversations_bp.route('/conversations', methods=['GET'])
def get_user_conversations():
    #gets the authorization token from the request headers
    token = request.headers.get('Authorization')
    if not token:
        
        return jsonify({"error": "Authorization token is required"}), 401 #401 (Unauthorized)

    #validates the token
    user = get_user(token)
    if not user:
        return jsonify({"error": "Invalid token"}), 401 #401 (Unauthorized)

    #fetch the conversations where the user is involved
    #by using regex on the conversation_id (because the conversation_id is a combination of the two users)
    username = user["username"]
    conversations_cursor = db["conversations"].find({
        "conversation_id": {"$regex": f"^{username}_|_{username}$"}
    })

    #format the conversations for the user
    user_conversations = [
        format_conversation(conversation, username)
        for conversation in conversations_cursor
    ]

    # Return the list of user conversations
    return jsonify(user_conversations), 200
