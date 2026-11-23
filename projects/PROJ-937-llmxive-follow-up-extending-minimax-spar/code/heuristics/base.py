"""
Base abstract class for Heuristic Selector.
Defines the interface for heuristic-based attention block selection.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging
from dataclasses import dataclass, field

from utils.logger import get_logger_for_task

logger = get_logger_for_task(__name__)


@dataclass
class HeuristicConfig:
    """Configuration for heuristic selection."""
    top_k: int = 4
    entropy_weight: float = 1.0
    gradient_weight: float = 1.0
    recency_weight: float = 1.0
    fallback_threshold: float = 1e-6
    device: str = "cpu"


class HeuristicSelector(ABC):
    """
    Abstract base class for heuristic-based attention block selection.

    This class defines the interface for selecting attention blocks based on
    various heuristics (entropy, gradient magnitude, recency bias).
    """

    def __init__(self, config: Optional[HeuristicConfig] = None):
        """
        Initialize the HeuristicSelector.

        Args:
            config: HeuristicConfig instance. If None, uses default config.
        """
        self.config = config or HeuristicConfig()
        self.logger = logger
        self._scores: Dict[str, np.ndarray] = {}

    @abstractmethod
    def compute_scores(
        self,
        attention_logits: np.ndarray,
        block_positions: np.ndarray,
        **kwargs: Any
    ) -> Dict[str, np.ndarray]:
        """
        Compute heuristic scores for each attention block.

        Args:
            attention_logits: Attention logits from the model.
            block_positions: Positions of attention blocks.
            **kwargs: Additional arguments for specific heuristics.

        Returns:
            Dictionary mapping heuristic names to score arrays.
        """
        pass

    @abstractmethod
    def select_blocks(
        self,
        scores: Dict[str, np.ndarray],
        k: Optional[int] = None
    ) -> List[int]:
        """
        Select top-k blocks based on heuristic scores.

        Args:
            scores: Dictionary of heuristic scores.
            k: Number of blocks to select. If None, uses config.top_k.

        Returns:
            List of indices of selected blocks.
        """
        pass

    def aggregate_scores(
        self,
        scores: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Aggregate multiple heuristic scores into a single score.

        Args:
            scores: Dictionary of heuristic scores.
            weights: Optional dictionary of weights for each heuristic.
                    If None, uses config weights.

        Returns:
            Aggregated score array.
        """
        if not scores:
            raise ValueError("No scores provided for aggregation")

        if weights is None:
            weights = {
                "entropy": self.config.entropy_weight,
                "gradient": self.config.gradient_weight,
                "recency": self.config.recency_weight,
            }

        aggregated = np.zeros_like(list(scores.values())[0])
        total_weight = 0.0

        for name, score in scores.items():
            if name in weights:
                weight = weights[name]
                # Normalize score to [0, 1] range before weighting
                if score.max() > score.min():
                    normalized = (score - score.min()) / (score.max() - score.min())
                else:
                    normalized = np.zeros_like(score)
                aggregated += weight * normalized
                total_weight += weight

        if total_weight > 0:
            aggregated /= total_weight

        return aggregated

    def is_fallback_needed(
        self,
        scores: Dict[str, np.ndarray]
    ) -> bool:
        """
        Check if fallback selection is needed (all scores near zero).

        Args:
            scores: Dictionary of heuristic scores.

        Returns:
            True if fallback is needed, False otherwise.
        """
        threshold = self.config.fallback_threshold
        for name, score in scores.items():
            if np.any(np.abs(score) > threshold):
                return False
        return True

    def get_scores(self) -> Dict[str, np.ndarray]:
        """Get the computed scores."""
        return self._scores.copy()

    def set_scores(self, scores: Dict[str, np.ndarray]) -> None:
        """Set the computed scores."""
        self._scores = scores.copy()