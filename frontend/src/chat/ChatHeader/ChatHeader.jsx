import "./ChatHeader.css";

export default function ChatHeader({ user, state, setState }) {
  return (
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
        </button>
      </div>
    </div>
  );
}