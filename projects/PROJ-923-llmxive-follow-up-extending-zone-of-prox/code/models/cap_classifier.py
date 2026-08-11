"""
Confidence-Adaptive Pruning (CAP) Classifier Module.

Implements the logic to classify negative candidates based on historical
confidence scores to prune the NCQ prompt dynamically.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from utils.logging import get_logger, debug, warning

logger = get_logger(__name__)

# Thresholds defined in FR-003 and Constitution Principle VI
THRESHOLD_REJECTED = 0.1
THRESHOLD_ACCEPTED = 0.9

@dataclass
class ConfidenceStats:
    """Holds statistical summary for a single candidate."""
    mean_confidence: float
    variance_confidence: float
    count: int
    last_confidence: float
    classification: str  # 'rejected', 'fluctuating', 'accepted'

class CAPClassifier:
    """
    Classifies negative candidates based on their historical confidence scores.

    Logic:
    - Calculates mean and variance of confidence scores for each candidate.
    - Classifies as:
      - 'rejected': mean < 0.1
      - 'accepted': mean > 0.9
      - 'fluctuating': 0.1 <= mean <= 0.9
    
    Pruning Rule (FR-003, Constitution Principle VI):
    - Explicitly exclude BOTH 'consistently rejected' (<0.1) AND 
      'consistently accepted' (>0.9) candidates from the prompt.
    - Retain only 'fluctuating' candidates.
    
    Fallback Rule (FR-007):
    - If the resulting set of 'fluctuating' candidates is empty, 
      fall back to the full set of candidates to avoid empty prompts.
    """

    def __init__(self, 
                 threshold_low: float = THRESHOLD_REJECTED, 
                 threshold_high: float = THRESHOLD_ACCEPTED):
        self.threshold_low = threshold_low
        self.threshold_high = threshold_high
        self.logger = logger

    def classify_confidence(self, 
                            scores: List[float]) -> str:
        """
        Classify a single candidate based on a list of historical scores.
        
        Args:
            scores: List of confidence scores for a specific candidate.
        
        Returns:
            Classification string: 'rejected', 'fluctuating', or 'accepted'.
        """
        if not scores:
            self.logger.warning("Empty score list provided to classify_confidence. Defaulting to 'fluctuating'.")
            return "fluctuating"

        mean_val = float(np.mean(scores))
        
        if mean_val < self.threshold_low:
            return "rejected"
        elif mean_val > self.threshold_high:
            return "accepted"
        else:
            return "fluctuating"

    def get_fluctuating_candidates(self, 
                                   candidate_history: Dict[str, List[float]],
                                   full_candidate_set: Optional[Set[str]] = None) -> Set[str]:
        """
        Identifies candidates to be retained in the prompt.
        
        Args:
            candidate_history: Dict mapping candidate_id -> list of confidence scores.
            full_candidate_set: Optional set of all known candidates. 
                                Used for fallback if filtering results in empty set.
        
        Returns:
            Set of candidate IDs to include in the prompt.
        
        Logic:
            1. Filter candidates where classification == 'fluctuating'.
            2. If the filtered set is empty, return the full_candidate_set (or all keys in history).
        """
        fluctuating_set: Set[str] = set()
        
        if not candidate_history:
            self.logger.warning("Empty candidate history provided to CAPClassifier.")
            return set()

        for candidate_id, scores in candidate_history.items():
            classification = self.classify_confidence(scores)
            debug(f"Candidate {candidate_id}: mean={np.mean(scores):.3f}, class={classification}")
            
            if classification == "fluctuating":
                fluctuating_set.add(candidate_id)

        # FR-007: Fallback if resulting set is empty
        if not fluctuating_set:
            fallback_set = set(candidate_history.keys())
            if full_candidate_set:
                fallback_set = full_candidate_set
            
            warning(f"CAP pruning resulted in an empty set. Falling back to {len(fallback_set)} candidates.")
            return fallback_set

        return fluctuating_set

    def analyze_candidates(self, 
                           candidate_history: Dict[str, List[float]]) -> Dict[str, ConfidenceStats]:
        """
        Analyze all candidates and return detailed statistics.
        
        Args:
            candidate_history: Dict mapping candidate_id -> list of confidence scores.
        
        Returns:
            Dict mapping candidate_id -> ConfidenceStats.
        """
        stats_map = {}
        for candidate_id, scores in candidate_history.items():
            if not scores:
                continue
            
            mean_val = float(np.mean(scores))
            var_val = float(np.var(scores))
            classification = self.classify_confidence(scores)
            
            stats_map[candidate_id] = ConfidenceStats(
                mean_confidence=mean_val,
                variance_confidence=var_val,
                count=len(scores),
                last_confidence=scores[-1],
                classification=classification
            )
        
        return stats_map

def classify_confidence(scores: List[float], 
                        threshold_low: float = THRESHOLD_REJECTED, 
                        threshold_high: float = THRESHOLD_ACCEPTED) -> str:
    """
    Standalone helper function to classify confidence scores.
    
    Args:
        scores: List of confidence scores.
        threshold_low: Lower bound for fluctuating range.
        threshold_high: Upper bound for fluctuating range.
        
    Returns:
        Classification string.
    """
    if not scores:
        return "fluctuating"
    
    mean_val = float(np.mean(scores))
    
    if mean_val < threshold_low:
        return "rejected"
    elif mean_val > threshold_high:
        return "accepted"
    else:
        return "fluctuating"