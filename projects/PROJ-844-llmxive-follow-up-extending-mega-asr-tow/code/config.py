"""
Configuration module for llmXive project.
Defines paths, seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent

# Data Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
DATA_VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"

# Hyperparameters
RANDOM_SEED = 42
VALIDATION_SAMPLE_SIZE = 500

# ASR Models
ASR_MODEL_NAME = "whisper-tiny"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Thresholds
COLLAPSE_SSS_THRESHOLD = 0.5
COLLAPSE_WER_MULTIPLIER = 2.0

# Distortion Parameters
SNR_RANGE = (0, 30)  # dB
RT60_RANGE = (0.1, 2.0)  # seconds

def get_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary.
    """
    return {
        "paths": {
            "raw": str(DATA_RAW_DIR),
            "derived": str(DATA_DERIVED_DIR),
            "validation": str(DATA_VALIDATION_DIR),
            "project_root": str(PROJECT_ROOT)
        },
        "hyperparameters": {
            "random_seed": RANDOM_SEED,
            "validation_sample_size": VALIDATION_SAMPLE_SIZE,
            "collapse_sss_threshold": COLLAPSE_SSS_THRESHOLD,
            "collapse_wer_multiplier": COLLAPSE_WER_MULTIPLIER
        },
        "models": {
            "asr": ASR_MODEL_NAME,
            "embedding": EMBEDDING_MODEL_NAME
        },
        "distortion": {
            "snr_range": SNR_RANGE,
            "rt60_range": RT60_RANGE
        }
    }
