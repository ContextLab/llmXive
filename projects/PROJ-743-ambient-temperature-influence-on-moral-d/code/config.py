import os
from pathlib import Path

# Directories
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
DATA_EXTERNAL_DIR = Path("data/external")
RESULTS_DIR = Path("results")
RESULTS_LOG_DIR = Path("results/logs")
RESULTS_STATS_DIR = Path("results/stats")
RESULTS_FIGS_DIR = Path("results/figures")

# Thresholds & Constants
DISTANCE_THRESHOLD_KM = 100
TEMPERATURE_MIN = -50.0
TEMPERATURE_MAX = 60.0
RESPONSE_TIME_MIN_MS = 100
RESPONSE_TIME_MAX_MS = 10000
AD_TEST_SEED = 42

# Baseline Task / Physio Proxy (for later tasks)
BASELINE_TASK_URL = "https://example.com/baseline_rt.csv"
PHYSIO_PROXY_URL = "https://example.com/physio_proxy.csv"

def get_path_env_override(key: str, default: Path) -> Path:
    """Get a path from environment variable or default."""
    return Path(os.getenv(key, str(default)))
