"""Language detection using fastText."""
import re
import fasttext
from typing import Optional


class LanguageDetector:
    def __init__(self, model_path: str = "models/lid.176.bin"):
        """Initialize fastText language detector."""
        # Try multiple paths
        paths_to_try = [model_path, "../models/lid.176.bin", "./models/lid.176.bin"]
        
        self.model = None
        for path in paths_to_try:
            try:
                import os
                if os.path.exists(path):
                    self.model = fasttext.load_model(path)
                    print(f"✓ Loaded model from: {path}")
                    break
            except Exception:
                continue
        
        if self.model is None:
            print("Warning: Could not load fastText model. Using fallback detection.")
    
    def detect(self, text: str) -> str:
        """
        Detect language and return one of: hi, hi-Latn, en, other.
        
        hi: Hindi in Devanagari script
        hi-Latn: Hinglish (Hindi in Latin script)
        en: English
        other: Everything else
        """
        if not text or len(text.strip()) < 3:
            return "other"
        
        # Check script first
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        # If mostly Devanagari, it's hi
        if has_devanagari and not has_latin:
            return "hi"
        
        # If Devanagari + Latin, it's still hi (code-mixing)
        if has_devanagari and has_latin:
            return "hi"
        
        # If only Latin, need to determine if hi-Latn or en
        if has_latin and not has_devanagari:
            # Use fastText for Latin-only text
            if self.model:
                try:
                    text_clean = text.replace('\n', ' ').strip()
                    predictions = self.model.predict(text_clean, k=1)
                    lang_code = predictions[0][0].replace('__label__', '')
                    
                    # Check for Hinglish patterns
                    hinglish_patterns = [
                        r'\b(hai|hain|ka|ki|ke|ko|se|me|ne|tha|thi|the)\b',
                        r'\b(kya|kaise|kyun|kab|kahan|kaun)\b',
                        r'\b(acha|achha|thik|sahi|nahi|nahin)\b',
                        r'\b(mera|meri|mere|tera|teri|tere)\b'
                    ]
                    
                    for pattern in hinglish_patterns:
                        if re.search(pattern, text.lower()):
                            return "hi-Latn"
                    
                    # If fastText says Hindi, it's Hinglish
                    if lang_code == 'hi':
                        return "hi-Latn"
                    
                    # If fastText says English
                    if lang_code == 'en':
                        return "en"
                    
                    return "other"
                except Exception:
                    pass
            
            # Fallback: check for common Hinglish words
            hinglish_words = ['hai', 'ka', 'ki', 'ko', 'se', 'me', 'kya', 'aur']
            text_lower = text.lower()
            if any(word in text_lower.split() for word in hinglish_words):
                return "hi-Latn"
            
            return "en"
        
        return "other"
