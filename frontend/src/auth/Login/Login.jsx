import { useState } from "react";
import config from "../../Config";
import "./Login.css";

export default function Login({ setUser }) {
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${config.BASE_URL}${config.AUTH_LOGIN}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();
      if (response.ok) {
        const conversationsResponse = await fetch(
          `${config.BASE_URL}${config.API_CONVERSATIONS}`,
          {
            method: "GET",
            headers: {
              Authorization: data.token,
            },
          }
        );

        const conversations = await conversationsResponse.json();
        if (conversationsResponse.ok) {
          setUser({
            username: credentials.username,
            token: data.token,
            conversations: conversations,
          });
        } else {
          setError("Failed to fetch conversations");
        }
      } else {
        setError(data.error || "Login failed");
      }
    } catch (err) {
      setError("Connection error");
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin} className="login-form">
        <input
          type="text"
          placeholder="Username"
          value={credentials.username}
          onChange={(e) =>
            setCredentials({ ...credentials, username: e.target.value })
          }
          className="login-input"
        />
        <input
          type="password"
          placeholder="Password"
          value={credentials.password}
          onChange={(e) =>
            setCredentials({ ...credentials, password: e.target.value })
          }
          className="login-input"
        />
        <button type="submit" className="login-button">
          Login
        </button>
        {error && <p className="login-error">{error}</p>}
      </form>
    </div>
  );
}
