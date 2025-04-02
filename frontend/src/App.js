import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Chat from './chat/Chat';
import { useState } from 'react';

function App() {
  const [user, setUser] = useState(null);

  return (
    <Router>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/chat" /> : <Login setUser={setUser} />} />
        <Route path="/chat" element={user ? <Chat user={user} /> : <Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;