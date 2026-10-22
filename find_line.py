#!/usr/bin/env python3
"""Find document by line number from input files."""

import json
import sys

def find_by_line(filename, line_num):
    """Find document by file and line number."""
    
    # Construct ID
    doc_id = f"{filename}_line{line_num}"
    
    print("\n" + "="*80)
    print(f"SEARCHING: {filename}.jsonl - Line {line_num}")
    print(f"ID: {doc_id}")
    print("="*80 + "\n")
    
    # 1. Get INPUT from raw file
    input_file = f"data/raw/{filename}.jsonl"
    print(f"📥 INPUT (Line {line_num} from {filename}.jsonl)")
    print("-" * 80)
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i == line_num:
                    doc = json.loads(line)
                    print(f"Text: {doc.get('text', 'N/A')}")
                    break
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    
    # 2. Get LEDGER decision
    print(f"\n📋 LEDGER DECISION")
    print("-" * 80)
    ledger_found = False
    with open('data/output/ledger.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            if entry['id'] == doc_id:
                print(f"Status:   {entry['status']}", end="")
                if entry['status'] == 'kept':
                    print(" ✅")
                else:
                    print(" ❌")
                print(f"Stage:    {entry['stage']}")
                print(f"Reason:   {entry['reason']}")
                if entry.get('pii_masked'):
                    print(f"PII:      {entry['pii_masked']}")
                if entry.get('language'):
                    print(f"Language: {entry['language']}")
                if entry.get('dup_of'):
                    print(f"Dup Of:   {entry['dup_of']}")
                ledger_found = True
                kept = entry['status'] == 'kept'
                break
    
    if not ledger_found:
        print(f"❌ Not found in ledger")
        return
    
    # 3. Get OUTPUT (if kept)
    if kept:
        print(f"\n📤 OUTPUT (clean.jsonl)")
        print("-" * 80)
        with open('data/output/clean/clean.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                doc = json.loads(line)
                if doc['id'] == doc_id:
                    print(f"Text: {doc['text']}")
                    break
    else:
        print(f"\n❌ NOT IN OUTPUT (Document was dropped)")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nUsage: python find_line.py <filename> <line_number>")
        print("\nExamples:")
        print("  python find_line.py hindi_1000 2      # Line 2 from hindi_1000.jsonl")
        print("  python find_line.py hinglish_1000 5   # Line 5 from hinglish_1000.jsonl")
        print()
    else:
        filename = sys.argv[1]
        line_num = int(sys.argv[2])
        find_by_line(filename, line_num)
