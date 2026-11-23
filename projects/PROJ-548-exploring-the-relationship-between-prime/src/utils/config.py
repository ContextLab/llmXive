"""
Configuration management for the prime gap analysis pipeline.

Defines global constants for the research parameters including N (max prime),
W (window size), WINDOW_STEP (sliding window stride), and a deterministic
GLOBAL_SEED for reproducibility.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
RESULTS_ROOT = PROJECT_ROOT / "results"
STATE_ROOT = PROJECT_ROOT / "state"

# Research parameters
N = 10**10  # Maximum prime to generate
W = 10**6   # Window size for sliding window analysis
WINDOW_STEP = 10**5  # Step size for sliding windows

# Deterministic random seed for reproducibility (Addresses FR-001, SC-004)
# This seed ensures all random generators in the pipeline produce identical results
# across runs, enabling verification and reproducibility.
GLOBAL_SEED = 42

def ensure_directories():
    """Create required directories if they do not exist."""
    dirs = [
        DATA_ROOT / "raw",
        DATA_ROOT / "processed",
        DATA_ROOT / "null",
        RESULTS_ROOT,
        STATE_ROOT / "projects",
        PROJECT_ROOT / "src" / "data",
        PROJECT_ROOT / "src" / "analysis",
        PROJECT_ROOT / "src" / "utils",
        PROJECT_ROOT / "src" / "cli",
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_global_seed():
    """
    Retrieve the global random seed for the pipeline.

    Returns:
        int: The deterministic seed value (GLOBAL_SEED).
    """
    return GLOBAL_SEED
