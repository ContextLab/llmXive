"""
Configuration module for the Network Module Dynamics project.

This module centralizes pinned random seeds for reproducibility and
sliding window parameters for dynamic connectivity analysis.
"""

import random
import numpy as np

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    import leidenalg
    HAS_LEIDENALG = True
except ImportError:
    HAS_LEIDENALG = False

# ---------------------------------------------------------------------
# Reproducibility: Pinned Random Seeds
# ---------------------------------------------------------------------
# Using a fixed seed ensures that stochastic processes (e.g., initialization,
# sampling, or algorithmic randomness in community detection) are reproducible
# across runs.
RANDOM_SEED = 42

def set_all_seeds(seed: int = RANDOM_SEED) -> None:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.

    Args:
        seed: Integer seed value. Defaults to RANDOM_SEED (42).
    """
    random.seed(seed)
    np.random.seed(seed)

    if HAS_NETWORKX:
        # NetworkX relies on numpy's random state for many algorithms.
        # We rely on np.random.seed being set.
        pass

    if HAS_LEIDENALG:
        # LeidenAlg relies on numpy for randomness in initialization.
        # No specific 'set_seed' function exposed directly in all versions,
        # so global numpy seed is the primary mechanism.
        pass

# ---------------------------------------------------------------------
# Analysis Parameters: Sliding Window Configuration
# ---------------------------------------------------------------------
# Window lengths (in seconds) to test for sensitivity analysis.
# Includes the primary values 60 and 90, plus intermediate values.
# Typical TR for HCP 7T rs-fMRI is ~0.72s.
# 60s window ≈ 83 volumes, 90s window ≈ 125 volumes.
WINDOW_LENGTHS_SEC = [30, 45, 60, 75, 90]

# Step size (in seconds) for sliding window.
# A step size of 10s is common to balance temporal resolution and overlap.
WINDOW_STEP_SEC = 10

# Minimum number of time points required per window for valid analysis.
# This prevents calculating connectivity on too-short segments.
MIN_TIME_POINTS_PER_WINDOW = 30

# ---------------------------------------------------------------------
# File Paths (Relative to project root)
# ---------------------------------------------------------------------
DATA_DIR = "data"
PROCESSED_DIR = "data/processed"
RESULTS_DIR = "data/results"
RAW_FMRI_DIR = "data/raw_fmri"
RAW_BEHAV_DIR = "data/raw_behavior"

# ---------------------------------------------------------------------
# Execution Flags
# ---------------------------------------------------------------------
# Maximum memory limit in GB (enforced by memory_monitor.py)
MEMORY_LIMIT_GB = 7.0

# Verbose logging flag
VERBOSE = False