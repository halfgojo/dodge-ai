import os
import json
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

SQL_SYSTEM_PROMPT = """
You are a SQL expert for an Order-to-Cash database. 
You are querying a SQLite database with the following core schema:

- sales_order_headers (salesOrder, soldToParty, totalNetAmount, transactionCurrency, creationDate)
- sales_order_items (salesOrder, salesOrderItem, material)
- outbound_delivery_headers (deliveryDocument, creationDate)
- outbound_delivery_items (deliveryDocument, referenceSdDocument) -> referenceSdDocument maps to sales_order_headers.salesOrder
- billing_document_headers (billingDocument, creationDate, totalNetAmount)
- billing_document_items (billingDocument, referenceSdDocument) -> referenceSdDocument usually maps to outbound_delivery_headers.deliveryDocument
- journal_entry_items_accounts_receivable (accountingDocument, referenceDocument, amountInCompanyCodeCurrency) -> referenceDocument usually maps to billing_document_headers.billingDocument
- business_partners (customer, businessPartnerFullName)
- products (product) -> material in sales_order_items maps to product

Rules:
1. Return ONLY a valid SQL query, nothing else (no markdown blocks, no explanations).
2. If the user's question is fundamentally not about this dataset or asks general knowledge questions, return exactly: GUARDRAIL: off-topic
3. Flow traces are: Sales Order -> Delivery -> Billing -> Journal Entry.
4. Broken delivery: Sales without delivery
5. Broken billing: Delivery without billing.
"""

SUMMARY_SYSTEM_PROMPT = """
You are an intelligent data analyst summarizing database results for a user.
Given the user's question and the SQL results (as a list of JSON records),
write a helpful, natural language answer. Do not show the raw SQL. Just answer the question clearly using the data.
"""

def generate_sql(query: str) -> str:
    model = genai.GenerativeModel('gemini-2.5-flash',
                                  system_instruction=SQL_SYSTEM_PROMPT,
                                  generation_config=generation_config)
    response = model.generate_content(query)
    sql = response.text.strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    if sql.endswith("```"):
        sql = sql[:-3]
    return sql.strip()

def summarize_results(query: str, sql: str, results: list) -> str:
    prompt = f"User Question: {query}\n\nSQL Results:\n{json.dumps(results[:50], indent=2)}\n\nPlease summarize the results in natural language."
    model = genai.GenerativeModel('gemini-2.5-flash',
                                  system_instruction=SUMMARY_SYSTEM_PROMPT,
                                  generation_config=generation_config)
    response = model.generate_content(prompt)
    return response.text.strip()

def process_query(query: str) -> str:
    if not api_key:
        return "LLM integration is currently unavailable. Please provide a GEMINI_API_KEY."

    sql = generate_sql(query)
    
    if sql.startswith("GUARDRAIL: off-topic"):
        return "This system is designed to answer questions related to the provided dataset only."
        
    results = database.run_query(sql)
    
    if isinstance(results, dict) and "error" in results:
        return f"Sorry, I encountered an error running the database query: {results['error']} | Generated SQL: {sql}"
        
    if not results:
        return "The query returned no results from the database."
        
    answer = summarize_results(query, sql, results)
    return answer
