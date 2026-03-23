import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GraphCanvas from './components/GraphCanvas';
import ChatPanel from './components/ChatPanel';
import './index.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/graph`)
      .then(res => {
        setGraphData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load graph:", err);
        setError("Could not connect to backend. Ensure the API is running on port 8000.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', alignItems: 'center', justifyContent: 'center', 
        height: '100vh', background: '#0a0e17', color: '#6366f1', fontSize: '1.1rem',
        fontFamily: 'Inter, sans-serif', flexDirection: 'column', gap: '16px'
      }}>
        <div className="typing-dots" style={{ display: 'flex', gap: '6px' }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#6366f1', animation: 'bounce 1.4s ease-in-out infinite' }} />
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#6366f1', animation: 'bounce 1.4s ease-in-out 0.16s infinite' }} />
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#6366f1', animation: 'bounce 1.4s ease-in-out 0.32s infinite' }} />
        </div>
        Loading Graph...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: '#0a0e17', color: '#ef4444', fontSize: '1rem',
        fontFamily: 'Inter, sans-serif', flexDirection: 'column', gap: '12px', padding: '40px'
      }}>
        <span style={{ fontSize: '2rem' }}>⚠️</span>
        {error}
      </div>
    );
  }

  return (
    <div className="app-container">
      <GraphCanvas graphData={graphData} />
      <ChatPanel />
    </div>
  );
}

export default App;
