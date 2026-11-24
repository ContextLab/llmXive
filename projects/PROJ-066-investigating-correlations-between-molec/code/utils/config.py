"""
Configuration constants for the molecular descriptor pipeline.

This module defines global constants used throughout the research pipeline.
CRITICAL: The RANDOM_SEED defined here MUST be passed to the stratified splitter
in T017 (code/models/train.py) to ensure reproducibility of the train/test split.
"""
import os
from pathlib import Path

# Random seed for reproducibility
# IMPORTANT: This seed must be used in T017 for the stratified splitter
# (e.g. train_test_split(..., random_state=RANDOM_SEED) in
# code/models/train.py) to ensure that the train/test split is
# reproducible across runs.
RANDOM_SEED = 42

# Resource constraints
# Maximum allowed memory usage in Gigabytes
MAX_MEMORY_GB = 7
# Maximum allowed duration for pipeline execution in hours
MAX_DURATION_HOURS = 6
# Maximum number of molecules retained after stratified sampling (T013)
MAX_MOLECULES = 15000

# Project paths
# Determine project root relative to this file (utils/config.py)
# Structure: code/utils/config.py -> code/ -> project_root/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Ensure project-owned data directories exist.
# This is a safety measure; directories should ideally be created by T008
# but ensuring existence here prevents runtime errors in downstream tasks.
# NOTE: the platform owns the top-level state/ directory, so no state
# paths are created or written here.
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)