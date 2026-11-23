"""
Configuration management for the llmXive research pipeline.

Handles environment variables, path management, and project constants.
"""
import os
from pathlib import Path
from typing import Optional

# Project root is two levels up from this file (code/utils/config.py -> code/utils -> code -> root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
BEHAVIORAL_DATA_DIR = DATA_DIR / "behavioral"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Configuration file paths
CONFIG_DIR = PROJECT_ROOT / "config"
STATE_DIR = PROJECT_ROOT / "state"
DOCS_DIR = PROJECT_ROOT / "docs"

# Environment variables with defaults
OPENNEURO_API_KEY = os.getenv("OPENNEURO_API_KEY", "")
FMRIPREP_CONTAINER = os.getenv("FMRIPREP_CONTAINER", "poldracklab/fmriprep:23.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Motion threshold for QC (mm) - per Spec Constraints
MOTION_THRESHOLD = 0.5

# Database settings (Legacy/Placeholder - YAML state is primary per Constitution Principle III)
# Note: DB_PATH is kept for backward compatibility with existing API surface, 
# but primary state tracking is YAML-based.
DB_PATH = DATA_DIR / "registry.db"

# Retry settings
MAX_RETRIES = 3
TIMEOUT = 30

# Analysis constants
PARCELLATION_SCHAEFER = "schaefer_200"
CORRELATION_METHOD = "pearson"

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def get_data_dir() -> Path:
    """Return the main data directory."""
    return DATA_DIR

def get_raw_data_dir() -> Path:
    """Return the raw data directory."""
    return RAW_DATA_DIR

def get_processed_data_dir() -> Path:
    """Return the processed data directory."""
    return PROCESSED_DATA_DIR

def get_behavioral_data_dir() -> Path:
    """Return the behavioral data directory."""
    return BEHAVIORAL_DATA_DIR

def get_figures_dir() -> Path:
    """Return the figures directory."""
    return FIGURES_DIR

def get_state_dir() -> Path:
    """Return the state directory for YAML tracking."""
    return STATE_DIR

def get_docs_dir() -> Path:
    """Return the documentation directory."""
    return DOCS_DIR

def ensure_directories() -> None:
    """Create all necessary directories if they don't exist."""
    directories = [
        DATA_DIR, 
        RAW_DATA_DIR, 
        PROCESSED_DATA_DIR, 
        BEHAVIORAL_DATA_DIR, 
        FIGURES_DIR, 
        CONFIG_DIR,
        STATE_DIR,
        DOCS_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_value(key: str, default: Optional[str] = None) -> str:
    """
    Get a configuration value from environment variables or defaults.
    
    Args:
        key: The configuration key to retrieve.
        default: Default value if key is not found.
        
    Returns:
        The configuration value as a string.
    """
    config_map = {
        "OPENNEURO_API_KEY": OPENNEURO_API_KEY,
        "FMRIPREP_CONTAINER": FMRIPREP_CONTAINER,
        "LOG_LEVEL": LOG_LEVEL,
        "MOTION_THRESHOLD": str(MOTION_THRESHOLD),
        "PARCELLATION": PARCELLATION_SCHAEFER,
        "CORRELATION_METHOD": CORRELATION_METHOD,
    }
    return config_map.get(key, default or "")

def get_db_path() -> Path:
    """Return the path to the legacy SQLite database (if used)."""
    return DB_PATH