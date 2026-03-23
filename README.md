# Order-to-Cash AI Graph Query System

## Overview
This project unifies a fragmented Order-to-Cash dataset (Sales Orders, Deliveries, Invoices, Journal Entries) into an interconnected context graph system with a Google Gemini LLM-powered conversational interface. Users can explore the graph visually or ask complex, multi-hop natural language questions that are dynamically compiled to SQL, executed, and synthesized as grounded answers.

## Architecture Decisions
- **Backend:** FastAPI (Python) was chosen for its asynchronous performance, automatic payload validation via Pydantic, and fast integration.
- **Frontend:** React + Vite provides a fast, modern component-based UI. `react-force-graph-2d` handles the graph visualization, offering performant canvas rendering for hundreds of nodes and smooth physics simulations.
- **Data Ingestion:** A Python pipeline reads the distributed JSONL files, serializes nested structures, and normalizes them into a SQLite database. NetworkX serves as the in-memory graph builder mapping foreign-keys to explicit edges.

## Database Choice (SQLite + NetworkX)
Rather than introducing the operational complexity of a dedicated Graph Database like Neo4j, this system uses **SQLite** for durable structured querying and **NetworkX** for in-memory graph generation. 
- **Tradeoffs:** SQLite is highly portable, requires zero setup, and is excellent for LLM-generated SQL due to its widely understood SQL dialect. While Neo4j allows native Cypher graph-traversals, SQLite combined with standard SQL JOINs easily resolves the flow tracing required for this assigned dataset.

## LLM Prompting Strategy (Gemini)
The architecture uses a two-step "Retrieve & Summarize" prompting pattern:
1. **NL -> SQL:** The LLM is provided with a strict schema definition and explicit contextual mapping rules (e.g., how to detect "broken flows"). It strictly generates a SQL query targeting the SQLite DB.
2. **SQL Results -> NL:** After local execution, the raw JSON results are piped back into Gemini, instructing it to synthesize the extracted records into a natural language response. This ensures responses remain 100% grounded in accurate reporting data.

## Guardrails
To prevent misuse, arbitrary knowledge retrieval, and prompt injection:
- The SQL generator system prompt explicitly commands: "If the user's question is fundamentally not about this dataset or asks general knowledge questions, return exactly: GUARDRAIL: off-topic".
- The backend intercepts this deterministic output syntax. If the guardrail tripwire is hit, it short-circuits the SQL compilation process and safely returns the fallback: *"This system is designed to answer questions related to the provided dataset only."*
