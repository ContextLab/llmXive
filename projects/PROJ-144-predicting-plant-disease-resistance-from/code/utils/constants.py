"""
Global constants and configuration paths for the project.

This module centralizes all magic numbers, file paths, and hyperparameter
grids used across the research pipeline to ensure consistency and reproducibility.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Directory Paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_INTERMEDIATE_DIR = PROJECT_ROOT / "data" / "intermediate"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_DIR = PROJECT_ROOT / "state"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_PLOTS_DIR = RESULTS_DIR / "plots"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SPECS_DIR = PROJECT_ROOT / "specs"

# Random Seeds
RANDOM_STATE = 42

# Hypothesis Thresholds
# Minimum acceptable balanced accuracy for the model to be considered successful
BALANCED_ACC_THRESHOLD = 0.75

# Data Splitting
# Fraction of data to hold out for final independent evaluation
HOLD_OUT_FRACTION = 0.20

# Model Hyperparameters Grid
# Grid of max_depth values to search during Random Forest hyperparameter tuning
MAX_DEPTH_GRID = [5, 10, 15]

# File Names
STUDY_MANIFEST_FILE = "study_manifest.json"
METRICS_FILE = "metrics.json"
SHAP_ANALYSIS_FILE = "shap_analysis.json"
PATHWAY_ANALYSIS_FILE = "pathway_analysis.json"
ARTIFACT_HASHES_FILE = "artifact_hashes.yaml"
VIF_SCORES_FILE = "vif_scores.json"
SPLIT_INDICES_FILE = "split_indices.json"
ALIGNMENT_MISSING_FILE = "alignment_missing.json"

# Ensure directories exist (soft fail for constants module)
def ensure_dirs():
    """Create all project directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR,
        TESTS_DIR, STATE_DIR, RESULTS_DIR, RESULTS_PLOTS_DIR,
        CONTRACTS_DIR, SPECS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)