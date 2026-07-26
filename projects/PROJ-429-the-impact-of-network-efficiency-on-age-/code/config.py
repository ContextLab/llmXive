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
CONFIG_DIR = PROJECT_ROOT / 'data' / 'config'

# Configuration parameters
# Design decision: 10-second epochs for better spectral resolution (T014)
EPOCH_LENGTH_SEC = 10
BANDPASS_MIN_FREQ = 1.0  # Hz
BANDPASS_MAX_FREQ = 40.0  # Hz
SNR_THRESHOLD_DB = 10.0
ARTIFACT_REJECTION_THRESHOLD = 0.5  # 50% artifact tolerance

# Sensitivity Analysis Thresholds (FR-008)
NETWORK_DENSITY_THRESHOLDS = [0.1, 0.3, 0.5]  # Low, Medium, High

# Cognitive Instrument Registry Path
COGNITIVE_INSTRUMENT_REGISTRY_PATH = CONFIG_DIR / 'cognitive_instrument_registry.yaml'

def ensure_dirs():
    """Create all required directories if they don't exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        QUALITY_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        STATE_DIR,
        CONFIG_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def get_config_summary():
    """Return a dictionary of current configuration values."""
    return {
        'epoch_length_sec': EPOCH_LENGTH_SEC,
        'bandpass_min_freq': BANDPASS_MIN_FREQ,
        'bandpass_max_freq': BANDPASS_MAX_FREQ,
        'snr_threshold_db': SNR_THRESHOLD_DB,
        'artifact_rejection_threshold': ARTIFACT_REJECTION_THRESHOLD,
        'network_density_thresholds': NETWORK_DENSITY_THRESHOLDS,
        'cognitive_instrument_registry': str(COGNITIVE_INSTRUMENT_REGISTRY_PATH)
    }
