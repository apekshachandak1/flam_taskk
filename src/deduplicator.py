"""Exact and near-duplicate detection."""
from typing import Dict, Optional, Set, Tuple
import re


class Deduplicator:
    def __init__(self, threshold: float = 0.85):
        """
        Initialize deduplicator.
        
        Args:
            threshold: Jaccard similarity threshold for near-duplicates (0.85 = 85% similar)
        """
        self.exact_hashes: Set[str] = set()
        self.near_dup_fingerprints: Dict[str, str] = {}  # fingerprint -> doc_id
        self.threshold = threshold
    
    def is_duplicate(self, doc_id: str, text: str, text_hash: str) -> Tuple[bool, str, str]:
        """
        Check if document is duplicate.
        
        Returns:
            (is_dup, dup_type, dup_of_id)
            dup_type: 'exact' or 'near'
        """
        # Check exact duplicate
        if text_hash in self.exact_hashes:
            return True, 'exact', text_hash
        
        # Check near duplicate using fingerprinting
        fingerprint = self._create_fingerprint(text)
        fingerprint_frozen = frozenset(fingerprint)  # Make hashable
        
        for existing_fp_frozen, existing_id in self.near_dup_fingerprints.items():
            existing_fp = set(existing_fp_frozen)  # Convert back to set for comparison
            similarity = self._jaccard_similarity(fingerprint, existing_fp)
            if similarity >= self.threshold:
                return True, 'near', existing_id
        
        # Not a duplicate - store it
        self.exact_hashes.add(text_hash)
        self.near_dup_fingerprints[fingerprint_frozen] = doc_id
        
        return False, '', ''
    
    def _create_fingerprint(self, text: str, n: int = 3) -> Set[str]:
        """Create character n-gram fingerprint."""
        # Clean text: remove spaces and lowercase
        text = re.sub(r'\s+', '', text.lower())
        
        # Create character n-grams
        ngrams = set()
        for i in range(len(text) - n + 1):
            ngrams.add(text[i:i+n])
        
        return ngrams
    
    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
