"""
Shared configuration for the Gut Microbiome and Cognitive Flexibility study.
Defines fixed random seeds, paths, and environment constants.
"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Ensure data directories exist (best practice for config)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Fixed Random Seed for Reproducibility
# Per Plan Amendment Task 0.1, we need deterministic synthetic generation
SEED = 42

# Analysis Constants
COGNITIVE_SCORE_COL = "cognitive_score"
AGE_COL = "age"
MIN_AGE_THRESHOLD = 65

# Logging
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
