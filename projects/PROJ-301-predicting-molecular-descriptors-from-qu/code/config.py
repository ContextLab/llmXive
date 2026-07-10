"""
Configuration module for the molecular descriptor prediction pipeline.

This module ensures reproducibility by seeding all random number generators
at the start of execution.
"""
import os
import random
import numpy as np

# Reproducibility Seed
# Setting a fixed seed ensures that random operations (data splits,
# model initialization, etc.) are deterministic across runs.
RANDOM_SEED = 42

def set_seeds(seed: int = RANDOM_SEED) -> None:
    """
    Set the random seed for reproducibility across Python, NumPy, and PyTorch (if available).
    
    Args:
        seed (int): The seed value to use. Defaults to 42.
    """
    # Seed Python's built-in random module
    random.seed(seed)
    
    # Seed NumPy's random number generator
    np.random.seed(seed)
    
    # Optional: Seed PyTorch if installed (common in ML pipelines)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch is not installed; skip seeding
        pass
    
    # Optional: Seed TensorFlow if installed
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        # TensorFlow is not installed; skip seeding
        pass

# Execute seeding immediately upon import to ensure reproducibility
# for any downstream imports that might rely on random state.
set_seeds(RANDOM_SEED)

# Project Paths Configuration
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts")
MODELS_DIR = os.path.join(ARTIFACTS_DIR, "models")
METRICS_DIR = os.path.join(ARTIFACTS_DIR, "metrics")
PLOTS_DIR = os.path.join(ARTIFACTS_DIR, "plots")
CODE_DIR = os.path.join(ROOT_DIR, "code")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")
UTILS_DIR = os.path.join(CODE_DIR, "utils")

# Memory Limit Configuration (GB)
# Matches the limit used in utils/memory_monitor.py
MEMORY_LIMIT_GB = 6.5

# Model Hyperparameters Defaults
DEFAULT_N_ESTIMATORS = 100
DEFAULT_MAX_DEPTH = None
DEFAULT_RANDOM_STATE = RANDOM_SEED

# Feature Extraction Defaults
DEFAULT_MORGAN_RADIUS = 2
DEFAULT_MORGAN_NBITS = 2048

# Training Defaults
DEFAULT_N_FOLDS = 5
DEFAULT_CV_SCORING = "neg_mean_absolute_error"