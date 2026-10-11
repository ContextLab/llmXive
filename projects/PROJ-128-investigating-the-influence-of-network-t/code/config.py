"""
Configuration module for the llmXive brain network topology project.
Defines paths, seeds, and hyperparameters as per T004b and T001.

T004b requirements implemented here:
  - WINDOW_LENGTH_BASELINE = 30 (TRs)
  - WINDOW_LENGTH_VALIDATION = [20] (list of TRs, per task spec)
  - WINDOW_STEP = 1 (TRs)
  - K_MEANS_K = 5
  - BASELINE_DENSITY = 0.1
  - DENSITY_THRESHOLD_VARIATIONS derived as BASELINE_DENSITY ± 5% relative
    perturbation (FR-008): [0.095, 0.1, 0.105] — explicit numeric offsets,
    not vague heuristics.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DIR_CODE = PROJECT_ROOT / "code"
DIR_DATA = PROJECT_ROOT / "data"
DIR_DATA_RAW = DIR_DATA / "raw"
DIR_DATA_PROCESSED = DIR_DATA / "processed"
DIR_DATA_DERIVED = DIR_DATA / "derived"
DIR_DATA_LOGS = DIR_DATA / "logs"
DIR_DATA_FIGURES = DIR_DATA / "figures"
DIR_CONTRACTS = PROJECT_ROOT / "contracts"
DIR_TESTS = PROJECT_ROOT / "tests"

# Hyperparameters (T004b)
# Sliding Window Parameters (in TRs)
WINDOW_LENGTH_BASELINE = 30  # Baseline window length for functional connectivity
WINDOW_LENGTH_VALIDATION = [20]  # Validation window lengths (list) for robustness check
WINDOW_STEP = 1  # Step size between windows in TRs

# Clustering Parameters
K_MEANS_K = 5  # Number of clusters for K-Means state extraction

# Graph Density Thresholds (Proportional)
# Baseline density (10% of edges retained). May be derived dynamically
# (e.g., median degree of the cohort) by downstream consumers; when
# derived, they should override this value and log the derived value.
BASELINE_DENSITY = 0.1

# FR-008: ±5% RELATIVE perturbation of the baseline density.
# For BASELINE_DENSITY = 0.1: 0.1 * 0.95 = 0.095, 0.1, 0.1 * 1.05 = 0.105.
DENSITY_PERTURBATION = 0.05  # relative ±5% offset (fraction of baseline)
DENSITY_THRESHOLD_VARIATIONS = [
    round(BASELINE_DENSITY * (1.0 - DENSITY_PERTURBATION), 6),
    BASELINE_DENSITY,
    round(BASELINE_DENSITY * (1.0 + DENSITY_PERTURBATION), 6),
]  # -> [0.095, 0.1, 0.105]

# Backward-compatible alias: existing modules import
# DENSITY_THRESHOLD_BASELINE (e.g., preprocess/structural.py, main.py).
DENSITY_THRESHOLD_BASELINE = BASELINE_DENSITY

# Tractography Confidence Parameters (T041)
# Defined range for sensitivity analysis on tractography confidence thresholds
TRACTOGRAPHY_CONFIDENCE_THRESHOLDS = [0.0, 0.2, 0.4, 0.6, 0.8]

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
        DIR_DATA_DERIVED,
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
        "window_length_validation": list(WINDOW_LENGTH_VALIDATION),
        "window_step": WINDOW_STEP,
        "k_means_k": K_MEANS_K,
        "baseline_density": BASELINE_DENSITY,
        "density_perturbation": DENSITY_PERTURBATION,
        "density_threshold_variations": list(DENSITY_THRESHOLD_VARIATIONS),
        "density_threshold_baseline": DENSITY_THRESHOLD_BASELINE,
        "tractography_confidence_min": 0.0,
        "tractography_confidence_max": 1.0,
        "tractography_confidence_steps": 5,
        "tractography_confidence_thresholds": TRACTOGRAPHY_CONFIDENCE_THRESHOLDS,
        "random_seed": RANDOM_SEED,
        "paths": {
            "root": str(PROJECT_ROOT),
            "data_raw": str(DIR_DATA_RAW),
            "data_processed": str(DIR_DATA_PROCESSED),
            "data_derived": str(DIR_DATA_DERIVED),
            "data_logs": str(DIR_DATA_LOGS),
            "data_figures": str(DIR_DATA_FIGURES),
            "contracts": str(DIR_CONTRACTS),
        }
    }

# Initialize directories on import to satisfy T001 immediately
ensure_directories()
