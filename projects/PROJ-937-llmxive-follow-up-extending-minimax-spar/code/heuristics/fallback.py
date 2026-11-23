import os
import sys
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass, field

from heuristics.base import HeuristicSelector

logger = logging.getLogger(__name__)

@dataclass
class FallbackConfig:
    """Configuration for the fallback heuristic logic."""
    near_zero_threshold: float = 1e-6
    default_top_k: int = 4
    fallback_strategy: str = "first_k"  # Options: "first_k"

class FallbackHeuristicWrapper:
    """
    Wrapper that implements fallback logic for heuristic selection.
    
    If all heuristic scores are near-zero (< threshold), this wrapper
    selects the first k blocks instead of relying on the scores.
    """
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        self.config = config or FallbackConfig()
        
    def _is_scores_near_zero(self, scores: np.ndarray) -> bool:
        """Check if all scores are below the near-zero threshold."""
        if scores is None or len(scores) == 0:
            return True
        return np.all(np.abs(scores) < self.config.near_zero_threshold)
    
    def select_blocks_fallback(self, num_blocks: int) -> List[int]:
        """
        Select the first k blocks as a fallback.
        
        Args:
            num_blocks: Total number of available blocks.
            
        Returns:
            List of block indices to select (first k blocks).
        """
        k = min(self.config.default_top_k, num_blocks)
        return list(range(k))
    
    def select_blocks(self, scores: np.ndarray, num_blocks: int, top_k: Optional[int] = None) -> List[int]:
        """
        Select blocks based on scores, with fallback logic.
        
        If scores are near-zero, falls back to selecting the first k blocks.
        Otherwise, selects the top-k blocks with highest scores.
        
        Args:
            scores: Array of scores for each block.
            num_blocks: Total number of available blocks.
            top_k: Number of blocks to select. Defaults to config value if None.
            
        Returns:
            List of block indices to select.
        """
        if top_k is None:
            top_k = self.config.default_top_k
            
        # Ensure top_k doesn't exceed available blocks
        top_k = min(top_k, num_blocks)
        
        # Check for near-zero scores
        if self._is_scores_near_zero(scores):
            logger.warning(
                f"All heuristic scores are near-zero (< {self.config.near_zero_threshold}). "
                f"Activating fallback: selecting first {top_k} blocks."
            )
            return self.select_blocks_fallback(num_blocks)
        
        # Normal selection: top-k highest scores
        if len(scores) == 0:
            return []
            
        # Get indices of top-k scores
        # Using np.argpartition for efficiency, then sorting the top-k
        if top_k >= len(scores):
            return list(range(len(scores)))
        
        top_k_indices = np.argpartition(scores, -top_k)[-top_k:]
        # Sort these indices by their scores in descending order
        sorted_indices = top_k_indices[np.argsort(scores[top_k_indices])[::-1]]
        return sorted_indices.tolist()

def main():
    """Test the fallback logic with example data."""
    config = FallbackConfig(near_zero_threshold=1e-6, default_top_k=4)
    wrapper = FallbackHeuristicWrapper(config)
    
    # Test 1: Normal scores
    scores_normal = np.array([0.1, 0.5, 0.3, 0.8, 0.2])
    selected_normal = wrapper.select_blocks(scores_normal, num_blocks=5, top_k=3)
    print(f"Normal scores {scores_normal} -> Selected: {selected_normal}")
    assert selected_normal == [3, 1, 2], f"Expected [3, 1, 2], got {selected_normal}"
    
    # Test 2: Near-zero scores (fallback)
    scores_zero = np.array([1e-7, 1e-8, 1e-9, 1e-7, 1e-8])
    selected_zero = wrapper.select_blocks(scores_zero, num_blocks=5, top_k=3)
    print(f"Near-zero scores {scores_zero} -> Selected: {selected_zero}")
    assert selected_zero == [0, 1, 2], f"Expected [0, 1, 2] (first 3), got {selected_zero}"
    
    # Test 3: Empty scores
    scores_empty = np.array([])
    selected_empty = wrapper.select_blocks(scores_empty, num_blocks=0, top_k=3)
    print(f"Empty scores -> Selected: {selected_empty}")
    assert selected_empty == [], f"Expected [], got {selected_empty}"
    
    # Test 4: All zeros
    scores_all_zeros = np.zeros(10)
    selected_zeros = wrapper.select_blocks(scores_all_zeros, num_blocks=10, top_k=5)
    print(f"All zeros (len=10) -> Selected: {selected_zeros}")
    assert selected_zeros == [0, 1, 2, 3, 4], f"Expected [0, 1, 2, 3, 4], got {selected_zeros}"
    
    print("All fallback tests passed!")

if __name__ == "__main__":
    main()
