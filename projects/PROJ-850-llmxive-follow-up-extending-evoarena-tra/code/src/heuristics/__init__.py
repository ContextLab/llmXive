"""
Heuristics module for EvoMem-Conflict Filtering.
"""
from .conflict_detector import ConflictDetector, DEFAULT_MODEL_NAME, DEFAULT_THRESHOLD

__all__ = [
    'ConflictDetector',
    'DEFAULT_MODEL_NAME',
    'DEFAULT_THRESHOLD'
]
