"""
Fallback logic for heuristic selection.

Implements a safe fallback mechanism to select the first k attention blocks
when all heuristic scores are near-zero (indicating potential failure in
score computation or degenerate attention patterns).
"""
import os
import sys
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass

# Import base class from existing API
from heuristics.base import HeuristicSelector

logger = logging.getLogger(__name__)

@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""
    k_blocks: int = 10
    score_threshold: float = 1e-6
    min_blocks: int = 1
    max_blocks: int = 100

def is_scores_degenerate(
    scores: np.ndarray,
    threshold: float
) -> bool:
    """
    Check if all scores are near-zero (degenerate).
    
    Args:
        scores: Array of heuristic scores for attention blocks
        threshold: Threshold below which scores are considered near-zero
        
    Returns:
        True if all scores are below threshold, False otherwise
    """
    if scores is None or len(scores) == 0:
        return True
    
    max_score = np.max(np.abs(scores))
    return max_score < threshold

def select_fallback_blocks(
    num_blocks: int,
    k: int,
    min_blocks: int = 1,
    max_blocks: int = 100
) -> List[int]:
    """
    Select the first k blocks as fallback.
    
    Args:
        num_blocks: Total number of available blocks
        k: Number of blocks to select
        min_blocks: Minimum number of blocks to select
        max_blocks: Maximum number of blocks to select
        
    Returns:
        List of block indices to select
    """
    # Clamp k to valid range
    k = max(min_blocks, min(k, max_blocks, num_blocks))
    
    # Select first k blocks
    selected = list(range(k))
    
    logger.info(
        f"Using fallback selection: choosing first {k} blocks "
        f"out of {num_blocks} available"
    )
    
    return selected

def apply_fallback_if_needed(
    scores: np.ndarray,
    num_blocks: int,
    config: Optional[FallbackConfig] = None
) -> Tuple[List[int], bool]:
    """
    Apply fallback logic if scores are degenerate.
    
    Args:
        scores: Heuristic scores for each block
        num_blocks: Total number of blocks
        config: Fallback configuration (uses defaults if None)
        
    Returns:
        Tuple of (selected_block_indices, was_fallback_used)
    """
    if config is None:
        config = FallbackConfig()
    
    # Check for degenerate scores
    if is_scores_degenerate(scores, config.score_threshold):
        logger.warning(
            f"Degenerate scores detected (max={np.max(np.abs(scores)):.2e}, "
            f"threshold={config.score_threshold}). Applying fallback."
        )
        
        selected = select_fallback_blocks(
            num_blocks=num_blocks,
            k=config.k_blocks,
            min_blocks=config.min_blocks,
            max_blocks=config.max_blocks
        )
        return selected, True
    
    # Normal case: select based on scores (top-k)
    # Sort indices by score descending
    top_k_indices = np.argsort(scores)[::-1][:config.k_blocks]
    selected = top_k_indices.tolist()
    
    return selected, False

class FallbackHeuristicWrapper(HeuristicSelector):
    """
    Wrapper that adds fallback logic to any heuristic.
    
    This wrapper monitors the scores produced by the underlying heuristic
    and applies fallback selection if scores are degenerate.
    """
    
    def __init__(
        self,
        heuristic: HeuristicSelector,
        config: Optional[FallbackConfig] = None
    ):
        """
        Initialize wrapper.
        
        Args:
            heuristic: Underlying heuristic to wrap
            config: Fallback configuration
        """
        self.heuristic = heuristic
        self.config = config or FallbackConfig()
        self._fallback_count = 0
        self._total_calls = 0
        
        logger.info(
            f"FallbackHeuristicWrapper initialized with "
            f"fallback threshold={self.config.score_threshold}, "
            f"k_blocks={self.config.k_blocks}"
        )
    
    def select_blocks(
        self,
        attention_logits: np.ndarray,
        **kwargs
    ) -> List[int]:
        """
        Select blocks with fallback protection.
        
        Args:
            attention_logits: Attention logits from the model
            **kwargs: Additional arguments passed to underlying heuristic
            
        Returns:
            List of selected block indices
        """
        self._total_calls += 1
        
        # Get scores from underlying heuristic
        scores = self.heuristic.compute_scores(attention_logits, **kwargs)
        
        # Apply fallback logic
        selected, was_fallback = apply_fallback_if_needed(
            scores=scores,
            num_blocks=len(scores),
            config=self.config
        )
        
        if was_fallback:
            self._fallback_count += 1
        
        return selected
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get fallback statistics.
        
        Returns:
            Dictionary with fallback usage statistics
        """
        return {
            "total_calls": self._total_calls,
            "fallback_count": self._fallback_count,
            "fallback_rate": (
                self._fallback_count / self._total_calls
                if self._total_calls > 0 else 0.0
            )
        }

def main():
    """
    Standalone test for fallback logic.
    """
    # Test degenerate score detection
    print("Testing degenerate score detection...")
    
    # All zeros
    scores_zero = np.zeros(100)
    assert is_scores_degenerate(scores_zero, 1e-6), "Failed: all zeros"
    
    # Very small values
    scores_small = np.full(100, 1e-10)
    assert is_scores_degenerate(scores_small, 1e-6), "Failed: very small"
    
    # Normal values
    scores_normal = np.random.rand(100)
    assert not is_scores_degenerate(scores_normal, 1e-6), "Failed: normal values"
    
    print("✓ Degenerate score detection works correctly")
    
    # Test fallback block selection
    print("Testing fallback block selection...")
    
    selected = select_fallback_blocks(100, 10)
    assert selected == list(range(10)), "Failed: basic selection"
    
    # Test with limits
    selected = select_fallback_blocks(5, 10)  # k > num_blocks
    assert selected == list(range(5)), "Failed: k > num_blocks"
    
    selected = select_fallback_blocks(100, 5, min_blocks=10)
    assert selected == list(range(10)), "Failed: min_blocks enforcement"
    
    print("✓ Fallback block selection works correctly")
    
    # Test full wrapper
    print("Testing FallbackHeuristicWrapper...")
    
    # Create a simple mock heuristic
    class MockHeuristic(HeuristicSelector):
        def compute_scores(self, attention_logits, **kwargs):
            return np.zeros(len(attention_logits))  # Always degenerate
        
        def select_blocks(self, attention_logits, **kwargs):
            return []
    
    mock = MockHeuristic()
    wrapper = FallbackHeuristicWrapper(mock, FallbackConfig(k_blocks=5))
    
    dummy_logits = np.random.rand(100, 512)  # 100 blocks
    selected = wrapper.select_blocks(dummy_logits)
    
    assert selected == list(range(5)), "Failed: wrapper fallback"
    assert wrapper.get_stats()["fallback_count"] == 1, "Failed: fallback counter"
    
    print("✓ FallbackHeuristicWrapper works correctly")
    
    print("\n✅ All fallback logic tests passed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
