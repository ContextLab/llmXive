"""
Configuration module for the PerceptionDLM overflow experiment.
Defines paths, random seeds, and hyperparameters.

Design Decision Note:
---------------------
We explicitly use PerceptionDLM for both parallel and sequential (context-reset)
baselines to avoid architectural confounds. This supersedes Spec FR-003's
requirement for LLaVA per Plan Summary and Complexity Tracking.

Using the same model architecture for both conditions ensures that any observed
differences in performance (coherence degradation) are attributable to the
processing paradigm (parallel vs. sequential context-reset) rather than
inherent differences in model capability or architecture.
"""
import os
from pathlib import Path

# Project Root
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CODE_DIR = ROOT_DIR / "code"
TESTS_DIR = ROOT_DIR / "tests"
SPECS_DIR = ROOT_DIR / "specs"

# Paths for specific data types
RAW_DATA_DIR = DATA_DIR / "raw"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Random Seed
RANDOM_SEED = 42

# Hyperparameters
# Region counts for testing the overflow hypothesis
REGION_COUNTS = [20, 25, 30, 35, 40, 45, 50]

# Threshold for identifying the tipping point:
# Parallel coherence drops below this fraction of the sequential baseline
TIPPING_POINT_THRESHOLD = 0.9

# Model Settings
MODEL_NAME = "PerceptionDLM"  # Using PerceptionDLM for both parallel and sequential
BATCH_SIZE = 8
MAX_MEMORY_GB = 7.0

# Inference Time Configuration
USE_PERF_COUNTER = True

def ensure_directories():
    """Create all required data directories if they do not exist."""
    for directory in [RAW_DATA_DIR, SYNTHETIC_DATA_DIR, PROCESSED_DATA_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    return True