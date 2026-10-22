#!/bin/bash
# Download script - wrapper for download.py
set -e

echo "Downloading datasets..."
python3 download.py || python download.py

echo "Download complete!"
