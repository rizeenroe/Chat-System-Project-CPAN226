import React, { useState, useEffect } from "react";
import io from "socket.io-client";

//connecting to the backend
const socket = io("http://localhost:5000");

function App() {
  const[username, setUsername] = useState("");
  const[recipient, setRecipient] = useState("");
  const[room, setRoom] = useState("");
  const[message, setMessage] = useState("");
  const[messages, setMessages] = useState([]);

  const joinChat = () => {
    if(username.trim() && room.trim()){
      socket.emit("join", {username, room});
    }
  }

  useEffect(() => {
    //listen for messages from the server
    socket.on("message", (msg) => {
      //append new to message to the messages array
      setMessages((prev) => [...prev, msg])
    });

    return () => {
      socket.off("message");
    };
  }, []);

  const sendMessage = () => {
    if(recipient.trim() && message.trim()){
      socket.emit("private_message", {
        sender: username,
        recipient,
        message,
      });
      setMessage("");
    }
  };

  return(
    <div>
      <h2>Simple Chat</h2>
      <div>
        <input
          type="text"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => {
            setUsername(e.target.value); 
            setRecipient(e.target.value)
          }}
        />
        <input
          type="text"
          placeholder="Enter room ID"
          value={room}
          onChange={(e) => setRoom(e.target.value)}
        />
        <button onClick={joinChat}>Join Chat</button>
      </div>

      {/* <div>
        <input
          type="text"
          placeholder="Recipient username"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
        />
      </div> */}

      <div>
        {messages.map((msg, index) => (
          <p key={index}>{msg}</p>
        ))}
      </div>

      <div>
        <input
          type="text"
          placeholder="Type a message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button onClick={sendMessage}>Send</button>
      </div>

    </div>
  );

}
export default App;