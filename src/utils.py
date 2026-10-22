"""Utility functions for the pipeline."""
import json
import unicodedata
import re
import xxhash
from typing import Dict, Any, Tuple


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace after tag removal
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def remove_boilerplate(text: str) -> str:
    """Remove common boilerplate phrases from web content."""
    if not text:
        return ""
    
    # Common boilerplate patterns - more comprehensive
    boilerplate_patterns = [
        r'You May Also Like\s*:?',
        r'Related Articles?\s*:?',
        r'Read More\s*:?',
        r'Click Here\s*:?',
        r'Published on\s*:?\s*\d{1,2}\s+\w+\s+\d{4}',
        r'Author\s*:?',
        r'Share\s*:?',
        r'Facebook\s*\|?\s*Twitter\s*\|?\s*Instagram',
        r'Home\s*>\s*[^>]+>\s*',  # Breadcrumbs
        r'Copyright\s*©?\s*\d{4}',
        r'Privacy Policy',
        r'Terms & Conditions?',
        r'All Rights Reserved',
        r'Subscribe\s*:?',
        r'Follow us on',
        r'Advertisement',
        r'\[\s*truncated:.*?\]',
        r'Source\s*:?\s*https?://[^\s]+',  # Source with URL
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def remove_urls(text: str) -> str:
    """Remove URLs from text but keep meaningful content."""
    if not text:
        return ""
    # Remove URLs (http://, https://, www.)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'www\.[^\s]+', '', text)
    # Normalize whitespace after URL removal
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_text(text: str) -> str:
    """Normalize Unicode text for consistent comparison."""
    if not text:
        return ""
    
    # Convert to NFC form (Canonical Decomposition followed by Canonical Composition)
    text = unicodedata.normalize('NFC', text)
    
    # Remove zero-width characters
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def compute_hash(text: str) -> str:
    """Compute xxhash for deduplication."""
    return xxhash.xxh64(text.encode('utf-8')).hexdigest()


def is_spam(text: str) -> Tuple[bool, str]:
    """Detect ONLY genuine spam - not legitimate articles with URLs/HTML."""
    if not text or len(text.strip()) < 10:
        return True, f"too_short(len={len(text.strip())})"
    
    # Check for excessive repetition (very low threshold - only obvious spam)
    unique_ratio = len(set(text)) / len(text) if len(text) > 0 else 0
    if unique_ratio < 0.05:  # Increased threshold - only extreme cases
        return True, f"excessive_repetition(unique_ratio={unique_ratio:.2f})"
    
    # Check for excessive punctuation (only extreme cases)
    punct_ratio = sum(c in '!?$#@*' for c in text) / len(text)
    if punct_ratio > 0.20:  # Increased threshold
        punct_count = sum(c in '!?$#@*' for c in text)
        return True, f"excessive_punctuation(ratio={punct_ratio:.2f},count={punct_count})"
    
    # Check for excessive emojis (only extreme cases)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    emoji_count = len(emoji_pattern.findall(text))
    word_count = len(text.split())
    if word_count > 0 and emoji_count > word_count * 0.5:  # Increased threshold
        return True, f"excessive_emojis(emoji={emoji_count},words={word_count})"
    
    # Check for promotional spam (must have multiple spam indicators)
    spam_phrases = ['buy now', 'click here', 'limited offer', 'prize', 'winner', 'earn money']
    lower_text = text.lower()
    found_phrases = [p for p in spam_phrases if p in lower_text]
    
    # Only drop if MULTIPLE spam indicators + promotional language
    if len(found_phrases) >= 3:  # Need at least 3 spam phrases
        return True, f"promotional_spam(found={','.join(found_phrases)})"
    
    # DON'T check for URLs here - they've already been removed in cleaning
    # DON'T check for HTML here - it's already been removed
    
    return False, ""


def read_jsonl_stream(filepath: str):
    """Stream read JSONL file line by line."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed JSON at line {line_num}: {e}")
                continue


def write_jsonl(filepath: str, data: Dict[Any, Any]):
    """Append a single line to JSONL file."""
    with open(filepath, 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write('\n')
