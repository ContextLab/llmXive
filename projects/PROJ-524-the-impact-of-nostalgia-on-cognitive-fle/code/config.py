"""
Configuration management for the Nostalgia Cognitive Flexibility project.
Handles environment variables, path resolution, and project constants.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"
DATA_STIMULI_DIR = _PROJECT_ROOT / "data" / "stimuli"
CODE_DIR = _PROJECT_ROOT / "code"
TESTS_DIR = _PROJECT_ROOT / "tests"
SPECS_DIR = _PROJECT_ROOT / "specs"
CONTRACTS_DIR = _PROJECT_ROOT / "contracts"
FIGURES_DIR = _PROJECT_ROOT / "figures"
PAPER_DIR = _PROJECT_ROOT / "paper"

# File Paths
REFS_FILE = DATA_RAW_DIR / "references.json"
EXCLUSION_LOG_FILE = DATA_PROCESSED_DIR / "exclusion_log.json"
VALIDITY_METRICS_FILE = DATA_PROCESSED_DIR / "validity_metrics.json"
CLEANED_DATASET_FILE = DATA_PROCESSED_DIR / "cleaned_dataset.csv"
STATISTICAL_REPORT_FILE = DATA_RESULTS_DIR / "statistical_report.json"
SENSITIVITY_REPORT_FILE = DATA_RESULTS_DIR / "sensitivity_report.json"
STATE_FILE = _PROJECT_ROOT / "state" / "state.yaml"

# Environment Variable Keys
ENV_LOG_LEVEL = "NOSTALGIA_LOG_LEVEL"
ENV_DATA_SOURCE_URL = "NOSTALGIA_DATA_SOURCE_URL"
ENV_STIMULI_CHECKSUM = "NOSTALGIA_STIMULI_CHECKSUM"
ENV_MMSE_THRESHOLD = "NOSTALGIA_MMSE_THRESHOLD"

# Defaults
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_MMSE_THRESHOLD = 24
DEFAULT_DATA_SOURCE_URL = "https://www.openml.org/api/v1/json/data/1594"  # Example placeholder, overridden by env or ingestion logic

# Constants
MIN_AGE = 65
VALID_STIMULUS_TYPES = ["nostalgia", "control"]

# Logger setup
logger = logging.getLogger(__name__)

def get_env_str(key: str, default: Optional[str] = None) -> str:
    """Retrieve a string environment variable or return default."""
    val = os.getenv(key, default)
    if val is None:
        raise ValueError(f"Environment variable {key} is not set and no default provided.")
    return val

def get_env_int(key: str, default: Optional[int] = None) -> int:
    """Retrieve an integer environment variable or return default."""
    val = os.getenv(key)
    if val is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable {key} is not set and no default provided.")
    try:
        return int(val)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be an integer.")

def get_env_float(key: str, default: Optional[float] = None) -> float:
    """Retrieve a float environment variable or return default."""
    val = os.getenv(key)
    if val is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable {key} is not set and no default provided.")
    try:
        return float(val)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be a float.")

def get_env_bool(key: str, default: bool = False) -> bool:
    """Retrieve a boolean environment variable (true/false/1/0)."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes")

def ensure_dirs() -> None:
    """Ensure all required data directories exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        DATA_STIMULI_DIR,
        FIGURES_DIR,
        PAPER_DIR,
        _PROJECT_ROOT / "state"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def get_config() -> Dict[str, Any]:
    """
    Return a dictionary of the current configuration state.
    Useful for logging and reproducibility.
    """
    return {
        "project_root": str(_PROJECT_ROOT),
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "data_results": str(DATA_RESULTS_DIR),
        "data_stimuli": str(DATA_STIMULI_DIR),
        "log_level": os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
        "mmse_threshold": get_env_int(ENV_MMSE_THRESHOLD, DEFAULT_MMSE_THRESHOLD),
        "data_source_url": os.getenv(ENV_DATA_SOURCE_URL, DEFAULT_DATA_SOURCE_URL),
        "stimuli_checksum": os.getenv(ENV_STIMULI_CHECKSUM),
        "min_age": MIN_AGE,
        "valid_stimulus_types": VALID_STIMULUS_TYPES
    }

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.
    Initializes directories and returns the config dict.
    """
    ensure_dirs()
    return get_config()

# Convenience accessors
def get_mmse_threshold() -> int:
    return get_env_int(ENV_MMSE_THRESHOLD, DEFAULT_MMSE_THRESHOLD)

def get_data_source_url() -> str:
    return get_env_str(ENV_DATA_SOURCE_URL, DEFAULT_DATA_SOURCE_URL)

def get_log_level() -> str:
    return os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL)