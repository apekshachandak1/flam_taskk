#!/usr/bin/env python3
"""Extract parquet file to readable JSON."""

import pandas as pd
import json

parquet_file = "data/output/clean/clean.parquet"
json_output = "data/output/clean/clean_from_parquet.jsonl"

print("\n" + "="*80)
print("EXTRACTING PARQUET FILE")
print("="*80 + "\n")

print(f"Input:  {parquet_file}")
print(f"Output: {json_output}\n")

# Read parquet
df = pd.read_parquet(parquet_file)

print(f"✓ Loaded {len(df)} documents\n")

# Display info
print("Columns:", list(df.columns))
print(f"\nFirst 3 IDs:")
for i, row in df.head(3).iterrows():
    print(f"  - {row['id']}")

# Write to JSON
with open(json_output, 'w', encoding='utf-8') as f:
    for _, row in df.iterrows():
        doc = row.to_dict()
        json.dump(doc, f, ensure_ascii=False)
        f.write('\n')

print(f"\n✓ Extracted to: {json_output}")

# Show first 3 examples
print("\n" + "="*80)
print("FIRST 3 EXAMPLES")
print("="*80 + "\n")

for i, (_, row) in enumerate(df.head(3).iterrows(), 1):
    print(f"Document {i}:")
    print(f"  ID:     {row['id']}")
    print(f"  Lang:   {row['lang']}")
    print(f"  Source: {row['source']}")
    print(f"  Text:   {row['text'][:100]}{'...' if len(row['text']) > 100 else ''}")
    print()

print("="*80 + "\n")
