"""
Configuration settings for the llmXive automated science pipeline.

This module defines all project-wide constants, paths, random seeds,
and baseline parameters required for reproducibility and consistent execution.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# --- Project Paths ---
# Determine the root directory based on the location of this config file
_ROOT = Path(__file__).resolve().parent.parent

# Standardized directory structure
DATA_DIR = _ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_LOGS_DIR = DATA_DIR / "logs"
DATA_FIGURES_DIR = DATA_DIR / "figures"

CODE_DIR = _ROOT / "code"
CONTRACTS_DIR = _ROOT / "contracts"
TESTS_DIR = _ROOT / "tests"
SPECS_DIR = _ROOT / "specs"

# Output file paths (relative to project root)
STRUCTURAL_METRICS_CSV = DATA_PROCESSED_DIR / "structural_metrics.csv"
DYNAMIC_METRICS_CSV = DATA_PROCESSED_DIR / "dynamic_metrics.csv"
CORRELATION_RESULTS_CSV = DATA_PROCESSED_DIR / "correlation_results.csv"
EXCLUSION_LOG_JSON = DATA_LOGS_DIR / "exclusion_log.json"
FINAL_REPORT_JSON = DATA_PROCESSED_DIR / "final_report.json"

# --- Random Seeds ---
# Fixed seeds for reproducibility across numpy, sklearn, etc.
RANDOM_SEED = 42
NUMPY_SEED = 42
SKLEARN_SEED = 42

# --- Baseline Parameters (User Story 1 & 3) ---
# Windowing parameters for dynamic functional connectivity
WINDOW_LENGTH_TR = 30  # Baseline: 30 TR window
WINDOW_STEP_TR = 1     # 1 TR step size
WINDOW_LENGTH_TR_SENSITIVITY = 20  # Sensitivity check: 20 TR window (FR-006, SC-002)

# Clustering parameters
K_STATES = 5           # Number of dynamic states (k=5)
LOO_ENABLED = True     # Enable Leave-One-Out clustering to prevent circular correlation

# --- Hyperparameters (User Story 2) ---
# Structural network density thresholds
DENSITY_THRESHOLD_BASELINE = 0.10  # 10% density for structural graph
DENSITY_THRESHOLD_TOLERANCE = 0.05 # ±5% variation for robustness check (±5% of baseline)

# Statistical testing parameters
ALPHA_NORMALITY = 0.05   # Alpha level for Shapiro-Wilk normality test
ALPHA_CORRELATION = 0.05 # Alpha level for correlation significance
FDR_Q = 0.05             # False Discovery Rate threshold (Benjamini-Hochberg)

# --- Data Loading Configuration ---
# HCP OpenNeuro dataset identifiers
HCP_DATASET_ID = "hcp-750"  # Placeholder for specific dataset version
HCP_URL_TEMPLATE = "https://openneuro.org/datasets/ds000030" # Example base URL

# --- Execution Constraints ---
# CPU-only constraints
MAX_WORKERS = 4            # Maximum parallel workers for CPU-bound tasks
MAX_MEMORY_GB = 16         # Memory limit in GB

# --- Helper Functions ---
def get_config_dict() -> Dict[str, Any]:
    """
    Returns a dictionary of all configuration parameters.
    Useful for logging or passing to downstream functions.
    """
    return {
        "paths": {
            "root": str(_ROOT),
            "data_raw": str(DATA_RAW_DIR),
            "data_processed": str(DATA_PROCESSED_DIR),
            "data_logs": str(DATA_LOGS_DIR),
            "data_figures": str(DATA_FIGURES_DIR),
            "contracts": str(CONTRACTS_DIR),
        },
        "seeds": {
            "random": RANDOM_SEED,
            "numpy": NUMPY_SEED,
            "sklearn": SKLEARN_SEED,
        },
        "baseline": {
            "window_length_tr": WINDOW_LENGTH_TR,
            "window_step_tr": WINDOW_STEP_TR,
            "window_length_tr_sensitivity": WINDOW_LENGTH_TR_SENSITIVITY,
            "k_states": K_STATES,
            "loo_enabled": LOO_ENABLED,
        },
        "hyperparameters": {
            "density_threshold": DENSITY_THRESHOLD_BASELINE,
            "density_tolerance": DENSITY_THRESHOLD_TOLERANCE,
            "alpha_normality": ALPHA_NORMALITY,
            "alpha_correlation": ALPHA_CORRELATION,
            "fdr_q": FDR_Q,
        },
        "execution": {
            "max_workers": MAX_WORKERS,
            "max_memory_gb": MAX_MEMORY_GB,
        }
    }

def ensure_directories():
    """
    Creates all required data directories if they do not exist.
    """
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_LOGS_DIR, DATA_FIGURES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)