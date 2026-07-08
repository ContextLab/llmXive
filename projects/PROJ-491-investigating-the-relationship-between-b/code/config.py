"""
Configuration module for the llmXive research pipeline.
Defines paths, random seeds, and analysis parameters.
"""

import os
from pathlib import Path

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
STATE_DIR = _PROJECT_ROOT / "state"
CODE_DIR = _PROJECT_ROOT / "code"
TESTS_DIR = _PROJECT_ROOT / "tests"
FIGURES_DIR = _PROJECT_ROOT / "figures"
CONTRACTS_DIR = _PROJECT_ROOT / "data" / "contracts"

# Random Seeds for Reproducibility
RANDOM_SEED = 42
NUMPY_SEED = 42
TORCH_SEED = 42  # If PyTorch is added later

# Analysis Parameters
# Window sizes in TRs for sliding window analysis
WINDOW_SIZES_TR = [20, 30, 40]
DEFAULT_WINDOW_SIZE_TR = 30
STEP_SIZE_TR = 1

# Clustering Parameters
K_MEANS_K = 4
K_MEANS_INIT = "k-means++"

# Permutation Test Parameters
PERMUTATION_ITERATIONS = 1000  # Default sufficient for convergence

# Memory Constraints
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = MAX_RAM_GB * 1024**3

# HCP Data Configuration
HCP_MINIMUM_SUBJECTS = 50
HCP_EXPECTED_TR = 0.72  # Typical HCP TR, validated in ingestion

# Output Files
SESSION_VALIDATION_METRICS_FILE = DATA_PROCESSED_DIR / "session_validation_metrics.json"
EXCLUDED_SESSION_IDS_FILE = DATA_PROCESSED_DIR / "excluded_session_ids.csv"
VENTRAL_STRIATUM_ACTIVATION_FILE = DATA_PROCESSED_DIR / "ventral_striatum_activation.csv"
EXCLUDED_SUBJECTS_LOG_FILE = DATA_PROCESSED_DIR / "excluded_subjects_log.csv"
SENSITIVITY_ANALYSIS_FILE = DATA_PROCESSED_DIR / "sensitivity_analysis.csv"
INGESTION_WARNINGS_LOG = DATA_PROCESSED_DIR / "ingestion_warnings.log"
INGESTION_ERRORS_LOG = DATA_PROCESSED_DIR / "ingestion_errors.log"

# Contract Files
ATLAS_POWER_264_FILE = CONTRACTS_DIR / "atlas_power264.json"
ROI_VENTRAL_STRIATUM_FILE = CONTRACTS_DIR / "roi_ventral_striatum.json"
POWER_EXCL_VS_NODES_FILE = CONTRACTS_DIR / "Power264_excl_vs_nodes.json"

# Ensure directories exist
def ensure_directories():
    """Create all required directories if they do not exist."""
    for dir_path in [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        STATE_DIR,
        FIGURES_DIR,
        CONTRACTS_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)