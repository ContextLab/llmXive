"""
Configuration module for llmXive AgenticSTS pipeline.
Defines paths, seeds, and hyperparameters with environment variable overrides.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Project Root (assumed to be the directory containing 'code', 'data', 'tests')
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Hyperparameters (Explicit Constants with Env Overrides) ---
# Default values as specified in task T004
_DEFAULT_TOKEN_BUDGET = 4096
_DEFAULT_MIN_CONTEXT = 256
_DEFAULT_SEED = 42

# Load from environment variables if present, otherwise use defaults
TOKEN_BUDGET: int = int(os.getenv("LLMXIVE_TOKEN_BUDGET", _DEFAULT_TOKEN_BUDGET))
MIN_CONTEXT: int = int(os.getenv("LLMXIVE_MIN_CONTEXT", _DEFAULT_MIN_CONTEXT))
RANDOM_SEED: int = int(os.getenv("LLMXIVE_RANDOM_SEED", _DEFAULT_SEED))

# --- Paths ---
# Data Directories
RAW_DATA_DIR: Path = _PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR: Path = _PROJECT_ROOT / "data" / "processed"
FIGURES_DIR: Path = _PROJECT_ROOT / "figures"
MODELS_DIR: Path = _PROJECT_ROOT / "models"

# Specific File Paths
TRAJECTORIES_FILE: Path = RAW_DATA_DIR / "trajectories.csv"
ABLATION_LABELS_FILE: Path = PROCESSED_DATA_DIR / "ablation_labels_full.json"
UTILITY_LABELS_FILE: Path = PROCESSED_DATA_DIR / "utility_labels.csv"
TRAIN_SET_FILE: Path = PROCESSED_DATA_DIR / "train_set.csv"
HOLDOUT_SET_FILE: Path = PROCESSED_DATA_DIR / "holdout_set.csv"
CLASSIFIER_MODEL_FILE: Path = MODELS_DIR / "layer_utility_classifier.pkl"

# Output Reports
PROXY_VALIDATION_REPORT: Path = PROCESSED_DATA_DIR / "proxy_validation_report.json"
BASELINE_COMPARISON_CSV: Path = PROCESSED_DATA_DIR / "baseline_comparison.csv"
TOKEN_REDUCTION_VERIFICATION: Path = PROCESSED_DATA_DIR / "token_reduction_verification.json"
DIVERGENCE_REPORT: Path = PROCESSED_DATA_DIR / "divergence_report.json"
STATISTICAL_RESULTS: Path = PROCESSED_DATA_DIR / "statistical_results.json"

# --- Configuration Loading ---
def load_config_from_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration from a JSON file if provided, merging with defaults.
    If no path is provided, attempts to load from 'config.json' in project root.
    """
    if config_path is None:
        config_path = str(_PROJECT_ROOT / "config.json")

    config = {
        "token_budget": TOKEN_BUDGET,
        "min_context": MIN_CONTEXT,
        "random_seed": RANDOM_SEED,
        "paths": {
            "raw_data": str(RAW_DATA_DIR),
            "processed_data": str(PROCESSED_DATA_DIR),
            "figures": str(FIGURES_DIR),
            "models": str(MODELS_DIR),
        }
    }

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            file_config = json.load(f)
            # Merge file config into defaults (file overrides)
            for key, value in file_config.items():
                if key != "paths":
                    config[key] = value
                elif isinstance(value, dict):
                    config["paths"].update(value)

    return config

def ensure_directories() -> None:
    """Creates all required data and output directories if they don't exist."""
    for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR, MODELS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# --- Validation ---
def validate_config() -> None:
    """
    Validates that critical configuration values are within expected bounds.
    Raises ValueError if constraints are violated.
    """
    if TOKEN_BUDGET <= 0:
        raise ValueError(f"TOKEN_BUDGET must be positive, got {TOKEN_BUDGET}")
    if MIN_CONTEXT <= 0:
        raise ValueError(f"MIN_CONTEXT must be positive, got {MIN_CONTEXT}")
    if MIN_CONTEXT > TOKEN_BUDGET:
        raise ValueError(f"MIN_CONTEXT ({MIN_CONTEXT}) cannot exceed TOKEN_BUDGET ({TOKEN_BUDGET})")
    
    # Ensure data directories exist
    if not RAW_DATA_DIR.exists():
        # Warning only, as data might be generated later, but good to know
        print(f"Warning: Raw data directory {RAW_DATA_DIR} does not exist yet.")

# Execute validation on import (optional, can be disabled via env var)
if os.getenv("LLMXIVE_VALIDATE_CONFIG", "true").lower() == "true":
    validate_config()

# Ensure directories exist
ensure_directories()