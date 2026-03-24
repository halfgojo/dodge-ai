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
        height: '100vh', background: '#f7f9fc', color: '#4a90d9', fontSize: '1rem',
        fontFamily: 'Inter, sans-serif', flexDirection: 'column', gap: '12px'
      }}>
        <div style={{ display: 'flex', gap: '5px' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#4a90d9', animation: 'bounce 1.4s ease-in-out infinite' }} />
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#4a90d9', animation: 'bounce 1.4s ease-in-out 0.16s infinite' }} />
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#4a90d9', animation: 'bounce 1.4s ease-in-out 0.32s infinite' }} />
        </div>
        Loading Graph...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: '#f7f9fc', color: '#e06060', fontSize: '0.95rem',
        fontFamily: 'Inter, sans-serif', flexDirection: 'column', gap: '10px', padding: '40px'
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
