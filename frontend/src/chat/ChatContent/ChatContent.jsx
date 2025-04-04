import "./ChatContent.css";

export default function ChatContent({
  state,
  setState,
  filteredMessages,
  messagesEndRef,
  joinRoom,
  sendMessage,
  handleKeyPress,
}) {
  return (
    <div className="chat-content">
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
              onClick={() => {
                if (state.target.trim()) {
                  setState((prev) => ({
                    ...prev,
                    conversations: [
                      ...prev.conversations.filter(
                        (conv) => conv.with_user !== state.target
                      ),
                      { with_user: state.target, messages: [] },
                    ],
                    target: state.target,
                  }));
                }
              }}
              className="small-button"
            >
              New Chat
            </button>
          </div>
          <h3>Conversations</h3>
          {state.conversations.map((conversation) => (
            <div
              key={conversation.with_user}
              className={`conversation-item ${
                state.target === conversation.with_user
                  ? "active-conversation"
                  : ""
              }`}
              onClick={() =>
                setState((prev) => ({
                  ...prev,
                  target: conversation.with_user,
                }))
              }
            >
              {conversation.with_user}
            </div>
          ))}
        </div>
      )}

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
  );
}