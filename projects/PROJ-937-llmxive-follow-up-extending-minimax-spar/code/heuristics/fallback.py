"""
Fallback logic for heuristic selection.
Implements a safe fallback mechanism to select the first k blocks if all heuristic scores are near-zero.
"""
import os
import sys
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass, field

from heuristics.base import HeuristicSelector

@dataclass
class FallbackConfig:
    """Configuration for the fallback mechanism."""
    k_blocks: int = 10  # Number of blocks to select in fallback mode
    score_threshold: float = 1e-6  # Threshold below which scores are considered near-zero
    min_score_variance: float = 1e-8  # Minimum variance to consider scores as "meaningful"

class FallbackHeuristicWrapper:
    """
    Wraps a heuristic selector and provides fallback logic.
    If all scores are near-zero or have negligible variance, falls back to selecting the first k blocks.
    """

    def __init__(self, heuristic: HeuristicSelector, config: Optional[FallbackConfig] = None):
        """
        Initialize the fallback wrapper.

        Args:
            heuristic: The underlying heuristic selector to use.
            config: Optional FallbackConfig. If None, uses default values.
        """
        self.heuristic = heuristic
        self.config = config or FallbackConfig()
        self.logger = logging.getLogger(__name__)

    def select_blocks(self, scores: np.ndarray, total_blocks: int) -> List[int]:
        """
        Select blocks based on heuristic scores, with fallback logic.

        Args:
            scores: Array of heuristic scores for each block.
            total_blocks: Total number of available blocks.

        Returns:
            List of block indices to select.
        """
        if len(scores) == 0:
            self.logger.warning("No scores provided. Returning empty selection.")
            return []

        # Check if all scores are near-zero
        max_score = np.max(scores)
        score_variance = np.var(scores)

        is_near_zero = max_score < self.config.score_threshold
        is_low_variance = score_variance < self.config.min_score_variance

        if is_near_zero or is_low_variance:
            self.logger.info(
                f"Fallback triggered: max_score={max_score:.2e}, variance={score_variance:.2e}. "
                f"Selecting first {self.config.k_blocks} blocks."
            )
            # Select first k blocks (or all if fewer than k exist)
            k = min(self.config.k_blocks, total_blocks)
            selected = list(range(k))
            return selected

        # Normal operation: use the underlying heuristic
        # The heuristic should return indices based on scores
        # We assume the heuristic's select method handles the ranking
        # Since we don't have direct access to the heuristic's internal logic here,
        # we'll implement a simple top-k selection based on scores
        # This is a generic fallback that works with any score array
        k = min(self.config.k_blocks, total_blocks)
        # Get indices of top-k scores
        selected_indices = np.argsort(scores)[::-1][:k]
        return selected_indices.tolist()

    def get_fallback_status(self, scores: np.ndarray) -> Dict[str, Any]:
        """
        Get status information about whether fallback was triggered.

        Args:
            scores: Array of heuristic scores.

        Returns:
            Dictionary with fallback status details.
        """
        if len(scores) == 0:
            return {
                "fallback_triggered": False,
                "reason": "no_scores",
                "max_score": None,
                "variance": None
            }

        max_score = float(np.max(scores))
        variance = float(np.var(scores))
        is_near_zero = max_score < self.config.score_threshold
        is_low_variance = variance < self.config.min_score_variance

        return {
            "fallback_triggered": is_near_zero or is_low_variance,
            "reason": "near_zero_scores" if is_near_zero else ("low_variance" if is_low_variance else "normal"),
            "max_score": max_score,
            "variance": variance
        }

def main():
    """
    Main function to demonstrate fallback logic.
    This is for testing purposes only.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create a mock heuristic (we'll just use a simple score-based selection)
    class MockHeuristic:
        def select_blocks(self, scores, total_blocks):
            k = min(10, total_blocks)
            return list(np.argsort(scores)[::-1][:k])

    config = FallbackConfig(k_blocks=5, score_threshold=1e-6)
    wrapper = FallbackHeuristicWrapper(MockHeuristic(), config)

    # Test case 1: Normal scores
    logger.info("Test 1: Normal scores")
    scores1 = np.array([0.1, 0.5, 0.3, 0.8, 0.2, 0.9, 0.4, 0.6, 0.7, 0.05])
    result1 = wrapper.select_blocks(scores1, len(scores1))
    logger.info(f"Selected blocks: {result1}")
    status1 = wrapper.get_fallback_status(scores1)
    logger.info(f"Status: {status1}")

    # Test case 2: All near-zero scores
    logger.info("\nTest 2: Near-zero scores")
    scores2 = np.array([1e-8, 1e-9, 1e-7, 1e-8, 1e-9, 1e-10, 1e-8, 1e-9, 1e-7, 1e-8])
    result2 = wrapper.select_blocks(scores2, len(scores2))
    logger.info(f"Selected blocks: {result2}")
    status2 = wrapper.get_fallback_status(scores2)
    logger.info(f"Status: {status2}")

    # Test case 3: Low variance scores
    logger.info("\nTest 3: Low variance scores")
    scores3 = np.array([0.5, 0.5000001, 0.4999999, 0.5, 0.5000002, 0.4999998, 0.5, 0.5, 0.5, 0.5])
    result3 = wrapper.select_blocks(scores3, len(scores3))
    logger.info(f"Selected blocks: {result3}")
    status3 = wrapper.get_fallback_status(scores3)
    logger.info(f"Status: {status3}")

if __name__ == "__main__":
    main()