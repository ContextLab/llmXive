"""
llmXive Knot Complexity Analysis Project
Code package for implementing knot diagram complexity quantification.
"""
import os
import random
import hashlib

# Random seed pinning for reproducibility (Per Constitution Principle I)
_DEFAULT_SEED = 42
random.seed(_DEFAULT_SEED)

def get_seed():
    """Return the current random seed value."""
    return _DEFAULT_SEED
