"""
Configuration module for the llmXive brain network topology project.
Defines paths, seeds, and hyperparameters as per T004b and T001.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DIR_CODE = PROJECT_ROOT / "code"
DIR_DATA = PROJECT_ROOT / "data"
DIR_DATA_RAW = DIR_DATA / "raw"
DIR_DATA_PROCESSED = DIR_DATA / "processed"
DIR_DATA_LOGS = DIR_DATA / "logs"
DIR_DATA_FIGURES = DIR_DATA / "figures"
DIR_CONTRACTS = PROJECT_ROOT / "contracts"
DIR_TESTS = PROJECT_ROOT / "tests"

# Hyperparameters (T004b)
# Sliding Window Parameters (in TRs)
WINDOW_LENGTH_BASELINE = 30  # Baseline window length for functional connectivity
WINDOW_LENGTH_VALIDATION = 20  # Validation window length for robustness check
WINDOW_STEP = 1  # Step size between windows in TRs

# Clustering Parameters
K_MEANS_K = 5  # Number of clusters for K-Means state extraction

# Graph Density Thresholds (Proportional)
DENSITY_THRESHOLD_BASELINE = 0.15  # Baseline density (15% of edges retained)
DENSITY_THRESHOLD_VARIATIONS = [0.10, 0.15, 0.20]  # Sensitivity analysis levels

# Tractography Confidence Parameters
TRACTOGRAPHY_CONFIDENCE_MIN = 0.0
TRACTOGRAPHY_CONFIDENCE_MAX = 1.0
TRACTOGRAPHY_CONFIDENCE_STEPS = 5

# Random Seeds for reproducibility
RANDOM_SEED = 42

def ensure_directories() -> None:
    """
    Creates the required directory structure if it does not exist.
    This function satisfies T001 by ensuring code/, data/, contracts/, tests/ exist.
    """
    dirs = [
        DIR_CODE,
        DIR_DATA,
        DIR_DATA_RAW,
        DIR_DATA_PROCESSED,
        DIR_DATA_LOGS,
        DIR_DATA_FIGURES,
        DIR_CONTRACTS,
        DIR_TESTS,
        DIR_CODE / "preprocess",
        DIR_CODE / "analysis",
        DIR_CODE / "reports",
        DIR_CODE / "utils",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """Returns a dictionary of all configuration values."""
    return {
        "window_length_baseline": WINDOW_LENGTH_BASELINE,
        "window_length_validation": WINDOW_LENGTH_VALIDATION,
        "window_step": WINDOW_STEP,
        "k_means_k": K_MEANS_K,
        "density_threshold_baseline": DENSITY_THRESHOLD_BASELINE,
        "density_threshold_variations": DENSITY_THRESHOLD_VARIATIONS,
        "tractography_confidence_min": TRACTOGRAPHY_CONFIDENCE_MIN,
        "tractography_confidence_max": TRACTOGRAPHY_CONFIDENCE_MAX,
        "tractography_confidence_steps": TRACTOGRAPHY_CONFIDENCE_STEPS,
        "random_seed": RANDOM_SEED,
        "paths": {
            "root": str(PROJECT_ROOT),
            "data_raw": str(DIR_DATA_RAW),
            "data_processed": str(DIR_DATA_PROCESSED),
            "data_logs": str(DIR_DATA_LOGS),
            "data_figures": str(DIR_DATA_FIGURES),
            "contracts": str(DIR_CONTRACTS),
        }
    }

# Initialize directories on import to satisfy T001 immediately
ensure_directories()