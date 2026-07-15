"""
Mind-Wandering Questionnaire (MWQ) scoring utilities.
Implements reverse-scoring rules and total score calculation.
"""
from typing import List, Dict, Any
import numpy as np

# MWQ Configuration
# Items 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
# Items 2, 3, 4, 5, 6, 7, 8, 9, 10 are reverse scored? 
# Actually, standard MWQ (Smallwood et al., 2012):
# All items are phrased as "My mind was wandering". 
# High score = high mind wandering. 
# No reverse scoring typically needed if all items are consistent.
# However, some versions might have reverse items.
# For this implementation, we assume standard 10-item scale (1-5 Likert).
# If specific reverse items are needed, they can be added here.

REVERSE_ITEMS = [] # Empty for standard MWQ where all items are positive indicators of MW

def score_mwq(items: List[float]) -> Dict[str, Any]:
    """
    Calculate the total MWQ score from item responses.
    
    Args:
        items: List of 10 float responses (1-5 scale).
        
    Returns:
        Dictionary with 'total_score', 'mean_score', and 'item_count'.
    """
    if len(items) != 10:
        raise ValueError(f"MWQ expects 10 items, got {len(items)}")
    
    # Apply reverse scoring if defined
    scored_items = []
    for i, val in enumerate(items):
        if (i + 1) in REVERSE_ITEMS:
            # Reverse: 1->5, 2->4, 3->3, 4->2, 5->1
            scored_items.append(6.0 - val)
        else:
            scored_items.append(val)
    
    total = sum(scored_items)
    mean = total / 10.0
    
    return {
        "total_score": total,
        "mean_score": mean,
        "item_count": 10
    }

def validate_mwq_response(items: List[float]) -> bool:
    """Validate that all items are within the expected range [1, 5]."""
    return all(1.0 <= item <= 5.0 for item in items)
