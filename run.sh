#!/bin/bash
set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: ./run.sh <input_dir> <output_dir>"
    echo "Example: ./run.sh data/raw data/output"
    exit 1
fi

INPUT_DIR=$1
OUTPUT_DIR=$2

echo "Starting data cleaning pipeline..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

python src/main.py "$INPUT_DIR" "$OUTPUT_DIR"

echo ""
echo "✓ Pipeline complete!"
echo "Output files:"
echo "  - $OUTPUT_DIR/clean/clean.parquet"
echo "  - $OUTPUT_DIR/ledger.jsonl"
echo "  - $OUTPUT_DIR/eval.jsonl"
echo "  - $OUTPUT_DIR/contamination.jsonl"
echo "  - $OUTPUT_DIR/manifest.json"
