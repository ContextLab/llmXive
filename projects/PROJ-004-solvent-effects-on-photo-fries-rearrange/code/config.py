"""
Configuration and path management for the project.

This module enforces CPU-only execution constraints and defines file paths
for data directories.
"""

import os
import sys
from pathlib import Path

# Enforce CPU-only execution constraints
# Disable GPU usage for all major libraries to ensure reproducible CPU execution
# in CI environments without GPU support.

# Set environment variables BEFORE importing torch or tensorflow
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

# Attempt to disable GPU in torch if available
try:
    import torch
    torch.set_num_threads(1)
    if torch.cuda.is_available():
        # Force CPU usage even if CUDA is detected
        torch.set_default_device("cpu")
        # Log warning about GPU being disabled
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("GPU detected but forced to CPU-only mode via config.py")
except ImportError:
    pass
except Exception:
    # Silently ignore any torch configuration errors
    pass

# Attempt to disable GPU in tensorflow if available
try:
    import tensorflow as tf
    tf.config.set_visible_devices([], 'GPU')
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("TensorFlow GPU devices disabled via config.py")
except ImportError:
    pass
except Exception:
    # Silently ignore any tensorflow configuration errors
    pass

# Project root is the parent of the code directory
_PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
_RAW_DATA_DIR = _PROJECT_ROOT / "data" / "raw"
_COMPUTE_DATA_DIR = _PROJECT_ROOT / "data" / "compute"
_PROCESSED_DATA_DIR = _PROJECT_ROOT / "data" / "processed"
_CHEMICALS_DIR = _PROJECT_ROOT / "data" / "chemicals"
_FIGURES_DIR = _PROJECT_ROOT / "figures"
_PAPER_DIR = _PROJECT_ROOT / "paper"

def get_raw_data_path() -> Path:
    """Get the path to the raw data directory."""
    return _RAW_DATA_DIR

def get_compute_data_path() -> Path:
    """Get the path to the compute data directory."""
    return _COMPUTE_DATA_DIR

def get_processed_data_path() -> Path:
    """Get the path to the processed data directory."""
    return _PROCESSED_DATA_DIR

def get_chemicals_path() -> Path:
    """Get the path to the chemicals directory."""
    return _CHEMICALS_DIR

def get_figures_path() -> Path:
    """Get the path to the figures directory."""
    return _FIGURES_DIR

def get_paper_path() -> Path:
    """Get the path to the paper directory."""
    return _PAPER_DIR

def ensure_directories() -> None:
    """Create all necessary data directories if they don't exist."""
    for path in [
        _RAW_DATA_DIR,
        _COMPUTE_DATA_DIR,
        _PROCESSED_DATA_DIR,
        _CHEMICALS_DIR,
        _FIGURES_DIR,
        _PAPER_DIR
    ]:
        path.mkdir(parents=True, exist_ok=True)