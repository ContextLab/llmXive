"""
Configuration for the Dynamic Socio-Cognitive State Injection project.

This module defines all project-wide constants, paths, and hyperparameters.
"""

import logging
import logging.handlers
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# Random Seeds for Reproducibility
# ============================================================================
RANDOM_SEED = 42
NUMPY_SEED = 42
TORCH_SEED = 42

def set_all_seeds(seed: int = RANDOM_SEED) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: numpy and torch seeds are set in their respective modules

# ============================================================================
# File Paths
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for dir_path in [DATA_RAW, DATA_PROCESSED, DATA_RESULTS, CODE_DIR, TESTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Hyperparameters
# ============================================================================
TURN_WINDOW_SIZE = 3
STATISTICAL_VARIANCE_TOLERANCE = 0.01
CONFIDENCE_THRESHOLD = 0.75
TARGET_OVERSAMPLING_RATIO = 0.40

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging(log_level: int = LOG_LEVEL) -> logging.Logger:
    """Setup logging infrastructure."""
    ensure_directories()

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(DATA_RESULTS / "experiment.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    return logger

# ============================================================================
# Experiment Conditions
# ============================================================================
class ExperimentConditionFilter:
    """Filter for experiment conditions."""

    ADAPTER = "adapter"
    STATIC = "static"
    NEUTRAL_MONITORING = "neutral-monitoring"

# ============================================================================
# Configuration Summary
# ============================================================================
def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "random_seed": RANDOM_SEED,
        "turn_window_size": TURN_WINDOW_SIZE,
        "statistical_variance_tolerance": STATISTICAL_VARIANCE_TOLERANCE,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "target_oversampling_ratio": TARGET_OVERSAMPLING_RATIO,
        "data_raw": str(DATA_RAW),
        "data_processed": str(DATA_PROCESSED),
        "data_results": str(DATA_RESULTS),
    }
