"""Check for eval contamination in training data."""
from typing import List, Dict, Set
import re
from utils import normalize_text, compute_hash


class ContaminationChecker:
    def __init__(self, eval_items: List[Dict]):
        """Initialize with eval set."""
        self.eval_items = eval_items
        
        # Store eval hashes for exact matching
        self.eval_exact_hashes = {}
        
        # Store eval normalized hashes
        self.eval_norm_hashes = {}
        
        # Store eval fingerprints for near-duplicate detection
        self.eval_fingerprints = {}
        
        for item in eval_items:
            eval_id = item['id']
            text = item['text']
            
            # Exact hash
            exact_hash = compute_hash(text)
            self.eval_exact_hashes[exact_hash] = eval_id
            
            # Normalized hash
            norm_text = normalize_text(text)
            norm_hash = compute_hash(norm_text)
            self.eval_norm_hashes[norm_hash] = eval_id
            
            # Fingerprint for near-dup
            fingerprint = self._create_fingerprint(norm_text)
            self.eval_fingerprints[eval_id] = fingerprint
    
    def check_contamination(self, train_id: str, train_text: str) -> List[Dict]:
        """
        Check if training document contaminates eval set.
        
        Returns list of contamination records.
        """
        contaminations = []
        
        # Check exact match
        exact_hash = compute_hash(train_text)
        if exact_hash in self.eval_exact_hashes:
            contaminations.append({
                'eval_id': self.eval_exact_hashes[exact_hash],
                'train_id': train_id,
                'method': 'exact'
            })
            return contaminations
        
        # Check normalized match
        norm_text = normalize_text(train_text)
        norm_hash = compute_hash(norm_text)
        if norm_hash in self.eval_norm_hashes:
            contaminations.append({
                'eval_id': self.eval_norm_hashes[norm_hash],
                'train_id': train_id,
                'method': 'normalized'
            })
            return contaminations
        
        # Check near-duplicate (threshold 0.9 for contamination)
        train_fp = self._create_fingerprint(norm_text)
        
        for eval_id, eval_fp in self.eval_fingerprints.items():
            similarity = self._jaccard_similarity(train_fp, eval_fp)
            if similarity >= 0.9:  # Stricter threshold for contamination
                contaminations.append({
                    'eval_id': eval_id,
                    'train_id': train_id,
                    'method': f'near_duplicate (similarity={similarity:.2f})'
                })
        
        return contaminations
    
    def _create_fingerprint(self, text: str, n: int = 3) -> Set[str]:
        """Create character n-gram fingerprint."""
        text = re.sub(r'\s+', '', text.lower())
        ngrams = set()
        for i in range(len(text) - n + 1):
            ngrams.add(text[i:i+n])
        return ngrams
    
    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Calculate Jaccard similarity."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
