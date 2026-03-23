import os
import json
import re
import google.generativeai as genai
import database

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Cache the schema string (built lazily on first query)
_cached_schema = None

def _build_schema_string():
    """Reads the live SQLite schema and formats it for the LLM prompt."""
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
- sales_order_headers.soldToParty -> business_partners.customer (Customer who placed the order)
- sales_order_items.salesOrder -> sales_order_headers.salesOrder  
- sales_order_items.material -> products.product (Product/Material reference)
- outbound_delivery_items.referenceSdDocument -> sales_order_headers.salesOrder (Delivery links to Sales Order)
- outbound_delivery_items.deliveryDocument -> outbound_delivery_headers.deliveryDocument
- billing_document_items.referenceSdDocument -> outbound_delivery_headers.deliveryDocument (Billing links to Delivery)
- billing_document_items.billingDocument -> billing_document_headers.billingDocument
- billing_document_headers.accountingDocument -> journal_entry_items_accounts_receivable.accountingDocument (Billing links to Journal Entry)
- journal_entry_items_accounts_receivable.referenceDocument -> billing_document_headers.billingDocument
- payments_accounts_receivable.invoiceReference -> billing_document_headers.billingDocument (Payment links to Billing)
- product_descriptions.product -> products.product (Product name/description)
- billing_document_cancellations contains cancelled billing documents

FLOW TRACE (Order-to-Cash pipeline):
Sales Order -> Delivery -> Billing Document -> Journal Entry
                                            -> Payment

BROKEN FLOW DEFINITIONS:
- "Delivered but not billed": Sales order has a delivery but no billing document
- "Billed without delivery": Sales order has billing but no delivery  
- "No journal entry": Billing exists but no corresponding journal entry
- "Unpaid": Billing exists but no corresponding payment

RULES:
1. Return ONLY a valid SQLite SQL query. No markdown, no explanations, no code fences.
2. If the user's question is NOT about this dataset (e.g. general knowledge, creative writing, jokes, politics, weather, math problems unrelated to the data), return exactly: GUARDRAIL: off-topic
3. Use LEFT JOINs for broken flow detection.
4. Use DISTINCT when joining through items tables to avoid duplicates.
5. Limit results to 50 rows unless the user asks for more.
6. For product names, JOIN with product_descriptions WHERE language = 'EN'.
"""

SUMMARY_SYSTEM_PROMPT = """You are a data analyst presenting results from an SAP Order-to-Cash database.

Rules:
1. Answer the user's question clearly using ONLY the provided data.
2. Format numbers and dates nicely.
3. If the data contains IDs, mention them so the user can cross-reference.
4. Keep answers concise but thorough. Use bullet points or numbered lists for clarity.
5. Do NOT fabricate any data not present in the results.
6. Do NOT show raw SQL or JSON.
"""

def generate_sql(query: str) -> str:
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=_get_sql_system_prompt(),
        generation_config=generation_config
    )
    response = model.generate_content(query)
    sql = response.text.strip()
    # Strip markdown code fences if LLM wraps them anyway
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

    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=SUMMARY_SYSTEM_PROMPT,
        generation_config=generation_config
    )
    response = model.generate_content(prompt)
    return response.text.strip()

def process_query(query: str) -> str:
    if not api_key:
        return "⚠️ LLM integration is unavailable. Please set the GEMINI_API_KEY environment variable."

    try:
        sql = generate_sql(query)
    except Exception as e:
        return f"Sorry, I had trouble understanding your question. Error: {str(e)}"
    
    # Guardrail check
    if "GUARDRAIL" in sql.upper():
        return "🚫 This system is designed to answer questions related to the Order-to-Cash dataset only. Please ask about sales orders, deliveries, billing documents, payments, products, or journal entries."
    
    # Safety: only allow SELECT
    if not sql.strip().upper().startswith("SELECT"):
        return "🚫 I can only run read-only queries on the dataset."
        
    results = database.run_query(sql)
    
    if isinstance(results, dict) and "error" in results:
        # Retry once with error context
        retry_prompt = f"The previous SQL query failed with error: {results['error']}. Original question: {query}. Please generate a corrected SQL query."
        try:
            sql = generate_sql(retry_prompt)
            if "GUARDRAIL" in sql.upper() or not sql.strip().upper().startswith("SELECT"):
                return "Sorry, I couldn't generate a valid query for your question."
            results = database.run_query(sql)
            if isinstance(results, dict) and "error" in results:
                return f"Sorry, I encountered a persistent database error: {results['error']}"
        except Exception:
            return "Sorry, I couldn't process your question."
        
    if not results:
        return "The query returned no results from the database. Try rephrasing your question."
    
    try:
        answer = summarize_results(query, sql, results)
        return answer
    except Exception as e:
        # Fallback: return raw data if summarization fails
        return f"Here are the raw results:\n{json.dumps(results[:10], indent=2, default=str)}"
