"""
Core configuration management for the llmXive pipeline.
Defines paths, parameters, and validation logic.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from code.utils.logger import get_logger

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_DIR = PROJECT_ROOT / "state"
PROJECTS_DIR = STATE_DIR / "projects"

# Ensure these directories exist
def ensure_directories():
    """Create necessary directory structure if it doesn't exist."""
    dirs = [
        DATA_DIR,
        RESULTS_DIR,
        PROCESSED_DIR,
        STATE_DIR,
        PROJECTS_DIR,
        CODE_DIR / "data",
        CODE_DIR / "analysis",
        CODE_DIR / "validation",
        CODE_DIR / "utils",
        CODE_DIR / "config",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

# Configuration Constants
SAMPLING_RATE_THRESHOLD = 500  # Hz
MIN_ODDBALL_TRIALS = 100
MIN_STANDARD_TRIALS = 300

# Time Windows (ms)
AUDITORY_WINDOW = (100, 250)
VISUAL_WINDOW = (150, 350)

# OpenNeuro Dataset IDs
AUDITORY_DS_ID = "ds000246"
VISUAL_DS_ID = "ds000117"

# ICA & Filtering
ICA_COMPONENTS = 20
BANDPASS_LOW = 1.0
BANDPASS_HIGH = 40.0

# Source Localization
LEAD_FIELD_PATH = RESULTS_DIR / "lead_field.fif"
INV_OPERATOR_PATH = RESULTS_DIR / "inv_operator.fif"
HEAD_MODEL_PATH = RESULTS_DIR / "head_model.fif"

# Sensitivity Analysis
SENSITIVITY_SIGMAS = [5, 10, 15]  # mm

# Random Seed
RANDOM_SEED = 42

# Data Integrity
CHECKSUM_FILE = PROJECTS_DIR / "PROJ-779-cross-modal-comparison-of-neural-predict.yaml"

def get_config() -> Dict[str, Any]:
    """
    Returns a dictionary containing all configuration constants.
    This ensures a single source of truth for parameters.
    """
    ensure_directories()
    return {
        "project_root": PROJECT_ROOT,
        "code_dir": CODE_DIR,
        "data_dir": DATA_DIR,
        "results_dir": RESULTS_DIR,
        "processed_dir": PROCESSED_DIR,
        "state_dir": STATE_DIR,
        "projects_dir": PROJECTS_DIR,
        "sampling_rate_threshold": SAMPLING_RATE_THRESHOLD,
        "min_oddball_trials": MIN_ODDBALL_TRIALS,
        "min_standard_trials": MIN_STANDARD_TRIALS,
        "auditory_window": AUDITORY_WINDOW,
        "visual_window": VISUAL_WINDOW,
        "auditory_ds_id": AUDITORY_DS_ID,
        "visual_ds_id": VISUAL_DS_ID,
        "ica_components": ICA_COMPONENTS,
        "bandpass_low": BANDPASS_LOW,
        "bandpass_high": BANDPASS_HIGH,
        "lead_field_path": LEAD_FIELD_PATH,
        "inv_operator_path": INV_OPERATOR_PATH,
        "head_model_path": HEAD_MODEL_PATH,
        "sensitivity_sigmas": SENSITIVITY_SIGMAS,
        "random_seed": RANDOM_SEED,
        "checksum_file": CHECKSUM_FILE,
    }

# Log configuration status
logger = get_logger(__name__)
logger.info("Configuration module loaded. Paths initialized.")