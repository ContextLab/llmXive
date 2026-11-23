"""
Configuration module for the DSSC project.
Defines global constants and path utilities.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Global Constants
SEED = 42
DEVICE = "cpu"  # Force CPU execution as per constraints

# Path Constants
ROOT = Path(__file__).parent.parent.parent
CODE_DIR = ROOT / "code"
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
TESTS_DIR = ROOT / "tests"
LOGS_DIR = ROOT / "code" / "logs"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
FIGURES_DIR = RESULTS_DIR / "figures"
MODEL_ARTIFACTS_DIR = RESULTS_DIR / "model_artifacts"

# Checksums (Static, hardcoded as per T010 requirement)
# Note: This is a placeholder. In a real scenario, the researcher would provide the actual checksum.
# For T015, we just need the structure to exist.
EXPECTED_DATASET_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary containing all configuration values.
    """
    return {
        "seed": SEED,
        "device": DEVICE,
        "paths": {
            "root": str(ROOT),
            "code": str(CODE_DIR),
            "data": str(DATA_DIR),
            "raw": str(RAW_DATA_DIR),
            "processed": str(PROCESSED_DATA_DIR),
            "results": str(RESULTS_DIR),
            "logs": str(LOGS_DIR),
            "models": str(MODEL_ARTIFACTS_DIR),
        },
        "checksums": {
            "dataset": EXPECTED_DATASET_CHECKSUM,
        }
    }

def ensure_dirs() -> None:
    """
    Ensures all required directories exist.
    """
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        OUTPUTS_DIR,
        RESULTS_DIR,
        MODEL_ARTIFACTS_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        TESTS_DIR,
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True)
