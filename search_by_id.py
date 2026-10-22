#!/usr/bin/env python3
"""Search document by ID and compare INPUT vs OUTPUT."""

import json
import sys

def load_files():
    """Load all necessary files."""
    print("Loading files...")
    
    # Load raw inputs
    raw_docs = {}
    for filename in ['data/raw/hindi_1000.jsonl', 'data/raw/hinglish_1000.jsonl']:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    doc = json.loads(line)
                    # Store with source prefix
                    source = filename.split('/')[-1].replace('_1000.jsonl', '')
                    doc_id = f"mc4_{source}_{doc.get('id', 'unknown')}"
                    raw_docs[doc_id] = doc
        except FileNotFoundError:
            pass
    
    # Load ledger
    ledger = {}
    with open('data/output/ledger.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            ledger[entry['id']] = entry
    
    # Load clean output
    clean_docs = {}
    with open('data/output/clean/clean.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            clean_docs[doc['id']] = doc
    
    print(f"✓ Loaded {len(raw_docs)} raw documents")
    print(f"✓ Loaded {len(ledger)} ledger entries")
    print(f"✓ Loaded {len(clean_docs)} clean documents\n")
    
    return raw_docs, ledger, clean_docs


def search_by_id(doc_id, raw_docs, ledger, clean_docs):
    """Search and display document by ID."""
    
    print("="*80)
    print(f"SEARCHING FOR ID: {doc_id}")
    print("="*80 + "\n")
    
    # Check ledger first
    if doc_id not in ledger:
        print(f"❌ ID '{doc_id}' not found in ledger!")
        print("\nAvailable IDs (first 10):")
        for i, lid in enumerate(list(ledger.keys())[:10]):
            print(f"  - {lid}")
        return
    
    ledger_entry = ledger[doc_id]
    
    # Display INPUT
    print("📥 INPUT (Raw Document)")
    print("-" * 80)
    if doc_id in raw_docs:
        raw_doc = raw_docs[doc_id]
        print(f"ID:     {raw_doc.get('id', 'N/A')}")
        print(f"Source: {raw_doc.get('source', 'N/A')}")
        print(f"Text:   {raw_doc.get('text', 'N/A')}")
    else:
        print("⚠️  Raw document not found (might be from different source)")
    
    # Display LEDGER DECISION
    print("\n📋 LEDGER DECISION")
    print("-" * 80)
    print(f"ID:       {ledger_entry['id']}")
    print(f"Status:   {ledger_entry['status']}", end="")
    if ledger_entry['status'] == 'kept':
        print(" ✅")
    else:
        print(" ❌")
    print(f"Stage:    {ledger_entry['stage']}")
    print(f"Reason:   {ledger_entry['reason']}")
    if ledger_entry.get('dup_of'):
        print(f"Dup Of:   {ledger_entry['dup_of']}")
    if ledger_entry.get('pii_masked'):
        print(f"PII:      {ledger_entry['pii_masked']}")
    if ledger_entry.get('language'):
        print(f"Language: {ledger_entry['language']}")
    
    # Display OUTPUT (if kept)
    if ledger_entry['status'] == 'kept':
        print("\n📤 OUTPUT (Clean Document)")
        print("-" * 80)
        if doc_id in clean_docs:
            clean_doc = clean_docs[doc_id]
            print(f"ID:     {clean_doc['id']}")
            print(f"Lang:   {clean_doc['lang']}")
            print(f"Source: {clean_doc['source']}")
            print(f"Text:   {clean_doc['text']}")
        else:
            print("⚠️  Document should be in clean output but not found!")
    else:
        print("\n❌ OUTPUT")
        print("-" * 80)
        print("Document was DROPPED and not in final output")
    
    print("\n" + "="*80 + "\n")


def interactive_search(raw_docs, ledger, clean_docs):
    """Interactive search mode."""
    print("\n" + "="*80)
    print("INTERACTIVE SEARCH MODE")
    print("="*80)
    print("\nCommands:")
    print("  - Enter ID to search (e.g., mc4_hi_5)")
    print("  - Type 'list' to see available IDs")
    print("  - Type 'exit' to quit")
    print()
    
    while True:
        query = input("Search ID: ").strip()
        
        if query.lower() == 'exit':
            print("Goodbye!")
            break
        
        elif query.lower() == 'list':
            print("\nAvailable IDs (first 20):")
            for i, doc_id in enumerate(list(ledger.keys())[:20]):
                status = "✅" if ledger[doc_id]['status'] == 'kept' else "❌"
                print(f"  {status} {doc_id}")
            print()
        
        elif query:
            search_by_id(query, raw_docs, ledger, clean_docs)
        else:
            print("Please enter an ID\n")


if __name__ == "__main__":
    raw_docs, ledger, clean_docs = load_files()
    
    # If ID provided as argument, search directly
    if len(sys.argv) > 1:
        doc_id = sys.argv[1]
        search_by_id(doc_id, raw_docs, ledger, clean_docs)
    else:
        # Interactive mode
        interactive_search(raw_docs, ledger, clean_docs)
