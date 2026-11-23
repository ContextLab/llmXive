import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
METRICS_DIR = DATA_DIR / "metrics"
TRIAL_LEVEL_DIR = DATA_DIR / "trial_level"
LOGS_DIR = PROJECT_ROOT / "logs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Hyperparameters
BANDPASS_LOW = 1.0
BANDPASS_HIGH = 45.0
EPOCH_TMIN = -1.0
EPOCH_TMAX = 2.0
PRE_STIM_TMIN = -0.5
PRE_STIM_TMAX = 0.0
THETA_BAND = (4, 7)
GAMMA_BAND = (30, 45)
MEMORY_LIMIT_GB = 6.5
TIMEOUT_HOURS = 6

def ensure_directories():
    """Create all necessary directories if they don't exist."""
    dirs = [DATA_DIR, RAW_DIR, PROCESSED_DIR, METRICS_DIR, TRIAL_LEVEL_DIR, LOGS_DIR, CONTRACTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    # Ensure subdirectories for processed data
    (PROCESSED_DIR / "band_filtered").mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "epochs").mkdir(parents=True, exist_ok=True)

def main():
    ensure_directories()
    print("Directories ensured.")

if __name__ == "__main__":
    main()