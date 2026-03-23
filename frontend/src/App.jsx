import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GraphCanvas from './components/GraphCanvas';
import ChatPanel from './components/ChatPanel';
import './index.css';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  useEffect(() => {
    axios.get('http://localhost:8000/graph')
      .then(res => {
        setGraphData(res.data);
      })
      .catch(err => {
        console.error("Failed to load graph:", err);
      });
  }, []);

  return (
    <div className="app-container">
      <GraphCanvas graphData={graphData} />
      <ChatPanel />
    </div>
  );
}

export default App;
