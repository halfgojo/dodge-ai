import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database
import graph as graph_module
import llm_agent

# Auto-initialize SQLite DB on startup
database.init_db()

app = FastAPI(title="Dodge AI — Order-to-Cash Query API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build graph at startup
G = graph_module.build_graph()
graph_data = graph_module.get_graph_data(G)

@app.get("/health")
def health_check():
    return {"status": "ok", "nodes": G.number_of_nodes(), "edges": G.number_of_edges()}

@app.get("/graph")
def get_graph():
    return graph_data

@app.get("/graph/stats")
def get_graph_stats():
    """Returns summary statistics about the graph."""
    type_counts = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": type_counts,
    }

from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    reply: str
    status: str = "success"

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        reply = llm_agent.process_query(req.message, req.history)
        return ChatResponse(reply=reply)
    except Exception as e:
        return ChatResponse(reply=f"An error occurred: {str(e)}", status="error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
