"""
Configuration module for seed pinning and path management.

This module centralizes all project-wide constants, random seeds, and directory paths
to ensure reproducibility and consistent file system access across the llmXive pipeline.

It extends the root `config.py` by providing specific utilities for the
PROJ-964 follow-up tasks.
"""

import os
import random
from pathlib import Path
from typing import Dict, Any

# Project Root Configuration
# Assumes this file is at code/utils/config.py, so root is 3 levels up
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent

# Ensure we are in the correct project context
if not (PROJECT_ROOT / "code").exists():
    raise RuntimeError(
        f"Project root {PROJECT_ROOT} does not contain a 'code' directory. "
        "Please ensure this script is run from within the correct project structure."
    )

# --- Reproducibility Seeds ---
# Pinned seeds for numpy, torch, and random to ensure deterministic behavior
# across runs. These must be used before any data loading or model training.
SEED = 42
TORCH_SEED = 42
NUMPY_SEED = 42
RANDOM_SEED = 42

# --- Path Configuration ---
# Define all major directory paths relative to the project root

CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"

# Subdirectories within data/
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_MODELS = DATA_DIR / "models"
DATA_METRICS = DATA_DIR / "metrics"

# Subdirectories within code/
CODE_MODELS = CODE_DIR / "models"
CODE_INFERENCE = CODE_DIR / "inference"
CODE_EVALUATION = CODE_DIR / "evaluation"
CODE_UTILS = CODE_DIR / "utils"
CODE_TASKS = CODE_DIR / "tasks"

# Specific output paths required by tasks
STATE_YAML_PATH = STATE_DIR / "state.yaml"
CONFIG_YAML_PATH = CODE_DIR / "config.yaml"

# Dataset specific paths
VOXCELEB2_LOCAL_PATH = DATA_RAW / "voxceleb2"

# Model checkpoints
ESTIMATOR_CHECKPOINT_PATH = DATA_MODELS / "estimator_checkpoint.pt"

# Metrics outputs
BASELINE_COMPARISON_PATH = DATA_METRICS / "baseline_comparison.json"
TOST_RESULTS_PATH = DATA_METRICS / "tost_results.csv"
POWER_ANALYSIS_PATH = DATA_METRICS / "power_analysis.json"
UNCERTAINTY_CALIBRATION_PATH = DATA_METRICS / "uncertainty_calibration.json"

# Counterfactual data
COUNTERFACTUAL_GROUND_TRUTH_PATH = DATA_PROCESSED / "counterfactual_ground_truth.parquet"
COUNTERFACTUAL_INDICES_PATH = DATA_PROCESSED / "counterfactual_indices.parquet"

# --- Thresholds & Hyperparameters (Configurable) ---
# These values are referenced in T013 (event detection) and T014 (preprocessing)

# Audio energy threshold (dB) for detecting interruptions/pauses
# Defined here to be imported by extract_latents.py
AUDIO_ENERGY_THRESHOLD_DB = -30.0

# Memory limits (in GB) for graceful degradation
MEMORY_LIMIT_GB = 7.0
MINIMUM_SAMPLE_SIZE = 1000

# Time limits (in seconds) for training jobs
TRAINING_TIMEOUT_SECONDS = 6 * 3600  # 6 hours

# Statistical test parameters
TOST_DELTA = 0.05
CORRELATION_THRESHOLD = 0.7

# --- Configuration Dictionary ---
# Aggregates all paths and settings for easy passing to downstream modules

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration state.
    
    This function is compatible with the root `code/config.py` interface
    but provides project-specific details.
    
    Returns:
        Dict containing seed values, path strings, and key thresholds.
    """
    return {
        "seeds": {
            "global": SEED,
            "torch": TORCH_SEED,
            "numpy": NUMPY_SEED,
            "random": RANDOM_SEED
        },
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "data_raw": str(DATA_RAW),
            "data_processed": str(DATA_PROCESSED),
            "data_models": str(DATA_MODELS),
            "state_yaml": str(STATE_YAML_PATH)
        },
        "thresholds": {
            "audio_energy_db": AUDIO_ENERGY_THRESHOLD_DB,
            "memory_limit_gb": MEMORY_LIMIT_GB,
            "tost_delta": TOST_DELTA
        }
    }

def set_seed(seed: int = SEED) -> None:
    """
    Sets the random seeds for reproducibility across all libraries.
    
    Args:
        seed: The integer seed value to use. Defaults to the global SEED.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    try:
        import numpy as np
        np.random.seed(NUMPY_SEED)
    except ImportError:
        pass
        
    try:
        import torch
        torch.manual_seed(TORCH_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(TORCH_SEED)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

# Export public API
__all__ = [
    "PROJECT_ROOT",
    "DATA_RAW",
    "DATA_PROCESSED",
    "DATA_MODELS",
    "STATE_YAML_PATH",
    "SEED",
    "AUDIO_ENERGY_THRESHOLD_DB",
    "MEMORY_LIMIT_GB",
    "TRAINING_TIMEOUT_SECONDS",
    "TOST_DELTA",
    "get_config_summary",
    "set_seed"
]

# Ensure seeds are set immediately upon import to prevent accidental non-determinism
# Note: In production pipelines, this might be called explicitly in the entry point,
# but for research reproducibility, setting it here ensures consistency.
# set_seed() # Uncomment if immediate setting is required on import, 
             # otherwise rely on explicit calls in entry scripts.