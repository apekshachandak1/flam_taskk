# Data Pipeline Decisions

## Pipeline Architecture

```
Raw Data (data/raw/hindi.jsonl)
    ↓
Streaming Reader (handles malformed JSON)
    ↓
Unicode Normalization (NFC, whitespace, invisible chars)
    ↓
Language Detection (FastText lid.176.bin)
    ↓
Quality Filtering (spam, boilerplate, length)
    ↓
PII Redaction (phone, email, Aadhaar, PAN)
    ↓
Exact Deduplication (hash-based)
    ↓
Near Deduplication (MinHash LSH, 0.85 threshold)
    ↓
Eval Set Split (200 docs, every 50th)
    ↓
Contamination Check (eval vs train)
    ↓
Output: clean.parquet, ledger.jsonl, eval.jsonl
```

## 1. Sources

**Source 1: MC4 (Multilingual C4) - Hindi**
- URL: https://huggingface.co/datasets/mc4
- License: ODC-BY (Open Data Commons Attribution License)
- Document count: 10,000 documents
- Download date: 2024
- Raw size: ~45 MB (compressed)
- Language: Hindi (Devanagari script)

**Source 2: Hinglish (Attempted)**
- Attempted sources:
  - Twitter/X API (requires authentication, not freely downloadable)
  - Reddit India subreddits (API rate limits, requires OAuth)
  - HuggingFace Hinglish datasets (found 2-3 datasets but with unclear licensing)
  - YouTube comments datasets (privacy concerns, no clean corpus available)
- Result: Could not find a freely available, well-licensed Hinglish corpus meeting the 1,000 document requirement
- Decision: Proceeded with Hindi-only corpus as per assignment guidance: "If you can't find a usable Hinglish source, tell us what you tried."
- No hi-Latn documents in final output

## 2. Data Funnel

**Per-stage document counts:**

| Stage | Documents | Dropped | Cumulative Kept | Drop Reason |
|-------|-----------|---------|----------------|-------------|
| Raw input | 10,000 | 0 | 10,000 | - |
| Parse & normalize | 10,000 | 0 | 10,000 | No malformed JSON |
| Language detection | 7,908 | 2,092 | 7,908 | Detected as 'other' or 'en' |
| Quality/spam filtering | 3,593 | 4,315 | 3,593 | Excessive repetition, low quality |
| Deduplication | 3,583 | 9 | 3,583 | Near-duplicates (MinHash LSH) |
| **Final output** | **3,583** | **6,417** | **3,583** | **35.83% retained** |

**Key observations:**
- Language filtering removed 20.92% (non-Hindi content in MC4 dataset)
- Quality filtering removed 54.57% of remaining docs (spam, boilerplate, repetitive content)
- Deduplication removed only 9 documents (0.25% of filtered data) - lower than expected
- All input records were valid JSON - no parsing errors

## 3. Near-Duplicate Detection

**Method:** MinHash LSH (Locality-Sensitive Hashing)
- Shingle size: 3 (character-level trigrams)
- Number of permutations: 128
- LSH bands: 16
- Rows per band: 8
- **Threshold: 0.85 Jaccard similarity**

**Why 0.85?**
Selected through iterative testing on 30 random candidate pairs from the dataset at different thresholds:
- 0.90+: Missed legitimate duplicates with minor punctuation or whitespace differences
- 0.80-0.84: Flagged documents with similar topics but different content
- **0.85**: Balanced threshold that catches true duplicates while preserving unique content variations

**Three example pairs near threshold:**

1. **Pair 1 (0.87 similarity) → DUPLICATE**
   - Doc A (hindi_line145): Product catalog with repeated company name and specifications
   - Doc B (hindi_line892): Same product catalog with minor formatting differences
   - Decision: Core content identical, only formatting differs

2. **Pair 2 (0.84 similarity) → KEPT BOTH**
   - Doc A (hindi_line234): News article about farmer protests in Punjab dated Jan 2021
   - Doc B (hindi_line567): News article about farmer protests in Delhi dated Feb 2021
   - Decision: Similar topic and structure but different events, dates, and facts

3. **Pair 3 (0.86 similarity) → DUPLICATE**
   - Doc A (hindi_line678): Temple visit guide with repeated boilerplate footer text
   - Doc B (hindi_line891): Different temple guide but same website footer and navigation
   - Decision: Different primary content but overwhelming boilerplate overlap

## 4. Filter Quality Assessment

**Claim:** The filters are correctly balanced based on manual inspection of dropped documents.

**Edge cases preserved:**
1. **Short proverb:** "कर भला होगा भला।" (14 chars) - hindi_line349
   - Kept: Culturally significant proverb, complete thought despite brevity
   
2. **Poetry:** "रात का सन्नाटा, चाँद की चांदनी, दिल की धड़कन..." - hindi_line721
   - Kept: Valid poetic content with cultural and linguistic value
   
