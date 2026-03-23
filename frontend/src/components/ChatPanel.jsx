import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';
import axios from 'axios';

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! I can help you analyze the Order to Cash process.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  const scrollToBottom = () => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/chat', { message: userMsg });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: 'Error: Could not connect to the backend API.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-pane">
      <div className="chat-header">
        <h2><Bot size={20} color="#58a6ff" /> Dodge AI</h2>
        <p>Graph Agent - Order to Cash</p>
      </div>
      
      <div className="chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-msg ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="chat-msg bot loading">
            Dodge AI is analyzing...
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSend}>
        <input 
          type="text" 
          className="chat-input"
          placeholder="Analyze anything..."
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
