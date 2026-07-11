"""
Heuristics module for llmXive sparse attention selection.

This module provides the base class and concrete implementations
for attention block selection heuristics.
"""

from .base import HeuristicSelector
from .entropy import BlockEntropyHeuristic
from .gradient import GradientMagnitudeHeuristic
from .recency import RecencyBiasHeuristic

__all__ = [
    'HeuristicSelector',
    'BlockEntropyHeuristic',
    'GradientMagnitudeHeuristic',
    'RecencyBiasHeuristic'
]

# Mapping of heuristic names to classes for dynamic selection
HEURISTIC_REGISTRY = {
    'block_entropy': BlockEntropyHeuristic,
    'gradient_magnitude': GradientMagnitudeHeuristic,
    'recency_bias': RecencyBiasHeuristic
}

def get_heuristic_class(name: str):
    """
    Get a heuristic class by name from the registry.
    
    Args:
        name: The name of the heuristic (e.g., 'block_entropy')
        
    Returns:
        The heuristic class if found, None otherwise.
    """
    return HEURISTIC_REGISTRY.get(name.lower())

def get_available_heuristics():
    """
    Get a list of all available heuristic names.
    
    Returns:
        List of heuristic names.
    """
    return list(HEURISTIC_REGISTRY.keys())
