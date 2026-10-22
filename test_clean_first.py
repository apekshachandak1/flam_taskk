#!/usr/bin/env python3
"""Test the clean-first approach on test cases."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils import normalize_text, remove_html, remove_urls, remove_boilerplate
from pii_masker import redact_pii
from language_detector import detect_language

def process_test_case(line_num, doc):
    """Process a single test document and show step-by-step cleaning."""
    doc_id = f"test_line{line_num}"
    source = doc.get("meta", {}).get("source", "unknown")
    original = doc.get("text", "")
    
    print(f"\n{'='*80}")
    print(f"Test Case {line_num}: {source}")
    print(f"{'='*80}")
    print(f"ORIGINAL:\n{original[:200]}{'...' if len(original) > 200 else ''}\n")
    
    # Step 1: Normalize
    text = normalize_text(original)
    print(f"After NORMALIZE:\n{text[:200]}{'...' if len(text) > 200 else ''}\n")
    
    # Step 2: Remove HTML
    text = remove_html(text)
    print(f"After REMOVE HTML:\n{text[:200]}{'...' if len(text) > 200 else ''}\n")
    
    # Step 3: Remove URLs
    text, url_count = remove_urls(text)
    print(f"After REMOVE URLs ({url_count} removed):\n{text[:200]}{'...' if len(text) > 200 else ''}\n")
    
    # Step 4: Remove boilerplate
    text = remove_boilerplate(text)
    print(f"After REMOVE BOILERPLATE:\n{text[:200]}{'...' if len(text) > 200 else ''}\n")
    
    # Step 5: Redact PII
    text, pii_found = redact_pii(text)
    print(f"After REDACT PII ({len(pii_found)} items):\n{text[:200]}{'...' if len(text) > 200 else ''}\n")
    
    # Step 6: Check if meaningful text remains
    cleaned_check = text.strip()
    word_count = len(cleaned_check.split())
    char_count = len(cleaned_check)
    
    print(f"FINAL STATS:")
    print(f"  - Characters: {char_count}")
    print(f"  - Words: {word_count}")
    
    # Decision
    if char_count < 20 or word_count < 3:
        print(f"  - DECISION: ❌ DROP (too short after cleaning)")
        return None
    else:
        # Detect language
        lang = detect_language(text)
        print(f"  - Language: {lang}")
        print(f"  - DECISION: ✅ KEEP")
        return {
            "id": doc_id,
            "text": text,
            "lang": lang,
            "source": source,
            "original_length": len(original),
            "cleaned_length": len(text),
            "urls_removed": url_count,
            "pii_redacted": len(pii_found)
        }

def main():
    """Run test on all test cases."""
    test_file = Path("data/raw/test_cases.jsonl")
    
    if not test_file.exists():
        print(f"Error: {test_file} not found")
        return
    
    print("="*80)
    print("TESTING CLEAN-FIRST APPROACH")
    print("="*80)
    
    kept = []
    dropped = []
    
    with open(test_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                doc = json.loads(line.strip())
                result = process_test_case(line_num, doc)
                
                if result:
                    kept.append(result)
                else:
                    dropped.append(line_num)
                    
            except Exception as e:
                print(f"ERROR processing line {line_num}: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total test cases: {line_num}")
    print(f"Kept: {len(kept)}")
    print(f"Dropped: {len(dropped)}")
    
    if kept:
        print("\n✅ KEPT DOCUMENTS:")
        for doc in kept:
            print(f"  - {doc['id']}: {doc['source']}")
            print(f"    Text: {doc['text'][:80]}...")
            print(f"    Length: {doc['original_length']} → {doc['cleaned_length']}")
            print()
    
    if dropped:
        print(f"\n❌ DROPPED DOCUMENTS (lines): {dropped}")

if __name__ == "__main__":
    main()
