"""
Main package initialization for llmXive perovskite research pipeline.

This module provides the top-level package structure and exposes
the seed handling utilities for deterministic reproducibility.
"""

from src.utils.seed import set_seed, get_seed, get_rng_state, set_rng_state, SeedContext, validate_seed

__version__ = '0.1.0'
__all__ = [
    'set_seed',
    'get_seed',
    'get_rng_state',
    'set_rng_state',
    'SeedContext',
    'validate_seed',
]