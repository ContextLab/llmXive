"""
Fallback logic for heuristics: select first k blocks if all scores are near-zero.
Implements T018: Fallback logic in code/heuristics/ to select first k blocks if all scores are near-zero.
"""
import os
import sys
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass, field

# Ensure we can import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@dataclass
class FallbackConfig:
    """Configuration for fallback logic."""
    # Threshold below which a score is considered "near-zero"
    degenerate_threshold: float = 1e-6
    # Default number of blocks to select when fallback is triggered
    default_fallback_k: int = 10
    # Minimum number of blocks to always select (safety floor)
    min_blocks: int = 1
    # Maximum number of blocks to select (safety ceiling)
    max_blocks: int = 100

@dataclass
class FallbackHeuristicWrapper:
    """
    Wrapper that applies fallback logic to any heuristic.
    If the heuristic produces degenerate scores (all near-zero),
    it falls back to selecting the first k blocks.
    """
    config: FallbackConfig = field(default_factory=FallbackConfig)
    logger: logging.Logger = None

    def __post_init__(self):
        if self.logger is None:
            self.logger = logging.getLogger(__name__)

    def is_scores_degenerate(self, scores: np.ndarray) -> bool:
        """
        Check if all scores are near-zero (degenerate).
        
        Args:
            scores: Array of heuristic scores for each block
        
        Returns:
            True if all scores are below the degenerate threshold
        """
        if scores is None or len(scores) == 0:
            return True
        
        # Check if all scores are below the threshold
        return bool(np.all(scores < self.config.degenerate_threshold))

    def select_fallback_blocks(self, total_blocks: int, k: Optional[int] = None) -> List[int]:
        """
        Select the first k blocks as fallback.
        
        Args:
            total_blocks: Total number of available blocks
            k: Number of blocks to select (uses default if None)
        
        Returns:
            List of block indices to select (0-indexed)
        """
        if k is None:
            k = self.config.default_fallback_k
        
        # Clamp k to valid range
        k = max(self.config.min_blocks, min(k, self.config.max_blocks))
        k = min(k, total_blocks)
        
        # Select first k blocks
        fallback_indices = list(range(k))
        
        self.logger.info(
            f"Fallback triggered: selected first {k} blocks out of {total_blocks} total blocks"
        )
        
        return fallback_indices

    def apply_fallback_if_needed(
        self,
        scores: np.ndarray,
        total_blocks: int,
        k: Optional[int] = None
    ) -> Tuple[List[int], bool]:
        """
        Apply fallback logic if scores are degenerate.
        
        Args:
            scores: Array of heuristic scores for each block
            total_blocks: Total number of available blocks
            k: Number of blocks to select (uses default if None)
        
        Returns:
            Tuple of (selected_block_indices, was_fallback_triggered)
        """
        if self.is_scores_degenerate(scores):
            selected = self.select_fallback_blocks(total_blocks, k)
            return selected, True
        
        # Normal case: sort by score and select top k
        if k is None:
            k = self.config.default_fallback_k
        
        k = max(self.config.min_blocks, min(k, self.config.max_blocks))
        k = min(k, total_blocks)
        
        # Get indices of top k scores
        selected = np.argsort(scores)[-k:].tolist()
        selected.sort()  # Return in ascending order for consistency
        
        return selected, False

def main():
    """
    Test the fallback logic with sample data.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create wrapper with default config
    wrapper = FallbackHeuristicWrapper()
    
    # Test case 1: Degenerate scores (all near-zero)
    logger.info("Test 1: Degenerate scores")
    degenerate_scores = np.array([1e-10, 1e-11, 1e-9, 1e-12])
    selected, triggered = wrapper.apply_fallback_if_needed(degenerate_scores, total_blocks=4, k=2)
    logger.info(f"  Scores: {degenerate_scores}")
    logger.info(f"  Selected: {selected}, Fallback triggered: {triggered}")
    assert triggered, "Fallback should be triggered for degenerate scores"
    assert selected == [0, 1], f"Expected [0, 1], got {selected}"
    
    # Test case 2: Normal scores
    logger.info("Test 2: Normal scores")
    normal_scores = np.array([0.1, 0.5, 0.9, 0.3])
    selected, triggered = wrapper.apply_fallback_if_needed(normal_scores, total_blocks=4, k=2)
    logger.info(f"  Scores: {normal_scores}")
    logger.info(f"  Selected: {selected}, Fallback triggered: {triggered}")
    assert not triggered, "Fallback should NOT be triggered for normal scores"
    assert selected == [1, 2], f"Expected [1, 2] (indices of 0.5 and 0.9), got {selected}"
    
    # Test case 3: Edge case - all scores exactly zero
    logger.info("Test 3: All scores exactly zero")
    zero_scores = np.array([0.0, 0.0, 0.0])
    selected, triggered = wrapper.apply_fallback_if_needed(zero_scores, total_blocks=3, k=1)
    logger.info(f"  Scores: {zero_scores}")
    logger.info(f"  Selected: {selected}, Fallback triggered: {triggered}")
    assert triggered, "Fallback should be triggered for zero scores"
    assert selected == [0], f"Expected [0], got {selected}"
    
    # Test case 4: Edge case - k larger than total blocks
    logger.info("Test 4: k larger than total blocks")
    scores = np.array([0.0, 0.0, 0.0])
    selected, triggered = wrapper.apply_fallback_if_needed(scores, total_blocks=3, k=10)
    logger.info(f"  Selected: {selected}, Fallback triggered: {triggered}")
    assert selected == [0, 1, 2], f"Expected [0, 1, 2], got {selected}"
    
    logger.info("All tests passed!")

if __name__ == "__main__":
    main()
