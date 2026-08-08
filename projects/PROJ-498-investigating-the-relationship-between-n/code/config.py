import os
from pathlib import Path

def ensure_directories():
    """
    Create all necessary directories for the project.
    """
    dirs = [
        "data/raw",
        "data/processed",
        "data/metrics",
        "data/trial_level",
        "logs",
        "contracts"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# Configuration constants
BANDPASS_LOW = 1.0
BANDPASS_HIGH = 45.0
EPOCH_TMIN = -1.0  # -1000ms
EPOCH_TMAX = 2.0   # +2000ms
PRE_STIM = 0.0
NOTCH_FREQS = [50, 60]
ICA_KURTOSIS_THRESHOLD = 5.0
ICA_SPECTRAL_PEAK_THRESHOLD = 30.0
MIN_TRIALS_PER_CONDITION = 10
MAX_ARTIFACT_REMOVAL_RATIO = 0.5
MEMORY_LIMIT_GB = 6.5
TIMEOUT_HOURS = 4
