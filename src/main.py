"""Main pipeline for cleaning Hindi/Hinglish corpus."""
import sys
import os
import json
import hashlib
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd
from tqdm import tqdm
import random

from language_detector import LanguageDetector
from pii_masker import PIIMasker
from deduplicator import Deduplicator
from contamination import ContaminationChecker
from utils import normalize_text, compute_hash, is_spam, read_jsonl_stream, write_jsonl


def process_pipeline(input_dir: str, output_dir: str):
    """Main data cleaning pipeline."""
    
    # Setup
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directories
    (output_path / "clean").mkdir(parents=True, exist_ok=True)
    
    # Output files
    ledger_file = output_path / "ledger.jsonl"
    clean_file = output_path / "clean" / "clean.parquet"
    eval_file = output_path / "eval.jsonl"
    contamination_file = output_path / "contamination.jsonl"
    manifest_file = output_path / "manifest.json"
    
    # Clear previous outputs
    for f in [ledger_file, eval_file, contamination_file]:
        if f.exists():
            f.unlink()
    
    # Initialize components
    print("Loading language detector...")
    lang_detector = LanguageDetector()
    pii_masker = PIIMasker()
    deduplicator = Deduplicator(threshold=0.85)
    
    # Statistics
    stats = defaultdict(lambda: defaultdict(int))
    source_files = {}
    
    # Store for eval set (hold out 200 docs)
    eval_candidates = []
    
    # Store clean documents
    clean_documents = []
    contaminated_train_ids = set()
    
    # Find all JSONL files
    jsonl_files = list(input_path.glob("*.jsonl"))
    if not jsonl_files:
        print(f"Error: No .jsonl files found in {input_dir}")
        sys.exit(1)
    
    print(f"\nFound {len(jsonl_files)} input file(s)")
    for f in jsonl_files:
        print(f"  - {f.name}")
    
    # Compute input file hashes
    for jsonl_file in jsonl_files:
        with open(jsonl_file, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            source_files[jsonl_file.name] = file_hash
    
    print("\n" + "="*60)
    print("Starting pipeline processing...")
    print("="*60 + "\n")
    
    # Process all files
    for jsonl_file in jsonl_files:
        print(f"\nProcessing {jsonl_file.name}...")
        
        # Get filename without extension for source prefix
        file_prefix = jsonl_file.stem  # e.g., "hindi_1000" or "hinglish_1000"
        line_number = 0
        
        for doc in tqdm(read_jsonl_stream(str(jsonl_file)), desc=f"  Reading"):
            line_number += 1
            
            # Use LINE NUMBER as ID with file prefix
            doc_id = f"{file_prefix}_line{line_number}"
            
            # Extract text and source
            if isinstance(doc, dict):
                text = doc.get('text', '')
                source = doc.get('source', file_prefix)
            else:
                text = str(doc)
                source = file_prefix
            
            stats['input']['total'] += 1
            stats['by_source'][source] += 1
            
            # Skip empty
            if not text or len(text.strip()) < 5:
                write_jsonl(ledger_file, {
                    'id': doc_id,
                    'status': 'dropped',
                    'stage': 'input',
                    'reason': 'empty',
                    'dup_of': None,
                    'text_preview': text[:100] if text else ''
                })
                stats['dropped']['empty'] += 1
                continue
            
            # Step 1: Normalize
            normalized = normalize_text(text)
            if not normalized:
                write_jsonl(ledger_file, {
                    'id': doc_id,
                    'status': 'dropped',
                    'stage': 'normalize',
                    'reason': 'normalization_failed',
                    'dup_of': None
                })
                stats['dropped']['normalization_failed'] += 1
                continue
            
            # Track cleaning operations
            cleaning_report = []
            
            # Step 2: CLEAN-FIRST approach - Remove noise but keep content
            from utils import remove_html_tags, remove_urls, remove_boilerplate
            
            # Count what we're removing
            html_count = len(re.findall(r'<[^>]+>', normalized))
            url_count = len(re.findall(r'https?://[^\s]+|www\.[^\s]+', normalized))
            
            # Remove HTML tags
            if html_count > 0:
                normalized = remove_html_tags(normalized)
                cleaning_report.append(f'html_removed:{html_count}')
            
            # Remove URLs (keep meaningful text)
            if url_count > 0:
                normalized = remove_urls(normalized)
                cleaning_report.append(f'urls_removed:{url_count}')
            
            # Remove boilerplate
            before_boilerplate = len(normalized)
            normalized = remove_boilerplate(normalized)
            after_boilerplate = len(normalized)
            if before_boilerplate != after_boilerplate:
                cleaning_report.append('boilerplate_removed')
            
            # Check if meaningful text remains (LENIENT threshold)
            if not normalized or len(normalized.strip()) < 5:  # Very low threshold
                write_jsonl(ledger_file, {
                    'id': doc_id,
                    'status': 'dropped',
                    'stage': 'cleanup',
                    'reason': 'empty_after_cleanup',
                    'dup_of': None,
                    'cleaning': '|'.join(cleaning_report) if cleaning_report else None
                })
                stats['dropped']['empty_after_cleanup'] += 1
                continue
            
            # Step 3: Language detection (after cleaning)
            lang = lang_detector.detect(normalized)
            stats['language'][lang] += 1
            
            # We keep hi, hi-Latn, en (as mentioned in assignment)
            if lang not in ['hi', 'hi-Latn', 'en']:
                write_jsonl(ledger_file, {
                    'id': doc_id,
                    'status': 'dropped',
                    'stage': 'language',
                    'reason': f'unwanted_language_{lang}',
                    'dup_of': None
                })
                stats['dropped']['wrong_language'] += 1
                continue
            
            # Step 5: Spam filter (ONLY genuine spam - after all cleaning)
            is_spam_doc, spam_reason = is_spam(normalized)
            if is_spam_doc:
                write_jsonl(ledger_file, {
                    'id': doc_id,
                    'status': 'dropped',
                    'stage': 'spam_filter',
                    'reason': spam_reason,
                    'dup_of': None,
                    'cleaning': '|'.join(cleaning_report) if cleaning_report else None,
                    'text_preview': normalized[:150]
                })
                stats['dropped']['spam'] += 1
                continue
            
            # Step 6: PII masking
            masked_text, pii_found = pii_masker.mask(normalized)
            pii_details = '|'.join(pii_found) if pii_found else None
            if pii_found:
                stats['pii_masked'][pii_details] += 1
                cleaning_report.append(f'pii_masked:{pii_details}')
            
            # Step 7: Deduplication
            text_hash = compute_hash(masked_text)
            is_dup, dup_type, dup_of_id = deduplicator.is_duplicate(doc_id, masked_text, text_hash)
            
            if is_dup:
                write_jsonl(ledger_file, {
                    'id': doc_id,
                    'status': 'dropped',
                    'stage': 'deduplication',
                    'reason': f'{dup_type}_duplicate',
                    'dup_of': dup_of_id
                })
                stats['dropped'][f'{dup_type}_duplicate'] += 1
                continue
            
            # Document is clean!
            stats['kept']['total'] += 1
            stats['kept_by_lang'][lang] += 1
            
            write_jsonl(ledger_file, {
                'id': doc_id,
                'status': 'kept',
                'stage': 'complete',
                'reason': 'passed_all_filters',
                'dup_of': None,
                'pii_masked': pii_details,
                'language': lang,
                'cleaning': '|'.join(cleaning_report) if cleaning_report else None,
                'text_preview': masked_text[:150]
            })
            
            # Store for final output
            doc_record = {
                'id': doc_id,
                'text': masked_text,
                'lang': lang,
                'source': source
            }
            
            # Randomly select for eval (before saving to clean)
            if random.random() < 0.15:  # 15% chance for eval to get ~200 docs
                eval_candidates.append(doc_record)
            else:
                clean_documents.append(doc_record)
    
    print(f"\n\n{'='*60}")
    print("Pipeline processing complete!")
    print(f"{'='*60}\n")
    
    # Build eval set
    print("Building eval set...")
    eval_size = min(200, len(eval_candidates))
    eval_set = random.sample(eval_candidates, eval_size)
    
    # Write eval set
    for eval_doc in eval_set:
        write_jsonl(eval_file, eval_doc)
    
    print(f"Created eval set with {len(eval_set)} documents")
    
    # Contamination check
    print("\nChecking for contamination...")
    checker = ContaminationChecker(eval_set)
    
    contaminations = []
    clean_final = []
    
    for train_doc in tqdm(clean_documents, desc="  Checking"):
        contam_records = checker.check_contamination(train_doc['id'], train_doc['text'])
        
        if contam_records:
            # Found contamination
            contaminations.extend(contam_records)
            contaminated_train_ids.add(train_doc['id'])
        else:
            # Clean - keep it
            clean_final.append(train_doc)
    
    # Write contamination results (create file even if empty)
    with open(contamination_file, 'w', encoding='utf-8') as f:
        for contam in contaminations:
            json.dump(contam, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"Found {len(contaminations)} contaminated documents")
    print(f"Removed {len(contaminated_train_ids)} unique documents from training")
    
    # Write final clean data as BOTH parquet AND jsonl.gz
    print(f"\nWriting {len(clean_final)} clean documents...")
    
    # Save as parquet
    df = pd.DataFrame(clean_final)
    df.to_parquet(clean_file, index=False, compression='snappy')
    print(f"✓ Clean data saved to {clean_file}")
    
    # Save as jsonl.gz (JSON format)
    import gzip
    clean_jsonl_gz = output_path / "clean" / "clean.jsonl.gz"
    with gzip.open(clean_jsonl_gz, 'wt', encoding='utf-8') as f:
        for doc in clean_final:
            json.dump(doc, f, ensure_ascii=False)
            f.write('\n')
    print(f"✓ Clean data saved to {clean_jsonl_gz}")
    
    # Create manifest
    manifest = {
        'sources': [
            {
                'name': name,
                'file_hash': hash_val,
                'url': 'https://huggingface.co/datasets/allenai/c4' if 'hindi' in name or 'hinglish' in name else 'HuggingFace',
                'license': 'ODC-By 1.0',
                'download_date': '2026-10-22'
            }
            for name, hash_val in source_files.items()
        ],
        'thresholds': {
            'near_duplicate_threshold': 0.85,
            'contamination_threshold': 0.9,
            'min_text_length': 10
        },
        'statistics': {
            'input_total': stats['input']['total'],
            'kept_total': stats['kept']['total'],
            'eval_size': len(eval_set),
            'contaminations_found': len(contaminations),
            'dropped_total': sum(stats['dropped'].values()),
            'by_language': dict(stats['kept_by_lang']),
            'drop_reasons': dict(stats['dropped'])
        },
        'output_files': {
            'clean_data': str(clean_file),
            'ledger': str(ledger_file),
            'eval': str(eval_file),
            'contamination': str(contamination_file)
        }
    }
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Manifest saved to {manifest_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"\nInput documents:     {stats['input']['total']:,}")
    print(f"Kept documents:      {stats['kept']['total']:,}")
    print(f"Eval documents:      {len(eval_set):,}")
    print(f"Dropped documents:   {sum(stats['dropped'].values()):,}")
    print(f"Contaminated:        {len(contaminated_train_ids):,}")
    print(f"\nBy language:")
    for lang, count in sorted(stats['kept_by_lang'].items()):
        print(f"  {lang:10s} {count:,}")
    print(f"\nDrop reasons:")
    for reason, count in sorted(stats['dropped'].items(), key=lambda x: -x[1]):
        print(f"  {reason:20s} {count:,}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist")
        sys.exit(1)
    
    process_pipeline(input_dir, output_dir)
