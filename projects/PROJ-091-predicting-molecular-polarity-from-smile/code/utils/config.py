"""
Global configuration management for the molecular polarity prediction pipeline.

This module provides:
- Hardcoded random seeds for reproducibility (required by spec).
- Path resolution utilities relative to the project root.
- Hyperparameter defaults loaded from `code/config.yaml` if present,
  falling back to internal defaults.

Constraint: Random seeds are hardcoded in this file to ensure
deterministic execution across runs, regardless of external config changes.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# --------------------------------------------------------------------------
# Hardcoded Global Seeds (Reproducibility Constraint)
# These MUST NOT be overridden by external configuration files.
# --------------------------------------------------------------------------
RANDOM_SEED: int = 42
NUMPY_SEED: int = 42
PYTORCH_SEED: int = 42  # Included for future compatibility, though not currently used
LIGHTGBM_SEED: int = 42

# --------------------------------------------------------------------------
# Path Configuration
# --------------------------------------------------------------------------
def _get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the project structure:
    <root>/
      code/
        utils/
          config.py
      data/
      tests/
      specs/
    """
    current_file = Path(__file__).resolve()
    # Traverse up: config.py -> utils -> code -> root
    return current_file.parent.parent.parent

PROJECT_ROOT: Path = _get_project_root()

# Path constants
DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
DATA_ANALYSIS_DIR: Path = DATA_PROCESSED_DIR / "analysis"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
CODE_DIR: Path = PROJECT_ROOT / "code"
CONFIG_FILE_PATH: Path = CODE_DIR / "config.yaml"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Hyperparameter Defaults & YAML Loading
# --------------------------------------------------------------------------
# Default hyperparameters used if config.yaml is missing or keys are absent.
# These align with the LightGBM model requirements.
DEFAULT_HYPERPARAMETERS: Dict[str, Any] = {
    "model": {
        "n_estimators": 1000,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": -1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.0,
        "reg_lambda": 1.0,
        "random_state": LIGHTGBM_SEED,
        "verbose": -1,
        "n_jobs": -1,
    },
    "preprocessing": {
        "nan_threshold_drop": 0.05,  # Drop column if >5% missing
        "nan_strategy": "median",
        "correlation_threshold": 0.85,  # Threshold for target correlation filtering
    },
    "training": {
        "test_size": 0.2,
        "cv_folds": 5,
        "random_state": RANDOM_SEED,
    },
}

def load_hyperparameters(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load hyperparameters from a YAML configuration file.

    Args:
        config_path: Path to the YAML config file. Defaults to code/config.yaml.

    Returns:
        A dictionary containing the merged configuration (defaults + YAML overrides).
        Random seeds from the YAML are IGNORED to enforce reproducibility constraints.

    Raises:
        FileNotFoundError: If the config file does not exist (returns defaults).
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = config_path or CONFIG_FILE_PATH
    config = DEFAULT_HYPERPARAMETERS.copy()

    if not path.exists():
        # Log warning or handle silently? For now, return defaults.
        return config

    try:
        with open(path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML config at {path}: {e}")

    # Deep merge logic (simple recursive merge for nested dicts)
    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # Merge YAML into defaults
    config = deep_merge(config, yaml_config)

    # ENFORCEMENT: Override random seeds with hardcoded values regardless of YAML
    if "model" in config:
        config["model"]["random_state"] = LIGHTGBM_SEED
    if "training" in config:
        config["training"]["random_state"] = RANDOM_SEED

    return config

def get_config_summary() -> str:
    """
    Returns a string summary of the current configuration state.
    Useful for logging at the start of a pipeline run.
    """
    hp = load_hyperparameters()
    return (
        f"Config Summary:\n"
        f"  - Project Root: {PROJECT_ROOT}\n"
        f"  - Hardcoded Seeds: {RANDOM_SEED}, {NUMPY_SEED}, {LIGHTGBM_SEED}\n"
        f"  - Model Estimators: {hp['model']['n_estimators']}\n"
        f"  - Learning Rate: {hp['model']['learning_rate']}\n"
        f"  - NaN Drop Threshold: {hp['preprocessing']['nan_threshold_drop']}\n"
        f"  - Data Raw Dir: {DATA_RAW_DIR}\n"
        f"  - Data Processed Dir: {DATA_PROCESSED_DIR}"
    )

# Expose constants directly for easy import
__all__ = [
    "RANDOM_SEED",
    "NUMPY_SEED",
    "LIGHTGBM_SEED",
    "PROJECT_ROOT",
    "DATA_RAW_DIR",
    "DATA_PROCESSED_DIR",
    "DATA_ANALYSIS_DIR",
    "LOGS_DIR",
    "CONFIG_FILE_PATH",
    "DEFAULT_HYPERPARAMETERS",
    "load_hyperparameters",
    "get_config_summary",
]
