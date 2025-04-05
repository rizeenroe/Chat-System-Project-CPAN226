import { useState, useEffect, useRef, useMemo } from "react";
import io from "socket.io-client";
import ChatHeader from "../ChatHeader/ChatHeader";
import ChatContent from "../ChatContent/ChatContent";
import config from "../../Config";
import "./Chat.css";

export default function Chat({ user }) {
  const [state, setState] = useState({
    messages: [],
    input: "",
    activeTab: "room",
    target: "",
    currentRoom: "",
    conversations: user.conversations || [],
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
    const initialMessages = [];
    state.conversations.forEach((conversation) => {
      if (conversation.messages) {
        initialMessages.push(
          ...conversation.messages.map((msg) => ({
            ...msg,
            type: msg.sender === user.username ? "direct-out" : "direct",
            recipient: conversation.with_user,
          }))
        );
      }
    });

    setState((prev) => ({
      ...prev,
      messages: initialMessages,
    }));
  }, [state.conversations, user.username]);

  useEffect(() => {
    socketRef.current = io(config.BASE_URL, {
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
      setState((prev) => {
        const existingConversation = prev.conversations.find(
          (conv) => conv.with_user === data.sender
        );

        const updatedConversations = existingConversation
          ? prev.conversations.map((conv) =>
              conv.with_user === data.sender
                ? {
                    ...conv,
                    messages: [
                      ...conv.messages,
                      {
                        type: "direct",
                        sender: data.sender,
                        recipient: user.username,
                        message: data.message,
                        timestamp: new Date(
                          data.timestamp
                        ).toLocaleTimeString(),
                      },
                    ],
                  }
                : conv
            )
          : [
              ...prev.conversations,
              {
                with_user: data.sender,
                messages: [
                  {
                    type: "direct",
                    sender: data.sender,
                    recipient: user.username,
                    message: data.message,
                    timestamp: new Date(data.timestamp).toLocaleTimeString(),
                  },
                ],
              },
            ];

        return {
          ...prev,
          conversations: updatedConversations,
        };
      });

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
  }, [user.token, user.username]);

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
      socketRef.current.emit("join", { room: state.roomInput });
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

    if (state.activeTab === "direct") {
      addMessage(newMessage);

      setState((prev) => {
        const existingConversation = prev.conversations.find(
          (conv) => conv.with_user === state.target
        );

        const updatedConversations = existingConversation
          ? prev.conversations.map((conv) =>
              conv.with_user === state.target
                ? {
                    ...conv,
                    messages: [...conv.messages, newMessage],
                  }
                : conv
            )
          : [
              ...prev.conversations,
              {
                with_user: state.target,
                messages: [newMessage],
              },
            ];

        return {
          ...prev,
          conversations: updatedConversations,
          input: "",
        };
      });
    } else {
      setState((prev) => ({ ...prev, input: "" }));
    }

    if (state.activeTab === "room") {
      socketRef.current.emit("room_message", { message: state.input });
      setState((prev) => ({ ...prev, input: "" }));
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
      if (state.activeTab === "room") {
        return msg.type === "room" || msg.type === "room-out";
      }
      if (state.activeTab === "direct") {
        return (
          (msg.type === "direct" && msg.sender === state.target) ||
          (msg.type === "direct-out" && msg.recipient === state.target)
        );
      }
      return false;
    });
  }, [state.messages, state.activeTab, state.target]);

  return (
    <div className="chat-container">
      <ChatHeader user={user} state={state} setState={setState} />
      <ChatContent
        state={state}
        setState={setState}
        filteredMessages={filteredMessages}
        messagesEndRef={messagesEndRef}
        joinRoom={joinRoom}
        sendMessage={sendMessage}
        handleKeyPress={handleKeyPress}
      />
    </div>
  );
}