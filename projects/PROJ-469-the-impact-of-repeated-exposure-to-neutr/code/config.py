"""
Configuration settings for the llmXive project: The Impact of Repeated Exposure to Political News on Implicit Bias.

This module defines:
- Random seeds for reproducibility
- File system paths relative to the project root
- Statistical thresholds (alpha levels)
- Hyperparameters for robustness checks (bootstrap count)
"""
import os
from pathlib import Path

# ==============================================================================
# Project Root and Directory Paths
# ==============================================================================
# Determine the project root based on the location of this file (code/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory structure
DIR_RAW_DATA = _PROJECT_ROOT / "data" / "raw"
DIR_PROCESSED_DATA = _PROJECT_ROOT / "data" / "processed"
DIR_RESULTS = _PROJECT_ROOT / "results"
DIR_LOGS = _PROJECT_ROOT / "logs"
DIR_FIGURES = _PROJECT_ROOT / "results" / "figures"

# Ensure directories exist (optional initialization helper)
def ensure_dirs():
    """Create all required directories if they do not exist."""
    for d in [DIR_RAW_DATA, DIR_PROCESSED_DATA, DIR_RESULTS, DIR_LOGS, DIR_FIGURES]:
        d.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# Random Seeds
# ==============================================================================
# Fixed seeds for reproducibility across numpy, random, and tensorflow/pytorch if used
SEED_BASE = 42
SEED_NP = 42
SEED_RANDOM = 42
SEED_SPLITS = 42

# ==============================================================================
# Statistical Thresholds
# ==============================================================================
# Alpha levels for hypothesis testing and significance evaluation
ALPHA_LEVELS = [0.01, 0.05, 0.10]
DEFAULT_ALPHA = 0.05

# ==============================================================================
# Robustness & Hyperparameters
# ==============================================================================
# Number of bootstrap resamples for confidence interval estimation
BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 42

# MICE Imputation settings
MICE_N_IMPUTATIONS = 5
MICE_MAX_ITER = 50
MISSINGNESS_THRESHOLD = 0.50  # Halt if > 50% missing in a column

# ==============================================================================
# Data Schema & Column Mappings
# ==============================================================================
# Expected columns in the raw dataset after fetching
RAW_DATA_COLUMNS = [
    "IAT_D_score",
    "political_ideology",
    "news_exposure_freq",
    "age",
    "gender",
    "education"
]

# Derived variable names
DERIVED_VARS = {
    "news_exposure_z": "news_exposure_z",
    "ideology_binary": "ideology_binary"
}

# ==============================================================================
# Output File Paths
# ==============================================================================
# Primary output files
OUTPUT_IMPUTED_DATA = DIR_PROCESSED_DATA / "imputed_data.csv"
OUTPUT_MODEL_SUMMARY = DIR_RESULTS / "model_summary.csv"
OUTPUT_DIAGNOSTICS = DIR_RESULTS / "diagnostics.csv"
OUTPUT_POWER_ANALYSIS = DIR_RESULTS / "power_analysis.csv"
OUTPUT_POWER_DESIGN = DIR_RESULTS / "power_design.csv"
OUTPUT_BOOTSTRAP_RESULTS = DIR_RESULTS / "bootstrap_results.csv"
OUTPUT_ALPHA_SWEEP = DIR_RESULTS / "alpha_sweep.csv"
OUTPUT_BINARY_MODEL = DIR_RESULTS / "binary_model.csv"
OUTPUT_ROBUSTNESS_METRICS = DIR_RESULTS / "robustness_metrics.csv"
OUTPUT_REPORT_PDF = DIR_RESULTS / "report.pdf"

# Log file path
LOG_FILE = DIR_LOGS / "pipeline.log"

# ==============================================================================
# Constants for Modeling
# ==============================================================================
MODEL_FORMULA_PRIMARY = "IAT_D_score ~ news_exposure_z * political_ideology"
MODEL_FORMULA_COVARIATES = "IAT_D_score ~ news_exposure_z * political_ideology + age + gender + education"
MODEL_FORMULA_BINARY = "IAT_D_score ~ news_exposure_z * ideology_binary"