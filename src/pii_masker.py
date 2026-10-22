"""PII detection and masking for Indian data."""
import re
from typing import Tuple, List


class PIIMasker:
    def __init__(self):
        # Indian phone number: 10 digits, optional +91 or 0 prefix
        self.phone_pattern = re.compile(
            r'(\+91[\s\-]?)?[6-9]\d{9}\b|'
            r'\b0?[6-9]\d{9}\b'
        )
        
        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Aadhaar: 12 digits, often with spaces
        self.aadhaar_pattern = re.compile(
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
        )
        
        # PAN: AAAAA9999A format
        self.pan_pattern = re.compile(
            r'\b[A-Z]{5}\d{4}[A-Z]\b'
        )
    
    def mask(self, text: str) -> Tuple[str, List]:
        """Mask PII and return (masked_text, list_of_detailed_pii_info)."""
        if not text:
            return text, []
        
        found_pii = []
        original_text = text
        
        # Mask phone numbers
        phone_matches = self.phone_pattern.findall(text)
        if phone_matches:
            count = len(phone_matches)
            text = self.phone_pattern.sub('<PHONE>', text)
            found_pii.append(f'phone:count={count}')
        
        # Mask emails
        email_matches = self.email_pattern.findall(text)
        if email_matches:
            count = len(email_matches)
            text = self.email_pattern.sub('<EMAIL>', text)
            found_pii.append(f'email:count={count}')
        
        # Mask Aadhaar (be careful - only if looks like Aadhaar)
        aadhaar_count = 0
        for match in self.aadhaar_pattern.finditer(original_text):
            matched = match.group()
            # Check if it's really Aadhaar-like (not just any 12 digits)
            digits_only = re.sub(r'[\s\-]', '', matched)
            if len(digits_only) == 12:
                text = text.replace(matched, '<AADHAAR>', 1)
                aadhaar_count += 1
        
        if aadhaar_count > 0:
            found_pii.append(f'aadhaar:count={aadhaar_count}')
        
        # Mask PAN
        pan_matches = self.pan_pattern.findall(text)
        if pan_matches:
            count = len(pan_matches)
            text = self.pan_pattern.sub('<PAN>', text)
            found_pii.append(f'pan:count={count}')
        
        return text, found_pii
