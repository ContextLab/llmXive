import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Random Seed for Reproducibility
RANDOM_SEED = 42

# Directory Structure
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"

def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_DIR, DATA_RAW, DATA_PROCESSED,
        FIGURES_DIR, TESTS_DIR, DOCS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
