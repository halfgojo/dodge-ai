import os
import json
import re
import requests
import database

# Support multiple LLM providers
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Determine which provider to use
LLM_PROVIDER = None
if GROQ_API_KEY:
    LLM_PROVIDER = "groq"
elif GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        LLM_PROVIDER = "gemini"
    except ImportError:
        pass

print(f"LLM Provider: {LLM_PROVIDER or 'NONE (set GROQ_API_KEY or GEMINI_API_KEY)'}")

# Cache the schema string (built lazily)
_cached_schema = None

def _build_schema_string():
    global _cached_schema
    if _cached_schema:
        return _cached_schema
    try:
        schema = database.get_schema()
        lines = []
        for table, cols in schema.items():
            lines.append(f"- {table} ({', '.join(cols)})")
        _cached_schema = "\n".join(lines)
        return _cached_schema
    except Exception:
        return "(schema unavailable)"

def _get_sql_system_prompt():
    return f"""You are a SQL expert for an SAP Order-to-Cash (O2C) SQLite database.

DATABASE SCHEMA (all available tables and their columns):
{_build_schema_string()}

KEY RELATIONSHIPS (foreign key mappings):
- sales_order_headers.soldToParty -> business_partners.customer
- sales_order_items.salesOrder -> sales_order_headers.salesOrder  
- sales_order_items.material -> products.product
- outbound_delivery_items.referenceSdDocument -> sales_order_headers.salesOrder
- outbound_delivery_items.deliveryDocument -> outbound_delivery_headers.deliveryDocument
- billing_document_items.referenceSdDocument -> outbound_delivery_headers.deliveryDocument
- billing_document_items.billingDocument -> billing_document_headers.billingDocument
- journal_entry_items_accounts_receivable.referenceDocument -> billing_document_headers.billingDocument
- payments_accounts_receivable.invoiceReference -> billing_document_headers.billingDocument
- product_descriptions.product -> products.product

FLOW: Sales Order -> Delivery -> Billing Document -> Journal Entry / Payment

BROKEN FLOWS:
- "Delivered but not billed": SO has delivery but no billing
- "Billed without delivery": SO has billing but no delivery
- "Unpaid": Billing exists but no payment

RULES:
1. Return ONLY a valid SQLite SQL query. No markdown, no explanations, no code fences.
2. If NOT about this dataset, return exactly: GUARDRAIL: off-topic
3. If the user is asking a follow-up question that can be answered using the conversation history (like "explain these" or "why"), return exactly: FOLLOWUP
4. Use LEFT JOINs for broken flow detection.
5. DO NOT join header tables directly to each other! You MUST join through the items tables (e.g. sales_order_items, outbound_delivery_items, billing_document_items) using the reference document columns.
6. Use DISTINCT when joining through items tables to avoid duplicates.
7. Limit results to 50 rows unless asked for more.
8. For product names, JOIN product_descriptions WHERE language = 'EN'.
"""

SUMMARY_SYSTEM_PROMPT = """You are a data analyst presenting results from an SAP Order-to-Cash database.
Answer clearly using ONLY the provided data. Format numbers/dates nicely. Use bullet points.
CRITICAL: If there is a long sequential list of IDs (e.g., sales orders, deliveries), you MUST condense them into a range (e.g., '740506 to 740555') instead of listing every single one.
Do NOT fabricate data. Do NOT show raw SQL or JSON."""


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Call Groq API (OpenAI-compatible)."""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Call Gemini API."""
    import google.generativeai as genai
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=system_prompt,
        generation_config={"temperature": 0.0, "max_output_tokens": 4096},
    )
    response = model.generate_content(user_prompt)
    return response.text.strip()


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Route to the active LLM provider."""
    if LLM_PROVIDER == "groq":
        return _call_groq(system_prompt, user_prompt)
    elif LLM_PROVIDER == "gemini":
        return _call_gemini(system_prompt, user_prompt)
    else:
        raise RuntimeError("No LLM provider configured")


def generate_sql(query: str, history_context: str = "") -> str:
    prompt = _get_sql_system_prompt()
    if history_context:
        prompt += f"\n\nCONVERSATION HISTORY:\n{history_context}"
        
    sql = _call_llm(prompt, query)
    sql = re.sub(r'^```(?:sql)?\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    return sql.strip()


def summarize_results(query: str, sql: str, results: list) -> str:
    result_str = json.dumps(results[:50], indent=2, default=str)
    prompt = f"""User Question: {query}

SQL Query Used: {sql}
Query Results ({len(results)} rows, showing up to 50):
{result_str}

Summarize these results in a clear, helpful natural language answer."""
    return _call_llm(SUMMARY_SYSTEM_PROMPT, prompt)


def process_query(query: str, history: list = None) -> str:
    if not LLM_PROVIDER:
        return "⚠️ No LLM configured. Set GROQ_API_KEY (free at console.groq.com) or GEMINI_API_KEY (free at ai.google.dev)."

    history_context = ""
    if history:
        # Take up to last 4 messages for context
        recent = history[-4:]
        history_context = "\n".join([f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in recent])

    try:
        sql = generate_sql(query, history_context)
    except Exception as e:
        return f"Sorry, I had trouble understanding your question. Error: {str(e)}"

    if "FOLLOWUP" in sql.upper() and history_context:
        prompt = f"Previous Conversation:\n{history_context}\n\nNew User Question: {query}\n\nAnswer the user's question clearly based on the previous conversation data."
        return _call_llm(SUMMARY_SYSTEM_PROMPT, prompt)

    if "GUARDRAIL" in sql.upper():
        return "🚫 This system answers questions about the Order-to-Cash dataset only. Ask about sales orders, deliveries, billing, payments, or products."

    if not sql.strip().upper().startswith("SELECT"):
        return "🚫 I can only run read-only queries on the dataset."

    results = database.run_query(sql)

    if isinstance(results, dict) and "error" in results:
        retry_prompt = f"The SQL query failed with error: {results['error']}. Original question: {query}. Generate a corrected SQL query."
        try:
            sql = generate_sql(retry_prompt, history_context)
            if "GUARDRAIL" in sql.upper() or not sql.strip().upper().startswith("SELECT"):
                return "Sorry, I couldn't generate a valid query for your question."
            results = database.run_query(sql)
            if isinstance(results, dict) and "error" in results:
                return f"Sorry, persistent database error: {results['error']}"
        except Exception:
            return "Sorry, I couldn't process your question."

    if not results:
        return "The query returned no results. Try rephrasing your question."

    try:
        return summarize_results(query, sql, results)
    except Exception:
        return f"Here are the raw results:\n{json.dumps(results[:10], indent=2, default=str)}"
