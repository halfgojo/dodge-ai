import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SUGGESTED_QUERIES = [
  "Which products have the most billing documents?",
  "Find sales orders with broken flows",
  "Trace the full flow of billing document 91150187",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! I can help you analyze the **Order to Cash** process.\n\nTry asking about sales orders, deliveries, billing documents, or broken flows.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendQuery = async (text) => {
    if (!text.trim() || loading) return;
    
    const userMsg = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, { message: userMsg });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: '⚠️ Could not connect to the backend. Make sure the API server is running on port 8000.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  return (
    <div className="chat-pane">
      <div className="chat-header">
        <div className="chat-header-top">
          <div className="chat-avatar">
            <Bot size={22} color="#fff" />
          </div>
          <div>
            <h2>Dodge AI</h2>
            <p className="subtitle"><span className="status-dot" />Graph Agent</p>
          </div>
        </div>
      </div>
      
      <div className="chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-msg ${msg.role}`}>
            {msg.text}
          </div>
        ))}

        {/* Show suggested queries only at start */}
        {messages.length === 1 && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {SUGGESTED_QUERIES.map((q, i) => (
              <button key={i} onClick={() => sendQuery(q)} style={{
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                color: '#818cf8',
                padding: '10px 14px',
                borderRadius: '10px',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '0.85rem',
                lineHeight: '1.4',
                transition: 'all 0.2s',
                fontFamily: 'inherit',
              }}
              onMouseEnter={e => { e.target.style.background = 'rgba(99, 102, 241, 0.15)'; }}
              onMouseLeave={e => { e.target.style.background = 'rgba(99, 102, 241, 0.08)'; }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {loading && (
          <div className="chat-msg bot loading">
            <div className="typing-dots">
              <span /><span /><span />
            </div>
            Analyzing...
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSend}>
        <input 
          type="text" 
          className="chat-input"
          placeholder="Ask about orders, deliveries, billing..."
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="chat-btn" disabled={!input.trim() || loading}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
