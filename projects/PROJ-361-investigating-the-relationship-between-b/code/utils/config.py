import os
from pathlib import Path
from typing import Optional

# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
BEHAVIORAL_DATA_DIR = DATA_DIR / "behavioral"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Configuration file paths
CONFIG_DIR = PROJECT_ROOT / "config"
DB_PATH = DATA_DIR / "registry.db"

# Environment variables with defaults
OPENNEURO_API_KEY = os.getenv("OPENNEURO_API_KEY", "")
FMRIPREP_CONTAINER = os.getenv("FMRIPREP_CONTAINER", "poldracklab/fmriprep:23.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Motion threshold for QC (mm)
MOTION_THRESHOLD = 0.5

# Database settings
MAX_RETRIES = 3
TIMEOUT = 30

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the data directory."""
    return DATA_DIR

def ensure_directories() -> None:
    """Create all necessary directories if they don't exist."""
    for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, BEHAVIORAL_DATA_DIR, FIGURES_DIR, CONFIG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_value(key: str, default: Optional[str] = None) -> str:
    """Get a configuration value from environment variables or defaults."""
    config_map = {
        "OPENNEURO_API_KEY": OPENNEURO_API_KEY,
        "FMRIPREP_CONTAINER": FMRIPREP_CONTAINER,
        "LOG_LEVEL": LOG_LEVEL,
        "MOTION_THRESHOLD": str(MOTION_THRESHOLD),
    }
    return config_map.get(key, default or "")