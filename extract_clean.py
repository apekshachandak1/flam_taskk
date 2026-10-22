#!/usr/bin/env python3
"""Extract clean.jsonl.gz to readable JSON file."""

import gzip
import json
import shutil

input_file = "data/output/clean/clean.jsonl.gz"
output_file = "data/output/clean/clean.jsonl"

print("\n" + "="*80)
print("EXTRACTING CLEAN OUTPUT")
print("="*80 + "\n")

print(f"Input:  {input_file}")
print(f"Output: {output_file}\n")

# Extract gzip file
with gzip.open(input_file, 'rb') as f_in:
    with open(output_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

# Count lines
with open(output_file, 'r', encoding='utf-8') as f:
    line_count = sum(1 for _ in f)

print(f"✓ Extracted {line_count} documents")
print(f"✓ Saved to: {output_file}")

# Show first 3 examples
print("\n" + "="*80)
print("FIRST 3 EXAMPLES")
print("="*80 + "\n")

with open(output_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if i > 3:
            break
        doc = json.loads(line)
        print(f"Document {i}:")
        print(f"  ID:     {doc['id']}")
        print(f"  Lang:   {doc['lang']}")
        print(f"  Source: {doc['source']}")
        print(f"  Text:   {doc['text'][:100]}{'...' if len(doc['text']) > 100 else ''}")
        print()

print("="*80)
print("\nDone! You can now view: data/output/clean/clean.jsonl\n")
