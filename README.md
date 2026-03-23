# Dodge AI — Order-to-Cash Context Graph System

An AI-powered graph exploration and query system that unifies fragmented SAP Order-to-Cash data into an interactive knowledge graph with natural language querying via Google Gemini.

![Tech Stack](https://img.shields.io/badge/Backend-FastAPI-green) ![Frontend](https://img.shields.io/badge/Frontend-React%20+%20Vite-blue) ![LLM](https://img.shields.io/badge/LLM-Google%20Gemini-orange) ![DB](https://img.shields.io/badge/Database-SQLite-lightgrey)

## Features
- **Interactive Graph Visualization** — Force-directed graph with 700+ nodes representing Customers, Sales Orders, Deliveries, Invoices, Journal Entries, Payments, and Products
- **LLM-Powered Natural Language Queries** — Ask questions in plain English, get SQL-grounded answers
- **Smart Guardrails** — Off-topic queries are cleanly rejected
- **Node Inspector** — Click any node to see full metadata and connection count
- **Suggested Queries** — Pre-built query templates to get started quickly

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐
│   React + Vite  │────▶│  FastAPI      │────▶│  SQLite DB    │
│   Force Graph   │◀────│  Python       │◀────│  (19 tables)  │
│   Chat Panel    │     │  NetworkX     │     │               │
└─────────────────┘     └──────┬───────┘     └───────────────┘
                               │
                        ┌──────▼───────┐
                        │ Google Gemini│
                        │ (NL → SQL)   │
                        └──────────────┘
```

### LLM Prompting Strategy
The system uses a **two-step Retrieve & Summarize** pattern:
1. **NL → SQL**: Gemini receives the full database schema (all 19 tables with columns and relationship mappings) and generates a valid SQLite query. If the query fails, it retries once with error context.
2. **SQL Results → NL**: Raw query results are sent back to Gemini for natural language summarization, ensuring all answers are 100% grounded in real data.

### Database Choice: SQLite + NetworkX
- **SQLite**: Zero-setup, portable, well-understood SQL dialect (ideal for LLM-generated queries)
- **NetworkX**: In-memory graph for visualization — maps foreign keys to semantic edges
- **Tradeoff**: Neo4j would enable native graph traversals but adds deployment complexity and cost

### Guardrails
- System prompt instructs the LLM to return `GUARDRAIL: off-topic` for non-dataset questions
- Backend intercepts this token and returns a clean rejection message
- Only `SELECT` queries are permitted — mutations are blocked at the application layer

## Project Structure
```
dodge-ai/
├── backend/
│   ├── main.py              # FastAPI app with /graph, /chat, /health endpoints
│   ├── database.py          # SQLite init and query execution
│   ├── graph.py             # NetworkX graph construction
│   ├── llm_agent.py         # Gemini NL-to-SQL pipeline with guardrails
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main app with loading/error states
│   │   ├── main.jsx          # React entry point
│   │   ├── index.css         # Premium dark theme CSS
│   │   └── components/
│   │       ├── GraphCanvas.jsx  # Force graph with custom canvas rendering
│   │       └── ChatPanel.jsx    # Chat interface with suggested queries
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example
├── .gitignore
└── README.md
```

## Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key ([Get one free](https://ai.google.dev))

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download the dataset
pip install gdown
gdown 1UqaLbFaveV-3MEuiUrzKydhKmkeC1iAL
unzip sap-order-to-cash-dataset.zip

# Set your API key
export GEMINI_API_KEY="your_key_here"

# Start the server
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** to use the application.

## Example Queries
| Query | What it tests |
|-------|---------------|
| "Which products have the most billing documents?" | Multi-table JOIN + aggregation |
| "Trace the full flow of billing document 91150187" | End-to-end O2C flow trace |
| "Find sales orders that were delivered but not billed" | Broken flow detection (LEFT JOIN) |
| "What is the total revenue by customer?" | Aggregation across entities |
| "Tell me a joke" | Guardrail rejection |
