import os
from pathlib import Path

def get_path_env_override(key: str, default: Path) -> Path:
    """
    Get a path from environment variable or return default.
    """
    val = os.getenv(key)
    if val:
        return Path(val)
    return default

# Project root configuration
PROJECT_ROOT = get_path_env_override("PROJECT_ROOT", Path(__file__).resolve().parent.parent)

# Directory shortcuts
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_LOG_DIR = PROJECT_ROOT / "results" / "logs"
RESULTS_FIGURES_DIR = PROJECT_ROOT / "results" / "figures"

# ----------------------------------------------------------------------
# Core analysis thresholds and constants (Task T001)
# ----------------------------------------------------------------------
# Distance threshold for geospatial matching (km)
DISTANCE_THRESHOLD_KM = 100

# Acceptable ambient temperature range (Celsius)
TEMPERATURE_MIN = -50.0
TEMPERATURE_MAX = 50.0

# Response time bounds (milliseconds)
RESPONSE_TIME_MIN_MS = 100
RESPONSE_TIME_MAX_MS = 10_000

# Random seed for reproducibility of simulation / bootstrap steps
AD_TEST_SEED = 42

# Baseline task identifiers (placeholders for future extensions)
BASELINE_TASK_MORAL_MACHINE = "baseline_moral_machine"
BASELINE_TASK_REACTION_TIME = "baseline_reaction_time"

# Physiological proxy identifiers (placeholders)
PHYSIO_PROXY_HEART_RATE = "physio_heart_rate"
PHYSIO_PROXY_SKIN_CONDUCTANCE = "physio_skin_conductance"

# Additional configuration for external data sources
COVARIATE_INDICATORS = [
    ("SP.DYN.LE00.IN", "Life Expectancy"),
    ("SP.POP.TOTL", "Total Population")
]

# Geocoding settings
GEOCODING_TIMEOUT = 10  # seconds
GEOCODING_USER_AGENT = "llmXive_moral_temp_study"

# ----------------------------------------------------------------------
# Helper: ensure that key directories exist at import time
# ----------------------------------------------------------------------
for _dir in (DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_LOG_DIR, RESULTS_FIGURES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
