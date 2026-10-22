#!/usr/bin/env python3
"""Process 1000-line sample and create proper output structure."""

import sys
import os
import shutil
from pathlib import Path

# Create temporary input directory with samples
sample_input = Path("data/raw_sample")
sample_input.mkdir(exist_ok=True)

# Copy 1000-line samples
shutil.copy("data/raw/hindi_1000.jsonl", sample_input / "hindi.jsonl")
shutil.copy("data/raw/hinglish_1000.jsonl", sample_input / "hinglish.jsonl")

print("\n" + "="*80)
print("PROCESSING 1000-LINE SAMPLE")
print("="*80 + "\n")

# Import and run pipeline
sys.path.insert(0, 'src')
from main import process_pipeline

# Run on sample
process_pipeline(str(sample_input), "data/output")

# Create sample_1000.jsonl from clean output
print("\nCreating sample_1000.jsonl...")
import gzip
import json
import random

with gzip.open("data/output/clean/clean.jsonl.gz", 'rt', encoding='utf-8') as f:
    all_clean = [json.loads(line) for line in f]

# Take up to 1000 random samples
sample_size = min(1000, len(all_clean))
sample_docs = random.sample(all_clean, sample_size) if len(all_clean) > 1000 else all_clean

with open("data/output/sample_1000.jsonl", 'w', encoding='utf-8') as f:
    for doc in sample_docs:
        json.dump(doc, f, ensure_ascii=False)
        f.write('\n')

print(f"✓ Created sample_1000.jsonl with {len(sample_docs)} documents")

# Cleanup
shutil.rmtree(sample_input)

print("\n" + "="*80)
print("SAMPLE PROCESSING COMPLETE")
print("="*80)
print("\nOutput structure:")
print("data/output/")
print("  ├── clean/")
print("  │   └── clean.jsonl.gz")
print("  ├── ledger.jsonl")
print("  ├── eval.jsonl")
print("  ├── contamination.jsonl")
print("  ├── manifest.json")
print("  └── sample_1000.jsonl")
print()
