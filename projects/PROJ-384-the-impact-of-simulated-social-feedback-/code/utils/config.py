"""
Configuration paths, seeds, and thresholds.
"""
import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
LOGS_DIR = PROJECT_ROOT / "logs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Directories
def ensure_directories():
    """Creates necessary directories if they do not exist."""
    dirs = [
        CODE_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_RESULTS_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
        FIGURES_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Random Seed for reproducibility
RANDOM_SEED: Final[int] = 42

# Thresholds
VIF_LIMIT: Final[float] = 5.0
SENTIMENT_RANGE: Final[tuple] = (-1.0, 1.0)

# File Paths
LOG_FILE_NAME: Final[str] = "pipeline.log"
SCHEMA_FILE: Final[Path] = CONTRACTS_DIR / "interaction_schema.schema.yaml"
LEXICON_FILE: Final[Path] = DATA_RAW_DIR / "lexicons" / "rosenberg_words.txt"
