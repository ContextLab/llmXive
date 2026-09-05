"""Configuration constants for the pipeline."""
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
    """Configuration container."""
    MAX_ELEMENTS = 5
    ROOM_TEMP_THRESHOLD_C = 25.0
    ROOM_TEMP_TOLERANCE_C = 5.0
    COMPOSITION_SUM_THRESHOLD = 95.0
    MIN_N_FOR_POWER = 50
    TARGET_N = 100
    VIF_THRESHOLD = 5.0
    R2_SENSITIVITY_THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    MIN_SAMPLES_WARNING = 50
    MIN_SAMPLES_TARGET = 100
    CV_FOLDS = 5
    BOOTSTRAP_ITERATIONS = 100
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

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

def get_vif_threshold() -> float:
    """Get the VIF threshold."""
    return Config.VIF_THRESHOLD

def get_r2_sensitivity_thresholds() -> List[float]:
    """Get the R2 sensitivity thresholds."""
    return Config.R2_SENSITIVITY_THRESHOLDS

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
