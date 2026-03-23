import sqlite3
import networkx as nx

DB_PATH = "sqlite.db"

def build_graph():
    """Builds a NetworkX directed graph from the SQLite database."""
    G = nx.DiGraph()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # helper
    def query(sql):
        try:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    print("Loading Customers...")
    for row in query("SELECT businessPartner, customer, businessPartnerFullName FROM business_partners LIMIT 100"):
        cid = str(row['customer'])
        G.add_node(f"CUST-{cid}", type="Customer", label=row['businessPartnerFullName'] or cid, raw=row)

    print("Loading Sales Orders...")
    for row in query("SELECT salesOrder, soldToParty, totalNetAmount, transactionCurrency, creationDate FROM sales_order_headers LIMIT 200"):
        so_id = str(row['salesOrder'])
        G.add_node(f"SO-{so_id}", type="SalesOrder", label=f"Order {so_id}", raw=row)
        customer_id = str(row['soldToParty'])
        if customer_id:
            G.add_edge(f"CUST-{customer_id}", f"SO-{so_id}", label="PLACED")

    print("Loading Deliveries...")
    for row in query("SELECT deliveryDocument, creationDate, overallGoodsMovementStatus FROM outbound_delivery_headers LIMIT 200"):
        del_id = str(row['deliveryDocument'])
        G.add_node(f"DEL-{del_id}", type="Delivery", label=f"Del {del_id}", raw=row)
    
    # Map SO -> Delivery from outbound_delivery_items
    for row in query("SELECT deliveryDocument, referenceSdDocument FROM outbound_delivery_items LIMIT 500"):
        del_id = str(row['deliveryDocument'])
        so_id = str(row['referenceSdDocument'])
        if so_id and del_id:
            G.add_edge(f"SO-{so_id}", f"DEL-{del_id}", label="FULFILLED_BY")
            
    print("Loading Invoices...")
    for row in query("SELECT billingDocument, totalNetAmount, transactionCurrency, creationDate FROM billing_document_headers LIMIT 200"):
        inv_id = str(row['billingDocument'])
        G.add_node(f"INV-{inv_id}", type="Invoice", label=f"Inv {inv_id}", raw=row)
        
    # Map Delivery -> Invoice from billing_document_items
    for row in query("SELECT billingDocument, referenceSdDocument FROM billing_document_items LIMIT 500"):
        inv_id = str(row['billingDocument'])
        del_id = str(row['referenceSdDocument']) # which might be the delivery doc
        if inv_id and del_id:
            G.add_edge(f"DEL-{del_id}", f"INV-{inv_id}", label="TRIGGERS")
            
    print("Loading Journal Entries...")
    for row in query("SELECT accountingDocument, referenceDocument, amountInCompanyCodeCurrency, postingDate FROM journal_entry_items_accounts_receivable LIMIT 200"):
        je_id = str(row['accountingDocument'])
        G.add_node(f"JE-{je_id}", type="JournalEntry", label=f"JE {je_id}", raw=row)
        inv_id = str(row['referenceDocument']) # Usually maps to billing document
        if inv_id and je_id:
            G.add_edge(f"INV-{inv_id}", f"JE-{je_id}", label="RECORDED_IN")

    conn.close()
    
    # Post-process: Remove nodes with 0 degree to keep UI clean if desired, or keep all.
    # isolated = list(nx.isolates(G))
    # G.remove_nodes_from(isolated)
    
    return G

def get_graph_data(G):
    """Formats the NetworkX graph for React Force Graph 2D."""
    nodes = []
    links = []
    
    for node, data in G.nodes(data=True):
        clean_data = data.copy()
        raw = clean_data.pop("raw", {})
        # Merge properties to root
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
    print(f"Graph constructed with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
