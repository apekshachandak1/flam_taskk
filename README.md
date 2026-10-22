# Hindi/Hinglish Data Cleaning Pipeline - Flam Assignment

Clean Indic corpus pipeline for LLM training with language detection, PII masking, deduplication, and quality filtering.

## Quick Start

```bash
# 1. Download data
bash download.sh

# 2. Run pipeline
bash run.sh data/raw data/output

# 3. View results
python view_detailed_ledger.py
```

## Pipeline Features

✅ **Streaming processing** - Handles large datasets line-by-line  
✅ **Language detection** - hi (Hindi), hi-Latn (Hinglish), en (English)  
✅ **PII masking** - Phone, email, Aadhaar, PAN with counts  
✅ **Spam filtering** - Detailed reasons (repetition, URLs, HTML, etc.)  
✅ **Deduplication** - Exact + near-duplicate @ 0.85 similarity  
✅ **Contamination check** - Prevents eval leakage  
✅ **Complete audit trail** - Every decision logged with text previews

## Output Files

```
data/output/
├── clean/clean.parquet    # Training data (text, lang, source)
├── eval.jsonl             # Held-out eval set (~200 docs)
├── ledger.jsonl           # Complete audit trail
├── contamination.jsonl    # Contamination report
└── manifest.json          # Metadata & statistics
```

## Ledger Format (Detailed)

Each line tracks one document with **detailed reasons**:

### Kept Document:
```json
{
  "id": "doc_000123",
  "status": "kept",
  "stage": "complete",
  "reason": "passed_all_filters",
  "dup_of": null,
  "pii_masked": "phone:count=2|email:count=1",
  "language": "hi",
  "text_preview": "यह एक साफ <PHONE> डॉक्यूमेंट है..."
}
```

### Dropped Document (Spam):
```json
{
  "id": "doc_000456",
  "status": "dropped",
  "stage": "spam_filter",
  "reason": "excessive_repetition(unique_ratio=0.08)",
  "dup_of": null,
  "text_preview": "aaaa bbbb cccc aaaa bbbb cccc..."
}
```

### Dropped Document (Duplicate):
```json
{
  "id": "doc_000789",
  "status": "dropped",
  "stage": "deduplication",
  "reason": "near_duplicate",
  "dup_of": "doc_000567",
  "text_preview": "Similar content to previous document..."
}
```

## View Results

```bash
# Detailed analysis with examples
python view_detailed_ledger.py

# Compare input vs output
python compare_input_output.py

# Show specific examples
python show_examples.py
```

## Key Statistics

From 10,000 input documents:
- **Kept**: 1,292 (12.9%)
- **Dropped**: 8,708 (87.1%)
  - Spam: 6,585 (65.8%)
  - Wrong language: 2,088 (20.9%)
  - Duplicates: 5 (0.05%)

## PII Masking

Detects and masks with counts:
- **Phone**: Indian formats (+91, 10-digit)
- **Email**: Standard email patterns
- **Aadhaar**: 12-digit numbers (with validation)
- **PAN**: AAAAA9999A format

Example: `pii_masked: "phone:count=2|email:count=1"`

## Spam Detection Reasons

Detailed reasons with metrics:
- `excessive_repetition(unique_ratio=0.08)` - Low character diversity
- `excessive_punctuation(ratio=0.18,count=45)` - Too many symbols
- `url_spam(urls=12)` - Multiple URLs
- `html_spam(tags=8)` - HTML artifacts
- `promotional_spam(found=buy now,click here)` - Marketing content

## Requirements

```bash
pip install -r requirements.txt
```

Key dependencies:
- pandas, pyarrow (data handling)
- fasttext-wheel (language detection)
- tqdm (progress bars)
- regex, unicodedata2 (text processing)

## Documentation

- **docs/DECISIONS.md** - Complete writeup with real numbers
- **docs/README.md** - Architecture details
- **SUBMISSION_CHECKLIST.md** - Submission requirements
- **HOW_TO_VIEW_OUTPUT.md** - Output viewing guide

## Sources

- **allenai/c4** (Hindi subset) - 9,000 docs
- **allenai/c4** (Hinglish/hi-Latn) - 1,000 docs
- License: ODC-By 1.0 (permissive, commercial use OK)

## Author

Flam LLM Assignment - Data Cleaning Pipeline  
Built for high-quality Indic language training data
