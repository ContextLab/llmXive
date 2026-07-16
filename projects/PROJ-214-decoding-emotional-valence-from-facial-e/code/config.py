"""
Configuration module for the llmXive emotional valence decoding pipeline.

This module defines all project paths, hyperparameters, random seeds,
and DEAP dataset metadata required by the pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any, Final

# ============================================================================
# Project Paths
# ============================================================================
PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
CODE_DIR: Final = PROJECT_ROOT / "code"
DATA_DIR: Final = PROJECT_ROOT / "data"
TESTS_DIR: Final = PROJECT_ROOT / "tests"
FIGURES_DIR: Final = PROJECT_ROOT / "figures"
SPECS_DIR: Final = PROJECT_ROOT / "specs"

# Data subdirectories
DATA_RAW: Final = DATA_DIR / "raw"
DATA_PROCESSED: Final = DATA_DIR / "processed"
DATA_MODELS: Final = DATA_DIR / "models"

# Output paths
EXCLUSIONS_LOG: Final = DATA_PROCESSED / "exclusions.log"
MODEL_BUNDLE_PATH: Final = DATA_MODELS / "model_bundle.pkl"
RESULTS_JSON: Final = DATA_PROCESSED / "results.json"
REPORT_MD: Final = PROJECT_ROOT / "paper.md"

# ============================================================================
# DEAP Dataset Metadata
# ============================================================================
# Verified HuggingFace source as per T005
DEAP_HF_DATASET_ID: Final = "emre-ozgür/DEAP-EMG"
DEAP_HF_SPLIT: Final = "train"  # Dataset is typically small enough to load fully

# Target EMG channels for analysis
TARGET_CHANNELS: Final = [
    "corrugator_supercilii",  # frown muscle
    "zygomaticus_major",      # smile muscle
    "orbicularis_oculi"       # eye blink/squint muscle
]

# DEAP specific parameters
DEAP_SAMPLE_RATE: Final = 512  # Hz
DEAP_SIGNAL_LENGTH: Final = 60  # seconds per trial
DEAP_NUM_TRIALS: Final = 40     # standard DEAP protocol
DEAP_NUM_SUBJECTS: Final = 32   # standard DEAP protocol

# Valence threshold for binarization (neutral point)
# Values > 5.0 are Positive, <= 5.0 are Negative
VALENCE_THRESHOLD: Final = 5.0

# ============================================================================
# Preprocessing Hyperparameters
# ============================================================================
# Filtering
FILTER_LOW_CUTOFF: Final = 1.0       # Hz (High-pass)
FILTER_HIGH_CUTOFF: Final = 45.0     # Hz (Low-pass)
FILTER_ORDER: Final = 4
NOTCH_FREQUENCY: Final = 50.0          # Hz (Line noise)
NOTCH_Q: Final = 30.0                  # Quality factor

# Windowing
WINDOW_SIZE_SEC: Final = 2.0           # seconds
WINDOW_STEP_SEC: Final = 2.0           # non-overlapping
WINDOW_SIZE_SAMPLES: Final = int(WINDOW_SIZE_SEC * DEAP_SAMPLE_RATE)
WINDOW_STEP_SAMPLES: Final = int(WINDOW_STEP_SEC * DEAP_SAMPLE_RATE)

# Baseline correction
BASELINE_WINDOW_START: Final = 0.0     # seconds relative to trial start
BASELINE_WINDOW_END: Final = 1.0       # seconds (pre-stimulus)

# ============================================================================
# Model Hyperparameters
# ============================================================================
RANDOM_SEED: Final = 42

# Random Forest
RF_N_ESTIMATORS: Final = 100
RF_MAX_DEPTH: Final = 10
RF_MIN_SAMPLES_SPLIT: Final = 2
RF_MIN_SAMPLES_LEAF: Final = 1
RF_MAX_FEATURES: Final = "sqrt"
RF_CLASS_WEIGHT: Final = "balanced"

# Linear SVM
SVM_C: Final = 1.0
SVM_TOL: Final = 1e-3
SVM_MAX_ITER: Final = 10000

# Cross-Validation
N_JOBS: Final = 4  # Parallelization for LOSO

# ============================================================================
# Validation Hyperparameters
# ============================================================================
PERMUTATION_N_SHUFFLES: Final = 1000
PERMUTATION_RANDOM_STATE: Final = RANDOM_SEED

# Sensitivity Analysis
VALENCE_SENSITIVITY_RANGE: Final = [-0.10, 0.10]  # range around neutral
VALENCE_SENSITIVITY_STEP: Final = 0.05

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL: Final = "INFO"
LOG_FORMAT: Final = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# Helper Functions
# ============================================================================
def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration for logging."""
    return {
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "data_raw": str(DATA_RAW),
            "data_processed": str(DATA_PROCESSED),
            "data_models": str(DATA_MODELS),
        },
        "dataset": {
            "hf_id": DEAP_HF_DATASET_ID,
            "channels": TARGET_CHANNELS,
            "sample_rate": DEAP_SAMPLE_RATE,
        },
        "preprocessing": {
            "filter_band": f"{FILTER_LOW_CUTOFF}-{FILTER_HIGH_CUTOFF} Hz",
            "window_size": f"{WINDOW_SIZE_SEC}s",
            "notch_freq": f"{NOTCH_FREQUENCY} Hz",
        },
        "models": {
            "rf_estimators": RF_N_ESTIMATORS,
            "random_seed": RANDOM_SEED,
        }
    }

# Ensure directories exist (soft check, actual creation handled by T001a/b)
# This is a defensive check to prevent runtime errors if directories are missing
def ensure_directories():
    """Creates necessary directories if they do not exist."""
    for path in [DATA_RAW, DATA_PROCESSED, DATA_MODELS, FIGURES_DIR]:
        path.mkdir(parents=True, exist_ok=True)