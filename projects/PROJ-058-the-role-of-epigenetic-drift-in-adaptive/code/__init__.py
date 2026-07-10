"""
Epigenetic Drift Analysis Pipeline.

This package provides tools for analyzing the role of epigenetic drift
in adaptive landscape exploration across multi-generational datasets.
"""

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Import main components for convenient access
from config import set_seed, get_env, get_env_int, get_env_float, ensure_directories
from memory_monitor import (
    get_memory_usage,
    check_memory_usage,
    cleanup_memory,
    chunked_iter,
    process_in_chunks,
    reduce_dataframe_memory,
    memory_profile,
    enforce_memory_limit
)

__all__ = [
    "set_seed",
    "get_env",
    "get_env_int",
    "get_env_float",
    "ensure_directories",
    "get_memory_usage",
    "check_memory_usage",
    "cleanup_memory",
    "chunked_iter",
    "process_in_chunks",
    "reduce_dataframe_memory",
    "memory_profile",
    "enforce_memory_limit"
]
