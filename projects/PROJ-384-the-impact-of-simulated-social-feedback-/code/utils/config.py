"""
Configuration module for the llmXive research pipeline.
Defines project paths, random seeds, and analysis thresholds.
"""

import os
from pathlib import Path
from typing import Final

# Project Root (assumed to be the parent of 'code/')
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# --- Directory Paths ---
DATA_RAW_DIR: Final[Path] = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = _PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR: Final[Path] = _PROJECT_ROOT / "data" / "results"
DATA_RESULTS_DIAGNOSTICS_DIR: Final[Path] = DATA_RESULTS_DIR / "diagnostics"
LOGS_DIR: Final[Path] = _PROJECT_ROOT / "logs"
CODE_DIR: Final[Path] = _PROJECT_ROOT / "code"
TESTS_DIR: Final[Path] = _PROJECT_ROOT / "tests"

# Specific file paths
LOG_FILE_NAME: Final[str] = "pipeline.log"
LOG_FILE_PATH: Final[Path] = LOGS_DIR / LOG_FILE_NAME
LEXICON_PATH: Final[Path] = DATA_RAW_DIR / "lexicons" / "rosenberg_words.txt"
SCHEMA_PATH: Final[Path] = _PROJECT_ROOT / "contracts" / "interaction_schema.schema.yaml"

# --- Random Seeds ---
# Fixed seed for reproducibility across the pipeline
RANDOM_SEED: Final[int] = 42

# --- Thresholds & Limits ---
# Maximum allowed Variance Inflation Factor (VIF) before halting analysis
VIF_LIMIT: Final[float] = 5.0

# Sentiment Score Range
# Valid scores must fall within [NEGATIVE_THRESHOLD, POSITIVE_THRESHOLD]
NEGATIVE_THRESHOLD: Final[float] = -1.0
POSITIVE_THRESHOLD: Final[float] = 1.0

# Sentinel value for missing or undefined data (used in valence sequences)
SENTINEL_MISSING: Final[float] = -999.0

# Rolling Window Configuration
ROLLING_WINDOW_SIZE: Final[int] = 5
MIN_INTERACTIONS_FOR_METRICS: Final[int] = 2

# --- Device Configuration ---
# Force CPU usage for the sentiment model to ensure compatibility
DEVICE: Final[str] = "cpu"

# Ensure directories exist on import (side effect for setup robustness)
def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        DATA_RESULTS_DIAGNOSTICS_DIR,
        LOGS_DIR,
        DATA_RAW_DIR / "lexicons",
        _PROJECT_ROOT / "contracts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories immediately
ensure_directories()