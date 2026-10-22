#!/usr/bin/env python3
"""Verify specific samples mentioned in review."""

import sys
sys.path.insert(0, 'src')

from utils import remove_boilerplate, normalize_text, is_spam
from pii_masker import PIIMasker

test_cases = [
    {
        "name": "Product listing (should be removed/cleaned)",
        "text": "होम > उत्पादों > कोहनी सेनेटरी फिटिंग Shijiazhuang Huize Pipe Fitting Co., Ltd."
    },
    {
        "name": "News with boilerplate",
        "text": "SPOTLIGHT : 18 - APR - 5:00 PM अनिल अंबानी समूह की कंपनी रिलायंस डिफेंस... You May Also Like : Nepal, China hold first-ever joint military exercises"
    },
    {
        "name": "Contact info with PII",
        "text": "विकास फार्म, तृश्शूर, केरल फोन नंबर: 9876543210 ईमेल: contact@example.com"
    },
    {
        "name": "Simple news (should be kept)",
        "text": "यह भी पढें राम भक्तों का सपना हुआ साकार जय जयकारे के बीच रखी गई आधारशिला"
    }
]

pii_masker = PIIMasker()

print("\n" + "="*80)
print("SAMPLE VERIFICATION")
print("="*80 + "\n")

for i, test in enumerate(test_cases, 1):
    print(f"{i}. {test['name']}")
    print("-" * 80)
    print(f"Original:\n  {test['text']}\n")
    
    # Normalize
    text = normalize_text(test['text'])
    
    # Remove boilerplate
    cleaned = remove_boilerplate(text)
    if cleaned != text:
        print(f"After boilerplate removal:\n  {cleaned}\n")
    
    # Mask PII
    masked, pii_found = pii_masker.mask(cleaned)
    if pii_found:
        print(f"PII Found: {', '.join(pii_found)}")
        print(f"After PII masking:\n  {masked}\n")
    
    # Check spam
    is_spam_result, reason = is_spam(masked if pii_found else cleaned)
    
    if is_spam_result:
        print(f"Decision: ❌ DROP - {reason}")
    else:
        print(f"Decision: ✅ KEEP")
        print(f"Final text:\n  {masked if pii_found else cleaned}")
    
    print()

print("="*80 + "\n")
