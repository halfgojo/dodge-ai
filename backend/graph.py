import sqlite3
import networkx as nx
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sqlite.db")

def build_graph():
    """Builds a NetworkX directed graph from the SQLite database."""
    G = nx.DiGraph()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    def query(sql):
        try:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"  SQL Error: {e}")
            return []

    # --- Customers ---
    print("Loading Customers...")
    for row in query("SELECT businessPartner, customer, businessPartnerFullName, businessPartnerCategory FROM business_partners"):
        cid = str(row['customer'] or row['businessPartner'])
        G.add_node(f"CUST-{cid}", type="Customer", label=row['businessPartnerFullName'] or f"Customer {cid}", raw=row)

    # --- Products ---
    print("Loading Products...")
    for row in query("""
        SELECT p.product, pd.productDescription, p.productType, p.productGroup, p.baseUnit, p.division
        FROM products p
        LEFT JOIN product_descriptions pd ON p.product = pd.product AND pd.language = 'EN'
    """):
        pid = str(row['product'])
        desc = row['productDescription'] or f"Product {pid}"
        G.add_node(f"PROD-{pid}", type="Product", label=desc, raw=row)

    # --- Sales Orders ---
    print("Loading Sales Orders...")
    for row in query("SELECT salesOrder, soldToParty, totalNetAmount, transactionCurrency, creationDate, overallDeliveryStatus, overallOrdReltdBillgStatus FROM sales_order_headers"):
        so_id = str(row['salesOrder'])
        G.add_node(f"SO-{so_id}", type="SalesOrder", label=f"SO {so_id}", raw=row)
        customer_id = str(row['soldToParty'])
        if customer_id and f"CUST-{customer_id}" in G:
            G.add_edge(f"CUST-{customer_id}", f"SO-{so_id}", label="PLACED")

    # --- Sales Order Items -> Product edges ---
    print("Loading Sales Order Items...")
    for row in query("SELECT salesOrder, salesOrderItem, material, netAmount, requestedQuantity FROM sales_order_items"):
        so_id = str(row['salesOrder'])
        mat_id = str(row['material'])
        item_id = f"SOI-{so_id}-{row['salesOrderItem']}"
        G.add_node(item_id, type="SalesOrderItem", label=f"Item {row['salesOrderItem']}", raw=row)
        G.add_edge(f"SO-{so_id}", item_id, label="CONTAINS")
        if mat_id and f"PROD-{mat_id}" in G:
            G.add_edge(item_id, f"PROD-{mat_id}", label="REFERENCES")

    # --- Deliveries ---
    print("Loading Deliveries...")
    for row in query("SELECT deliveryDocument, creationDate, overallGoodsMovementStatus, overallPickingStatus, shippingPoint FROM outbound_delivery_headers"):
        del_id = str(row['deliveryDocument'])
        G.add_node(f"DEL-{del_id}", type="Delivery", label=f"Del {del_id}", raw=row)
    
    # Map SO -> Delivery from delivery items
    for row in query("SELECT DISTINCT deliveryDocument, referenceSdDocument FROM outbound_delivery_items"):
        del_id = str(row['deliveryDocument'])
        so_id = str(row['referenceSdDocument'])
        if so_id and del_id and f"SO-{so_id}" in G and f"DEL-{del_id}" in G:
            G.add_edge(f"SO-{so_id}", f"DEL-{del_id}", label="FULFILLED_BY")
            
    # --- Billing / Invoices ---
    print("Loading Billing Documents...")
    for row in query("SELECT billingDocument, billingDocumentType, totalNetAmount, transactionCurrency, creationDate, billingDocumentIsCancelled, soldToParty, companyCode, fiscalYear, accountingDocument FROM billing_document_headers"):
        inv_id = str(row['billingDocument'])
        G.add_node(f"INV-{inv_id}", type="Invoice", label=f"Inv {inv_id}", raw=row)
        
    # Map Delivery -> Invoice from billing items
    for row in query("SELECT DISTINCT billingDocument, referenceSdDocument FROM billing_document_items"):
        inv_id = str(row['billingDocument'])
        ref_id = str(row['referenceSdDocument'])
        if inv_id and ref_id:
            if f"DEL-{ref_id}" in G:
                G.add_edge(f"DEL-{ref_id}", f"INV-{inv_id}", label="TRIGGERS")
            elif f"SO-{ref_id}" in G:
                G.add_edge(f"SO-{ref_id}", f"INV-{inv_id}", label="BILLED_FROM")
            
    # --- Journal Entries ---
    print("Loading Journal Entries...")
    seen_je = set()
    for row in query("SELECT accountingDocument, companyCode, fiscalYear, referenceDocument, glAccount, amountInCompanyCodeCurrency, postingDate, customer FROM journal_entry_items_accounts_receivable"):
        je_id = str(row['accountingDocument'])
        if je_id not in seen_je:
            G.add_node(f"JE-{je_id}", type="JournalEntry", label=f"JE {je_id}", raw=row)
            seen_je.add(je_id)
        ref_id = str(row['referenceDocument'])
        if ref_id and f"INV-{ref_id}" in G:
            G.add_edge(f"INV-{ref_id}", f"JE-{je_id}", label="RECORDED_IN")

    # --- Payments ---
    print("Loading Payments...")
    seen_pay = set()
    for row in query("SELECT accountingDocument, customer, amountInTransactionCurrency, transactionCurrency, postingDate, invoiceReference FROM payments_accounts_receivable"):
        pay_id = str(row['accountingDocument'])
        if pay_id not in seen_pay:
            G.add_node(f"PAY-{pay_id}", type="Payment", label=f"Pay {pay_id}", raw=row)
            seen_pay.add(pay_id)
        inv_ref = str(row['invoiceReference'])
        if inv_ref and f"INV-{inv_ref}" in G:
            G.add_edge(f"INV-{inv_ref}", f"PAY-{pay_id}", label="SETTLED_BY")

    conn.close()
    
    print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def get_graph_data(G):
    """Formats the NetworkX graph for React Force Graph 2D."""
    nodes = []
    links = []
    
    for node, data in G.nodes(data=True):
        clean_data = data.copy()
        raw = clean_data.pop("raw", {})
        merged = {**clean_data, **raw}
        merged["id"] = node
        nodes.append(merged)
        
    for source, target, data in G.edges(data=True):
        links.append({
            "source": source,
            "target": target,
            "label": data.get("label", "")
        })
        
    return {"nodes": nodes, "links": links}

if __name__ == "__main__":
    G = build_graph()
