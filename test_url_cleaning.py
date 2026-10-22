#!/usr/bin/env python3
"""Test URL cleaning approach."""

import sys
sys.path.insert(0, 'src')

from utils import is_spam, normalize_text, remove_urls, remove_html_tags

test_cases = [
    {
        "name": "Useful text with URL",
        "text": "यह भी पढ़ें: https://example.com/news123 भारत ने मैच जीत लिया।",
        "expected": "URLs remove, text kept"
    },
    {
        "name": "Article with metadata URL",
        "text": "Source: https://news.com/article Published on: 12 Jan 2025 भारत विश्व कप जीत गया।",
        "expected": "URLs remove, text kept"
    },
    {
        "name": "Pure spam with URLs",
        "text": "Click Here!!! Earn Money!!! https://spam.com https://spam2.com https://spam3.com",
        "expected": "Drop as spam"
    },
    {
        "name": "HTML with useful content",
        "text": "<div>भारत एक महान देश है।</div>",
        "expected": "HTML remove, text kept"
    },
    {
        "name": "Multiple URLs with good text",
        "text": "भारत ने मैच जीत लिया। देखें वीडियो https://video.com और पढ़ें https://news.com",
        "expected": "URLs remove, text kept"
    }
]

print("\n" + "="*80)
print("URL CLEANING TEST")
print("="*80 + "\n")

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print("-" * 80)
    
    text = test['text']
    print(f"Original: {text}")
    
    # Remove HTML
    cleaned = remove_html_tags(text)
    if cleaned != text:
        print(f"After HTML removal: {cleaned}")
    
    # Remove URLs
    cleaned = remove_urls(cleaned)
    if cleaned != text:
        print(f"After URL removal: {cleaned}")
    
    # Check spam
    is_spam_result, reason = is_spam(cleaned)
    
    if is_spam_result:
        print(f"Result: ❌ DROP - {reason}")
    else:
        print(f"Result: ✅ KEEP")
        print(f"Final text: {cleaned}")
    
    print(f"Expected: {test['expected']}")
    print()

print("="*80 + "\n")
