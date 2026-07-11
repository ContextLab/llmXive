"""
Configuration module for the Ambient Noise Cognitive Flexibility study.
Contains reference tone parameters, thresholds, simulation settings,
logging infrastructure, and environment configuration management.
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("LOG_FILE", "study_pipeline.log")
LOG_FILE_PATH = os.path.join(LOGS_DIR, LOG_FILE)

# Reference Tone Parameters (FR-009)
# These define the ideal calibration signal used to validate device fidelity.
REFERENCE_TONE_PARAMS: Dict[str, Any] = {
    "frequency_hz": 1000.0,       # 1 kHz reference tone
    "duration_seconds": 2.0,      # 2 second burst
    "target_db": 60.0,            # Target SPL (A-weighted)
    "tolerance_db": 2.0,          # Acceptable error margin (FR-009)
    "sample_rate_hz": 44100,      # Standard audio sample rate
}

# Calibration Thresholds
CALIBRATION_ERROR_THRESHOLD_DB = 2.0  # Participants with >2dB error are flagged
CALIBRATION_MISSING_STATUS_FLAG = True

# Noise Bin Configuration (FR-007)
BIN_DURATION_SECONDS = 60  # 1-minute bins
MIN_VALID_PROPORTION = 0.80  # 80% valid logging required
MAX_GAP_PROPORTION = 0.20  # No single gap > 20% of session time

# CFI Calculation Parameters (FR-002)
RT_SD_THRESHOLD = 3.0  # Reaction time outlier threshold (SD)
ERROR_IMPUTE_VALUE = 0  # Default for missing errors if applicable
CFI_CORRELATION_THRESHOLD = 0.7  # r > 0.7 use RT diff only

# Model Parameters (FR-003)
VIF_COLLINEARITY_THRESHOLD = 5.0
LMM_RANDOM_INTERCEPT = "participant_id"
LMM_DEPENDENT_VAR = "cfi_score"

# Sensitivity Analysis (FR-005)
THRESHOLD_SWEEP_RANGES = {
    "low_noise_db": (30, 45),
    "moderate_noise_db": (45, 65),
    "high_noise_db": (65, 85)
}

def setup_logging(module_name: Optional[str] = None) -> logging.Logger:
    """
    Configures and returns a logger instance with file and console handlers.
    
    Args:
        module_name: Optional name for the logger. If None, uses 'root' or
                     the calling module's name.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(module_name if module_name else __name__)
    
    # Avoid adding handlers if already configured (e.g., in tests)
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # File Handler
    try:
        fh = logging.FileHandler(LOG_FILE_PATH)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)
    except (OSError, PermissionError) as e:
        # Fallback if log file cannot be written
        logger.warning(f"Could not create log file at {LOG_FILE_PATH}: {e}. Logging to console only.")
    
    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING) # Console only shows warnings by default to reduce noise
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)
    
    return logger

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration for logging."""
    return {
        "reference_tone": REFERENCE_TONE_PARAMS,
        "calibration_threshold_db": CALIBRATION_ERROR_THRESHOLD_DB,
        "bin_duration_seconds": BIN_DURATION_SECONDS,
        "log_level": LOG_LEVEL,
        "log_file": LOG_FILE_PATH,
    }

# Initialize a default logger for the module
logger = setup_logging()