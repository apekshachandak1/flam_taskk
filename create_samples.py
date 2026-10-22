#!/usr/bin/env python3
"""Create 1000-row random sample from cleaned output."""

import json
import random
from pathlib import Path

def create_sample():
    """Create random 1000-row sample from clean output."""
    
    clean_file = Path("data/output/clean/clean_from_parquet.jsonl")
    sample_file = Path("data/output/clean_sample_1000.jsonl")
    
    if not clean_file.exists():
        print(f"Error: {clean_file} not found")
        return
    
    # Read all documents
    print(f"Reading {clean_file}...")
    documents = []
    with open(clean_file, 'r', encoding='utf-8') as f:
        for line in f:
            documents.append(line.strip())
    
    total = len(documents)
    print(f"Total documents: {total}")
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Sample 1000 random documents
    sample_size = min(1000, total)
    sample_docs = random.sample(documents, sample_size)
    
    # Write sample
    print(f"Creating sample of {sample_size} documents...")
    with open(sample_file, 'w', encoding='utf-8') as f:
        for doc in sample_docs:
            f.write(doc + '\n')
    
    print(f"✓ Sample created: {sample_file}")
    print(f"  Sample size: {sample_size} documents")
    
    # Show first 3 examples
    print("\nFirst 3 examples from sample:")
    for i, doc in enumerate(sample_docs[:3], 1):
        data = json.loads(doc)
        print(f"\n{i}. ID: {data['id']}")
        print(f"   Lang: {data['lang']}")
        print(f"   Text: {data['text'][:80]}...")

if __name__ == "__main__":
    create_sample()
