"""
Central configuration for path handling and logger creation.
"""

import logging
from pathlib import Path

# Base directories – these are relative to the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Raw data directory (e.g., data/raw/)
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"

# Processed data directory (e.g., data/processed/)
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

# Manifest file location
DATA_MANIFEST_PATH = PROJECT_ROOT / "data_manifest.json"

def get_logger(name: str) -> logging.Logger:
    """Create (or retrieve) a module‑level logger with a sensible format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger