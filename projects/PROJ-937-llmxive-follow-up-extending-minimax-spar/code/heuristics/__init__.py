# Heuristics package
"""
Heuristic selection modules for sparse attention mechanisms.
Includes Block Entropy, Gradient Magnitude, and Recency Bias implementations.
"""

from .base import HeuristicSelector
from .entropy import BlockEntropyHeuristic
from .gradient import GradientMagnitudeHeuristic
from .recency import RecencyBiasHeuristic
from .fallback import FallbackHeuristicWrapper

__all__ = [
    "HeuristicSelector",
    "BlockEntropyHeuristic",
    "GradientMagnitudeHeuristic",
    "RecencyBiasHeuristic",
    "FallbackHeuristicWrapper",
]
