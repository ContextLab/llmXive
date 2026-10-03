"""Configuration constants for the pipeline.

This module defines all core configuration constants used across the
solder hardness prediction pipeline. It serves as the single source of truth
for thresholds, limits, and operational parameters.

CRITICAL: Do NOT include SENSITIVITY_EXTEND_STEP in this file.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from utils.error_handlers import ConfigurationError

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_OUTPUTS_DIR = DATA_DIR / "outputs"
CODE_DIR = PROJECT_ROOT / "code"
MODELS_DIR = PROJECT_ROOT / "models"

class Config:
    """Configuration container for all pipeline constants."""
    
    # --- T006 Constants (Task Requirement) ---
    # Maximum number of elements allowed in an alloy composition
    MAX_ELEMENTS: int = 5
    
    # Target room temperature for measurements (Celsius)
    ROOM_TEMP_THRESHOLD_C: float = 25.0
    
    # Tolerance for room temperature measurements (Celsius)
    ROOM_TEMP_TOLERANCE_C: float = 5.0
    
    # Minimum sum of elemental percentages required for valid composition
    COMPOSITION_SUM_THRESHOLD: float = 95.0
    
    # Minimum number of samples required for statistical power
    MIN_N_FOR_POWER: int = 50
    
    # Target number of samples for the dataset
    TARGET_N: int = 100
    
    # --- Other Constants (Existing/Required by Pipeline) ---
    
    # Fixed sensitivity thresholds for R2 analysis [low, medium, high]
    SENSITIVITY_THRESHOLDS: List[float] = [0.3, 0.6, 0.8]
    
    # Rounding step for sensitivity analysis
    SENSITIVITY_ROUND_STEP: float = 0.05
    
    # VIF threshold for collinearity detection
    VIF_THRESHOLD: float = 5.0
    
    # Deprecated step (kept for API compatibility, set to 0.0 as per T006)
    SENSITIVITY_EXTEND_STEP: float = 0.0
    
    # R2 sensitivity thresholds (legacy, kept for compatibility)
    R2_SENSITIVITY_THRESHOLDS: List[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    # Minimum samples for warning
    MIN_SAMPLES_WARNING: int = 50
    
    # Minimum samples for target
    MIN_SAMPLES_TARGET: int = 100
    
    # Number of CV folds
    CV_FOLDS: int = 5
    
    # Number of bootstrap iterations
    BOOTSTRAP_ITERATIONS: int = 100
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_config() -> Config:
    """Get the configuration object."""
    return Config()

def get_data_raw_dir() -> Path:
    """Get the raw data directory path."""
    return DATA_RAW_DIR

def get_data_processed_dir() -> Path:
    """Get the processed data directory path."""
    return DATA_PROCESSED_DIR

def get_data_outputs_dir() -> Path:
    """Get the outputs directory path."""
    return DATA_OUTPUTS_DIR

def get_models_dir() -> Path:
    """Get the models directory path."""
    return MODELS_DIR

def get_composition_sum_threshold() -> float:
    """Get the composition sum threshold."""
    return Config.COMPOSITION_SUM_THRESHOLD

def get_max_elements() -> int:
    """Get the maximum number of elements allowed."""
    return Config.MAX_ELEMENTS

def get_room_temp_threshold() -> float:
    """Get the room temperature threshold in Celsius."""
    return Config.ROOM_TEMP_THRESHOLD_C

def get_room_temp_tolerance() -> float:
    """Get the room temperature tolerance in Celsius."""
    return Config.ROOM_TEMP_TOLERANCE_C

def get_min_n_for_power() -> int:
    """Get the minimum N for statistical power."""
    return Config.MIN_N_FOR_POWER

def get_target_n() -> int:
    """Get the target sample size N."""
    return Config.TARGET_N

def get_vif_threshold() -> float:
    """Get the VIF threshold."""
    return Config.VIF_THRESHOLD

def get_r2_sensitivity_thresholds() -> List[float]:
    """Get the R2 sensitivity thresholds (deprecated: use get_sensitivity_thresholds)."""
    return Config.R2_SENSITIVITY_THRESHOLDS

def get_sensitivity_thresholds() -> List[float]:
    """Get the fixed sensitivity thresholds [0.3, 0.6, 0.8]."""
    return Config.SENSITIVITY_THRESHOLDS

def get_sensitivity_round_step() -> float:
    """Get the rounding step for sensitivity analysis."""
    return Config.SENSITIVITY_ROUND_STEP

def get_min_samples_warning() -> int:
    """Get the minimum samples for warning."""
    return Config.MIN_SAMPLES_WARNING

def get_min_samples_target() -> int:
    """Get the minimum samples for target."""
    return Config.MIN_SAMPLES_TARGET

def get_cv_folds() -> int:
    """Get the number of CV folds."""
    return Config.CV_FOLDS

def get_bootstrap_iterations() -> int:
    """Get the number of bootstrap iterations."""
    return Config.BOOTSTRAP_ITERATIONS

def get_log_level() -> str:
    """Get the log level."""
    return Config.LOG_LEVEL

def get_log_format() -> str:
    """Get the log format."""
    return Config.LOG_FORMAT