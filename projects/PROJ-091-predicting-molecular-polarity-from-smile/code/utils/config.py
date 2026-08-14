"""
Global configuration management for the molecular polarity prediction pipeline.

This module provides:
- Hardcoded random seeds for reproducibility (required by spec).
- Path resolution utilities relative to the project root.
- Hyperparameter defaults loaded from `code/config.yaml` if present,
  falling back to internal defaults.

Constraint: Random seeds are hardcoded in this file to ensure
deterministic execution across runs, regardless of external config changes.

Refactored to use Python dataclasses (T039a).
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

# --------------------------------------------------------------------------
# Hardcoded Global Seeds (Reproducibility Constraint)
# These MUST NOT be overridden by external configuration files.
# --------------------------------------------------------------------------
RANDOM_SEED: int = 42
NUMPY_SEED: int = 42
PYTORCH_SEED: int = 42  # Included for future compatibility, though not currently used
LIGHTGBM_SEED: int = 42

# --------------------------------------------------------------------------
# Dataclass Definitions for Configuration
# --------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Configuration for the LightGBM model."""
    n_estimators: int = 1000
    learning_rate: float = 0.05
    num_leaves: int = 31
    max_depth: int = -1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_alpha: float = 0.0
    reg_lambda: float = 1.0
    random_state: int = LIGHTGBM_SEED
    verbose: int = -1
    n_jobs: int = -1

@dataclass
class PreprocessingConfig:
    """Configuration for data preprocessing."""
    nan_threshold_drop: float = 0.05
    nan_strategy: str = "median"
    correlation_threshold: float = 0.85

@dataclass
class TrainingConfig:
    """Configuration for training parameters."""
    test_size: float = 0.2
    cv_folds: int = 5
    random_state: int = RANDOM_SEED

@dataclass
class PipelineConfig:
    """
    Main configuration container holding all sub-configurations.
    This replaces the previous dictionary-based approach.
    """
    model: ModelConfig = field(default_factory=ModelConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for JSON/YAML serialization."""
        return {
            "model": asdict(self.model),
            "preprocessing": asdict(self.preprocessing),
            "training": asdict(self.training),
        }

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
# Default Hyperparameters (as dataclass defaults)
# --------------------------------------------------------------------------
# These align with the LightGBM model requirements.
# Note: Random seeds in defaults are hardcoded constants to enforce reproducibility.
DEFAULT_HYPERPARAMETERS: PipelineConfig = PipelineConfig()

def load_hyperparameters(config_path: Optional[Path] = None) -> PipelineConfig:
    """
    Load hyperparameters from a YAML configuration file and merge with defaults.

    Args:
        config_path: Path to the YAML config file. Defaults to code/config.yaml.

    Returns:
        A PipelineConfig dataclass instance containing the merged configuration.
        Random seeds from the YAML are IGNORED to enforce reproducibility constraints.

    Raises:
        FileNotFoundError: If the config file does not exist (returns defaults).
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = config_path or CONFIG_FILE_PATH
    
    # Start with a fresh copy of defaults
    config = DEFAULT_HYPERPARAMETERS

    if not path.exists():
        return config

    try:
        with open(path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML config at {path}: {e}")

    # Deep merge logic for nested dicts
    def deep_merge(base_dict: Dict, override_dict: Dict) -> Dict:
        result = base_dict.copy()
        for key, value in override_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # Convert dataclass to dict for merging
    base_dict = config.to_dict()
    merged_dict = deep_merge(base_dict, yaml_config)

    # ENFORCEMENT: Override random seeds with hardcoded values regardless of YAML
    if "model" in merged_dict:
        merged_dict["model"]["random_state"] = LIGHTGBM_SEED
    if "training" in merged_dict:
        merged_dict["training"]["random_state"] = RANDOM_SEED

    # Reconstruct dataclass from merged dict
    # We manually map the nested dicts back to dataclasses
    model_cfg = ModelConfig(**merged_dict.get("model", {}))
    preproc_cfg = PreprocessingConfig(**merged_dict.get("preprocessing", {}))
    train_cfg = TrainingConfig(**merged_dict.get("training", {}))

    return PipelineConfig(model=model_cfg, preprocessing=preproc_cfg, training=train_cfg)

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
        f"  - Model Estimators: {hp.model.n_estimators}\n"
        f"  - Learning Rate: {hp.model.learning_rate}\n"
        f"  - NaN Drop Threshold: {hp.preprocessing.nan_threshold_drop}\n"
        f"  - Data Raw Dir: {DATA_RAW_DIR}\n"
        f"  - Data Processed Dir: {DATA_PROCESSED_DIR}"
    )

# Expose constants and classes directly for easy import
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
    "PipelineConfig",
    "ModelConfig",
    "PreprocessingConfig",
    "TrainingConfig",
    "DEFAULT_HYPERPARAMETERS",
    "load_hyperparameters",
    "get_config_summary",
]
