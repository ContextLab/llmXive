"""
Configuration and logging setup for the ambient noise project.
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent.parent

# Data directories
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "data" / "models"

# Noise categorization thresholds (dB)
NOISE_THRESHOLD_LOW = 45
NOISE_THRESHOLD_HIGH = 65

# Data validation thresholds
VALID_LOGGING_THRESHOLD = 0.80  # 80% of hours must have logs
GAP_THRESHOLD = 0.20  # Single gap >20% of total time triggers exclusion
CALIBRATION_ERROR_THRESHOLD = 2.0  # dB
REACTION_TIME_OUTLIER_SD = 3.0  # Standard deviations
MAD_OUTLIER_THRESHOLD = 3.5  # Median Absolute Deviation threshold

# Statistical analysis parameters
CFI_CORRELATION_THRESHOLD = 0.7  # Correlation between RT and Error
VIF_THRESHOLD = 5.0  # Variance Inflation Factor threshold for collinearity

# Target sample size
TARGET_SAMPLE_SIZE = 150


def setup_logging(module_name: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger instance with file and console handlers.
    
    Args:
        module_name: Optional name for the logger. If None, uses 'root' or
                    the calling module's name.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    if module_name is None:
        module_name = "ambient_noise_analysis"
    
    logger = logging.getLogger(module_name)
    
    # Only configure if not already configured
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    logs_dir = ROOT_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(logs_dir / f"{module_name}.log")
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration for logging.
    
    Returns:
        Dict[str, Any]: Configuration summary.
    """
    return {
        "root_dir": str(ROOT_DIR),
        "raw_data_dir": str(RAW_DATA_DIR),
        "processed_data_dir": str(PROCESSED_DATA_DIR),
        "models_dir": str(MODELS_DIR),
        "noise_threshold_low": NOISE_THRESHOLD_LOW,
        "noise_threshold_high": NOISE_THRESHOLD_HIGH,
        "valid_logging_threshold": VALID_LOGGING_THRESHOLD,
        "gap_threshold": GAP_THRESHOLD,
        "calibration_error_threshold": CALIBRATION_ERROR_THRESHOLD,
        "reaction_time_outlier_sd": REACTION_TIME_OUTLIER_SD,
        "cfi_correlation_threshold": CFI_CORRELATION_THRESHOLD,
        "vif_threshold": VIF_THRESHOLD,
        "target_sample_size": TARGET_SAMPLE_SIZE,
    }
