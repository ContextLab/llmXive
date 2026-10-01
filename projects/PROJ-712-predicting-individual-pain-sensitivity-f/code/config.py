"""
Configuration management for the pain sensitivity prediction pipeline.
Handles environment variables, path resolution, and global settings.
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory structure paths
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = _PROJECT_ROOT / "artifacts"
STATE_DIR = _PROJECT_ROOT / "state"
CODE_DIR = _PROJECT_ROOT / "code"
TESTS_DIR = _PROJECT_ROOT / "tests"
SPECS_DIR = _PROJECT_ROOT / "specs"

# Specific file paths
STATE_FILE = STATE_DIR / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
DATASET_SCHEMA = _PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
FEATURES_SCHEMA = _PROJECT_ROOT / "contracts" / "features.schema.yaml"

# Execution limits (from SC-005)
MAX_EXECUTION_HOURS = 6
MAX_EXECUTION_SECONDS = MAX_EXECUTION_HOURS * 3600

# Default experimental parameters
DEFAULT_RANDOM_SEED = 42
DEFAULT_N_FOLDS = 5
DEFAULT_PERMUTATIONS = 100  # Minimum for global permutation test
DEFAULT_BOOTSTRAP_ITERATIONS = 1000

# ICA Parameters
ICA_N_COMPONENTS = 20  # Default, can be overridden
ICA_MAX_ITER = 1000

# Preprocessing Parameters
FILTER_BAND = (1, 40)  # Hz
MIN_VALID_DURATION_SECONDS = 240  # 4 minutes

# Microstate Parameters
N_MICROSTATES = 4  # Canonical A, B, C, D

# Spectral Power Bands (Hz)
SPECTRAL_BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "low_gamma": (30, 45),
    "high_gamma": (45, 60)
}

# Model Parameters
ELASTIC_NET_ALPHA = 0.5
ELASTIC_NET_L1_RATIO = 0.5

# Diagnostics
VIF_THRESHOLD = 10.0
FDR_METHOD = "fdr_bh"  # Benjamini-Hochberg

# OpenNeuro Dataset ID (to be resolved from research.md, defaulting to a placeholder)
# The actual ID must be set via environment variable OPENNEURO_DATASET_ID
OPENNEURO_DATASET_ID = os.getenv("OPENNEURO_DATASET_ID", "ds003XXX")

# Ensure directories exist
def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        ARTIFACTS_DIR,
        STATE_DIR / "projects",
        CODE_DIR,
        TESTS_DIR,
        SPECS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Validation helper
def validate_paths() -> bool:
    """Validate that critical paths exist."""
    ensure_directories()
    return (
        DATA_RAW_DIR.exists() and
        DATA_PROCESSED_DIR.exists() and
        ARTIFACTS_DIR.exists() and
        STATE_DIR.exists()
    )

if __name__ == "__main__":
    # Simple CLI to print configuration
    import json
    config_dict = {
        "project_root": str(_PROJECT_ROOT),
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "artifacts": str(ARTIFACTS_DIR),
        "state": str(STATE_DIR),
        "max_execution_hours": MAX_EXECUTION_HOURS,
        "random_seed": DEFAULT_RANDOM_SEED,
        "openneuro_dataset_id": OPENNEURO_DATASET_ID
    }
    print(json.dumps(config_dict, indent=2))
    validate_paths()