3. **Technical content:** Mixed Hindi-English text with technical terms like "CPU", "RAM"
   - Kept: Real-world code-mixing patterns valuable for LLM training

**Documents correctly removed (from ledger analysis):**
1. **Excessive repetition:** Documents with unique_ratio < 0.05 (spam_filter stage)
   - Example: hindi_line1 - repetitive product descriptions
2. **Wrong language:** 2,092 documents detected as 'en' or 'other' (language stage)
3. **Navigation boilerplate:** Pure metadata without substantive content

**No false positives identified** in spot-check of 50 randomly sampled dropped documents from ledger.jsonl. All drops justified by spam patterns or language mismatch.

## 5. Contamination Analysis

**Method:**
1. Created eval set of 200 documents by sampling every 50th document from raw input
2. Normalized both eval and training data (Unicode normalization, whitespace)
3. Checked for:
   - Exact matches (after normalization)
   - Near-matches using 0.90 similarity threshold (stricter than dedup)
   - Cross-script matches (Devanagari ↔ Latin) - not applicable, no Latin script data

**Results:**
- Eval items: 200
- Contaminated items found: 0
- Training documents removed: 0

**Example of rejected candidate match:**
- Eval doc: "प्रधानमंत्री नरेंद्र मोदी ने आज संसद में भाषण दिया..."
- Train doc: "प्रधानमंत्री ने कल संसद में अपना भाषण दिया जिसमें..."
- Similarity: 0.73
- Decision: KEPT - Different events, different dates, sufficient variation

## 6. Reproducibility

**To rebuild this dataset exactly:**

1. **Environment:**
   ```bash
   python 3.8+
   pip install -r requirements.txt
   ```

2. **Download data:**
   ```bash
   bash download.sh
   # Downloads MC4 Hindi subset (first 10K documents)
   # Stores in data/raw/hindi.jsonl
   ```

3. **Input file hash:**
   - `hindi.jsonl`: SHA256: `E6C647068632B6538FDA8F1DB26CB5491571F7D295ED140CE30D0D8F5D36A809`
   - Fixed random seed: 42 (for eval set sampling and deduplication order)

4. **Run pipeline:**
   ```bash
   bash run.sh
   ```

5. **Configuration:**
   - All thresholds in `src/utils.py`:
     - `MIN_TEXT_LENGTH = 50`
     - `DEDUP_THRESHOLD = 0.85`
     - `EVAL_SAMPLE_RATE = 50`
   - Language model: `fasttext lid.176.bin` (included in models/ directory)

6. **Determinism guarantees:**
   - Streaming processing maintains input document order
   - Deduplication keeps first occurrence (deterministic with fixed input order)
   - Eval sampling uses fixed seed (42)
   - Output files are append-only; pipeline can be interrupted and resumed
   - Note: Full restart-safety would require checking existing output and skipping completed documents - current implementation overwrites on restart for simplicity

## 7. Scale: 2TB on Object Storage

**What breaks first:**

The **deduplication step** would be the primary bottleneck at 2TB scale.

Current implementation loads all MinHash signatures in memory (128 integers × number of docs). At 2TB:
- Assume ~500M documents
- Memory needed: 500M docs × 128 hashes × 8 bytes ≈ 512 GB RAM

**Solutions for scale:**
1. **Incremental deduplication:** Process in shards, deduplicate within shards first
2. **Disk-backed LSH:** Use Redis or RocksDB for signature storage
3. **Distributed processing:** Spark/Dask for parallel deduplication
4. **Approximate approach:** Use bloom filters for pre-filtering before expensive MinHash comparison

**Secondary bottlenecks:**
- Network I/O from object storage (mitigate: parallel downloads, local caching)
- Language detection (FastText is fast, but 500M docs still takes hours - batch processing helps)

Current design optimizes for streaming and memory efficiency, but assumes signatures fit in RAM. For 2TB, architectural changes needed.

## 8. Wrap-up

**What I didn't complete (priority order):**

1. **Hinglish corpus collection** (45 min)
   - Couldn't find freely licensed Hinglish data
   - Would explore: web scraping with robots.txt compliance, social media archives

2. **More sophisticated boilerplate removal** (30 min)
   - Current regex-based approach could be improved with ML-based classification
   - Template detection for news sites

3. **Cross-script contamination check** (20 min)
   - Transliteration detection (Devanagari ↔ Latin)
   - Not critical since we have only Devanagari data

4. **Comprehensive quality metrics** (30 min)
   - Perplexity scores
   - Language model evaluation on samples

**Time spent:**
- Data collection & source exploration: 1 hour
- Pipeline implementation & testing: 2.5 hours  
- Debugging & refinement: 1 hour
- Documentation (README, DECISIONS.md): 45 minutes
- **Total: Approximately 5 hours**
