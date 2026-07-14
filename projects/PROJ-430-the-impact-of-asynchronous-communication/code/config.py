"""
Configuration module for the llmXive asynchronous communication impact study.

This module centralizes all project paths, API keys, and deferred thresholds.
It adheres to the Constitution Principle of Configuration (separation of logic from values).
"""
import os
from pathlib import Path
from typing import Optional

# --- Project Root & Directory Structure ---
# Determine project root based on the assumption that this file is at code/config.py
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Data Subdirectories (created by T006, but defined here for path consistency)
RAW_DATA_DIR = DATA_DIR / "raw"
DERIVED_DATA_DIR = DATA_DIR / "derived"
VALIDATION_DATA_DIR = DATA_DIR / "validation"
FIGURES_DIR = PROJECT_ROOT / "figures"

# --- API Keys & External Services ---
# These are loaded from environment variables. If not set, they default to None.
# The pipeline will fail early if a required key is missing during execution.
GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
# Placeholder for future API keys (e.g., if using external sentiment APIs)
# OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

# --- Deferred Thresholds & Hyperparameters ---
# These values control the "deferred" logic for data processing and filtering.
# They are designed to be tuned or overridden via environment variables or a config file.

# Minimum number of events required to consider a project valid for analysis.
# Projects with fewer events are filtered out to avoid statistical noise.
MIN_EVENTS: int = int(os.getenv("MIN_EVENTS", "50"))

# Sample size for specific operations (e.g., manual annotation sampling).
# If None, all available data is used.
SAMPLE_SIZE: Optional[int] = (
    int(os.getenv("SAMPLE_SIZE", "1000"))
    if os.getenv("SAMPLE_SIZE") else None
)

# Threshold for language detection confidence (0.0 to 1.0).
# Text below this confidence is excluded from sentiment analysis.
LANGUAGE_CONFIDENCE_THRESHOLD: float = float(os.getenv("LANGUAGE_CONFIDENCE_THRESHOLD", "0.95"))

# Maximum number of events to process in a single chunk to prevent OOM.
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "100000"))

# Rate limit handling: seconds to wait before retrying a failed API request.
RATE_LIMIT_RETRY_DELAY: int = int(os.getenv("RATE_LIMIT_RETRY_DELAY", "60"))

# VIF (Variance Inflation Factor) threshold for halting regression analysis.
# If any feature has a VIF > this value, the analysis is halted to prevent multicollinearity issues.
VIF_THRESHOLD: float = float(os.getenv("VIF_THRESHOLD", "5.0"))

# Spearman correlation threshold for validation (US2).
# The VADER scores must correlate with manual ground truth at least this strongly.
SPEARMAN_VALIDATION_THRESHOLD: float = float(os.getenv("SPEARMAN_VALIDATION_THRESHOLD", "0.5"))

# --- Helper Functions ---
def ensure_directories_exist() -> None:
    """
    Creates all required data directories if they do not already exist.
    This is a safety check to ensure the pipeline can write output files.
    """
    directories = [
        RAW_DATA_DIR,
        DERIVED_DATA_DIR,
        VALIDATION_DATA_DIR,
        FIGURES_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> dict:
    """
    Returns a summary of the current configuration for logging/debugging.
    Does not expose actual API keys.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "min_events": MIN_EVENTS,
        "sample_size": SAMPLE_SIZE,
        "language_confidence_threshold": LANGUAGE_CONFIDENCE_THRESHOLD,
        "chunk_size": CHUNK_SIZE,
        "rate_limit_retry_delay": RATE_LIMIT_RETRY_DELAY,
        "vif_threshold": VIF_THRESHOLD,
        "spearman_validation_threshold": SPEARMAN_VALIDATION_THRESHOLD,
        "github_token_set": GITHUB_TOKEN is not None,
    }

# Execute directory creation on import if needed (optional, can be called explicitly)
# ensure_directories_exist()