"""
Configuration management for the EEG network efficiency project.

Defines paths and configuration parameters used throughout the pipeline.
"""
from pathlib import Path

# Project root is assumed to be the parent of this file's directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
PROCESSED_DATA_DIR = PROJECT_ROOT / 'data' / 'processed'
QUALITY_DIR = PROJECT_ROOT / 'data' / 'quality'
RESULTS_DIR = PROJECT_ROOT / 'data' / 'results'
FIGURES_DIR = PROJECT_ROOT / 'data' / 'figures'
STATE_DIR = PROJECT_ROOT / 'state'

# Configuration parameters
# Design decision: 10-second epochs for better spectral resolution
EPOCH_LENGTH_SEC = 10
BANDPASS_MIN_FREQ = 1.0  # Hz
BANDPASS_MAX_FREQ = 40.0  # Hz
SNR_THRESHOLD_DB = 10.0
ARTIFACT_REJECTION_THRESHOLD = 0.5  # 50% artifact tolerance

def ensure_dirs():
    """Create all required directories if they don't exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        QUALITY_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        STATE_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs