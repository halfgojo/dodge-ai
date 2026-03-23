from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import graph
import llm_agent

app = FastAPI(title="Order-to-Cash AI Query API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

G = graph.build_graph()
graph_data = graph.get_graph_data(G)

@app.get("/graph")
def get_graph():
    return graph_data

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        reply = llm_agent.process_query(req.message)
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"An error occurred: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
