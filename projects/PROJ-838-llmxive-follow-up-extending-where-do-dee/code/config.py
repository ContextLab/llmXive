"""
Configuration module for llmXive project.

Defines hyperparameters and paths used across the pipeline.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PROCESSED_GRAPHS_DIR = DATA_PROCESSED_DIR / "graphs"

# Hyperparameters
# Cutoff depth for early trajectory spans (0.0 < value <= 1.0)
# Default: 0.3 (first 30% of trajectory)
cutoff_depth = float(os.environ.get("LLMXIVE_CUTOFF_DEPTH", 0.3))

# Random seed for reproducibility
seed = int(os.environ.get("LLMXIVE_SEED", 42))

# Dataset URL / ID for TELBench
# Using the HuggingFace dataset ID as specified in T007
# Note: The execution feedback indicated 'datasets' library issues.
# The correct public ID for TELBench on HuggingFace is 'NJU-LINK/TELBench'.
dataset_url = "NJU-LINK/TELBench"

# Sensitivity analysis parameters (SC-004)
# Thresholds for sensitivity analysis on connectivity values
sensitivity_thresholds = [0.01, 0.05, 0.1]

# Percentiles for sensitivity analysis on the success class
sensitivity_percentiles = [10, 20, 30]

# Hash algorithm for file verification
hash_algorithm = "sha256"

def ensure_directories():
    """Create necessary data directories if they do not exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)