#!/usr/bin/env python3
"""Quick search - simplified version."""

import json

# Load files
print("Loading...")
ledger = {}
with open('data/output/ledger.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        entry = json.loads(line)
        ledger[entry['id']] = entry

clean_docs = {}
with open('data/output/clean/clean.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line)
        clean_docs[doc['id']] = doc

print(f"✓ Loaded {len(ledger)} ledger | {len(clean_docs)} clean\n")

# Show examples
print("="*80)
print("AVAILABLE IDS (First 10 kept + First 10 dropped)")
print("="*80 + "\n")

kept = [id for id, e in ledger.items() if e['status'] == 'kept'][:10]
dropped = [id for id, e in ledger.items() if e['status'] == 'dropped'][:10]

print("✅ KEPT:")
for doc_id in kept:
    print(f"   {doc_id}")

print("\n❌ DROPPED:")
for doc_id in dropped:
    reason = ledger[doc_id]['reason']
    print(f"   {doc_id} - {reason}")

print("\n" + "="*80)
print("\nUSAGE:")
print("  python search_by_id.py <ID>        # Direct search")
print("  python search_by_id.py             # Interactive mode")
print("\nExample:")
print(f"  python search_by_id.py {kept[0]}")
print()
