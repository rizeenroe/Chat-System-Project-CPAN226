import { useState, useEffect, useRef, useMemo } from "react";
import io from "socket.io-client";
import "./Chat.css";

export default function Chat({ user }) {
  const [state, setState] = useState({
    messages: [],
    input: "",
    activeTab: "room",
    target: "",
    currentRoom: "",
    unreadMessages: {},
    conversations: new Set(),
    roomInput: "",
  });

  const socketRef = useRef();
  const messagesEndRef = useRef(null);

  const activeTabRef = useRef(state.activeTab);
  const targetRef = useRef(state.target);

  useEffect(() => {
    activeTabRef.current = state.activeTab;
    targetRef.current = state.target;
  }, [state.activeTab, state.target]);

  useEffect(() => {
    socketRef.current = io("http://localhost:5000", {
      query: { token: user.token },
    });

    const handleSocketEvents = (event, handler) => {
      socketRef.current.on(event, handler);
    };

    handleSocketEvents("system_message", (data) => {
      addMessage({
        type: "system",
        sender: data.username || "System",
        message: data.message,
        timestamp: new Date(data.timestamp).toLocaleTimeString(),
      });
    });

    handleSocketEvents("room_message", (data) => {
      addMessage({
        type: "room",
        sender: data.sender,
        message: data.message,
        timestamp: new Date(data.timestamp).toLocaleTimeString(),
      });
    });

    handleSocketEvents("private_message", (data) => {
      const isActiveDirect =
        activeTabRef.current === "direct" && targetRef.current === data.sender;

      if (!isActiveDirect) {
        setState((prev) => ({
          ...prev,
          unreadMessages: {
            ...prev.unreadMessages,
            [data.sender]: (prev.unreadMessages[data.sender] || 0) + 1,
          },
        }));
      }

      setState((prev) => ({
        ...prev,
        conversations: new Set([...prev.conversations, data.sender]),
      }));

      addMessage({
        type: "direct",
        sender: data.sender,
        recipient: user.username,
        message: data.message,
        timestamp: new Date(data.timestamp).toLocaleTimeString(),
      });
    });

    handleSocketEvents("joined_room", (data) => {
      setState((prev) => ({
        ...prev,
        currentRoom: data.room,
      }));
      addMessage({
        type: "system",
        sender: "System",
        message: `You joined room: ${data.room}`,
        timestamp: new Date().toLocaleTimeString(),
      });
    });

    handleSocketEvents("error", (error) => {
      addMessage({
        type: "system",
        sender: "System",
        message: `Error: ${error.message}`,
        timestamp: new Date().toLocaleTimeString(),
      });
    });

    return () => {
      socketRef.current.disconnect();
    };
  }, [user.token]);

  const addMessage = (message) => {
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, message],
    }));
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [state.messages]);

  const joinRoom = () => {
    if (state.roomInput) {
      socketRef.current.emit("join_room", { room: state.roomInput });
      setState((prev) => ({ ...prev, roomInput: "" }));
    }
  };

  const sendMessage = () => {
    if (!state.input.trim()) return;

    const newMessage = {
      type: state.activeTab === "room" ? "room-out" : "direct-out",
      sender: user.username,
      recipient: state.target,
      message: state.input,
      timestamp: new Date().toLocaleTimeString(),
    };

    addMessage(newMessage);
    setState((prev) => ({ ...prev, input: "" }));

    if (state.activeTab === "room") {
      socketRef.current.emit("room_message", { message: state.input });
    } else {
      socketRef.current.emit("private_message", {
        recipient: state.target,
        message: state.input,
      });
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      if (state.activeTab === "room" && !state.currentRoom && state.roomInput) {
        joinRoom();
      } else {
        sendMessage();
      }
    }
  };

  const filteredMessages = useMemo(() => {
    return state.messages.filter((msg) => {
      if (state.activeTab === "room") return msg.type !== "direct";
      return (
        (msg.type === "direct" && msg.sender === state.target) ||
        (msg.type === "direct-out" && msg.recipient === state.target)
      );
    });
  }, [state.messages, state.activeTab, state.target]);

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h2>Welcome, {user.username}</h2>
        <div className="chat-tabs">
          <button
            className={`tab-button ${
              state.activeTab === "room" ? "active-tab" : ""
            }`}
            onClick={() => setState((prev) => ({ ...prev, activeTab: "room" }))}
          >
            Room Chat
          </button>
          <button
            className={`tab-button ${
              state.activeTab === "direct" ? "active-tab" : ""
            }`}
            onClick={() =>
              setState((prev) => ({ ...prev, activeTab: "direct" }))
            }
          >
            Direct Messages
            {Object.keys(state.unreadMessages).length > 0 && (
              <span className="unread-counter">
                {Object.values(state.unreadMessages).reduce((a, b) => a + b, 0)}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="chat-content">
        {/* Sidebar */}
        {state.activeTab === "direct" && (
          <div className="conversation-sidebar">
            <div className="new-conversation">
              <input
                type="text"
                placeholder="Enter username"
                value={state.target}
                onChange={(e) =>
                  setState((prev) => ({ ...prev, target: e.target.value }))
                }
                onKeyPress={handleKeyPress}
                className="input"
              />
              <button
                onClick={() =>
                  setState((prev) => ({
                    ...prev,
                    conversations: new Set([
                      ...prev.conversations,
                      state.target,
                    ]),
                    activeTab: "direct",
                  }))
                }
                className="small-button"
              >
                New Chat
              </button>
            </div>
            <h3>Conversations</h3>
            {Array.from(state.conversations).map((username) => (
              <div
                key={username}
                className={`conversation-item ${
                  state.target === username ? "active-conversation" : ""
                }`}
                onClick={() =>
                  setState((prev) => ({
                    ...prev,
                    target: username,
                    activeTab: "direct",
                    unreadMessages: {
                      ...prev.unreadMessages,
                      [username]: 0,
                    },
                  }))
                }
              >
                {username}
                {state.unreadMessages[username] > 0 && (
                  <span className="unread-badge">
                    {state.unreadMessages[username]}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Chat Area */}
        <div className="chat-area">
          {state.activeTab === "room" && !state.currentRoom && (
            <div className="room-join">
              <h3>Join a Room</h3>
              <div className="room-input-container">
                <input
                  type="text"
                  placeholder="Enter room name"
                  value={state.roomInput}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, roomInput: e.target.value }))
                  }
                  onKeyPress={handleKeyPress}
                  className="input"
                />
                <button onClick={joinRoom} className="button">
                  Join
                </button>
              </div>
            </div>
          )}

          {((state.activeTab === "room" && state.currentRoom) ||
            (state.activeTab === "direct" && state.target)) && (
            <>
              <div className="messages">
                {filteredMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`message ${
                      msg.type === "direct"
                        ? "direct-message"
                        : msg.type === "direct-out"
                        ? "direct-out-message"
                        : msg.type === "room-out"
                        ? "room-out-message"
                        : msg.type === "system"
                        ? "system-message"
                        : ""
                    }`}
                  >
                    <div className="message-header">
                      <strong>
                        {msg.type === "direct-out" || msg.type === "room-out"
                          ? "You"
                          : msg.sender}
                      </strong>
                      <span className="timestamp">{msg.timestamp}</span>
                    </div>
                    <div>{msg.message}</div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div className="input-area">
                <input
                  value={state.input}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, input: e.target.value }))
                  }
                  placeholder={
                    state.activeTab === "room"
                      ? `Message room ${state.currentRoom}`
                      : `Message ${state.target}`
                  }
                  onKeyPress={handleKeyPress}
                  className="message-input"
                />
                <button
                  onClick={sendMessage}
                  className="send-button"
                  disabled={!state.input.trim()}
                >
                  Send
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
