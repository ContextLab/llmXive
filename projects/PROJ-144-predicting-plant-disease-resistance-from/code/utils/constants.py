"""
Constants for the llmXive plant disease resistance prediction pipeline.

This module centralizes configuration values including random seeds,
file paths, and hypothesis testing thresholds to ensure reproducibility
and consistency across the project.
"""

import os
from pathlib import Path

# Project Root
# Assumes the project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Random Seeds ---
# Fixed seed for reproducibility across all random operations
RANDOM_STATE = 42

# --- File Paths ---
# Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Output Files
METRICS_FILE = RESULTS_DIR / "metrics.json"
SHAP_ANALYSIS_FILE = RESULTS_DIR / "shap_analysis.json"
PATHWAY_ANALYSIS_FILE = RESULTS_DIR / "pathway_analysis.json"
ARTIFACT_HASHES_FILE = STATE_DIR / "artifact_hashes.yaml"

# Data Files (Expected Outputs from US1)
BATCH_CORRECTED_MATRIX_FILE = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
LABELS_FILE = DATA_PROCESSED_DIR / "labels.csv"

# --- Hypothesis Thresholds ---
# Minimum balanced accuracy required to consider the model successful
MIN_BALANCED_ACCURACY = 0.75

# --- Model Hyperparameters ---
# Random Forest parameters
RF_N_ESTIMATORS = 500
RF_MAX_DEPTH = 10  # Default, can be tuned up to 20 via GridSearchCV

# --- Data Splitting ---
# Fraction of data to hold out for independent testing (used in T020)
# MUST be 0.20 as per task specification
HOLD_OUT_FRACTION = 0.20

# --- Preprocessing ---
# Maximum missing value percentage allowed before feature discarding
MAX_MISSING_FRACTION = 0.30

# --- Statistical Testing ---
# Number of permutations for null distribution generation
N_PERMUTATIONS = 1000

# FDR correction threshold
FDR_THRESHOLD = 0.05

# --- Sensitivity Analysis ---
# Decision cutoffs for sensitivity analysis (absolute diff)
SENSITIVITY_CUTOFFS = [0.01, 0.05, 0.1]

# --- VIF Diagnostics ---
# Variance Inflation Factor threshold for flagging collinearity
VIF_THRESHOLD = 5.0