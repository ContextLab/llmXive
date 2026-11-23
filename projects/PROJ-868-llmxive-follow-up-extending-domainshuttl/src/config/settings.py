"""
Configuration settings for the llmXive pipeline.
"""
import os
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default Paths
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DEFAULT_MODELS_DIR = PROJECT_ROOT / "data" / "models"

# Model Checkpoints
MODEL_CHECKPOINT_PATH = DEFAULT_RAW_DATA_DIR / "domainshuttle.pth"

# Hyperparameters
SEED = 42
DEVICE = "cpu"

# Fidelity Threshold (Deferred as per T004b)
FIDELITY_THRESHOLD: Optional[float] = None

def get_config() -> dict:
    """
    Returns the configuration dictionary.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "raw_data_dir": str(DEFAULT_RAW_DATA_DIR),
        "processed_data_dir": str(DEFAULT_PROCESSED_DATA_DIR),
        "results_dir": str(DEFAULT_RESULTS_DIR),
        "models_dir": str(DEFAULT_MODELS_DIR),
        "model_checkpoint_path": str(MODEL_CHECKPOINT_PATH),
        "seed": SEED,
        "device": DEVICE,
        "fidelity_threshold": FIDELITY_THRESHOLD
    }
