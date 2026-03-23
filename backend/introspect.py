import os
import pandas as pd
import json

base_dir = "sap-o2c-data"
schema = {}

for root, _, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.jsonl'):
            table_name = os.path.basename(root)
            path = os.path.join(root, f)
            with open(path, 'r') as file:
                first_line = file.readline()
                if first_line:
                    data = json.loads(first_line)
                    if table_name not in schema:
                        schema[table_name] = list(data.keys())

with open("schema.json", "w") as out:
    json.dump(schema, out, indent=2)
print("Schema written to schema.json")
