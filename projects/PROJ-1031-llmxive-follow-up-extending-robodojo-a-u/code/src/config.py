"""
src/config.py
----------------
Central configuration used by the RoboDojo symbolic‑extension pipeline.

This module defines constants required by many downstream modules, including
the dataset identifier used by the data loader, base directory helpers, and
some generic pipeline parameters.  All values are real – the dataset identifier
points to the publicly‑available RoboDojo dataset on HuggingFace.
"""

import os
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Dataset identifier – the public RoboDojo dataset on HuggingFace.
# ----------------------------------------------------------------------
# The dataset is hosted at https://huggingface.co/datasets/RoboDojo/robodojo
# and contains both the simulated and real‑world task splits.
DATASET_HF_ID: str = "RoboDojo/robodojo"
# Optional commit hash – “latest” resolves to the most recent version.
DATASET_COMMIT_HASH: str = "latest"

# ----------------------------------------------------------------------
# Directory helpers – these mirror the helpers defined in the top‑level
# `code/config.py` but are kept here for modules that import directly from
# `src.config`.
# ----------------------------------------------------------------------
RAW_DATA_DIR = paths.data("raw")
INTERIM_DATA_DIR = paths.data("interim")
PROCESSED_DATA_DIR = paths.data("processed")
FINAL_DATA_DIR = paths.data("final")

# Ensure the directories exist when this module is imported.
for _dir in (RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, FINAL_DATA_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Pipeline‑wide constants used by various components.
# ----------------------------------------------------------------------
# Base directory of the project (repository root).
BASE_DIR = paths.root

# Planning timeout (seconds) – matches the value expected by `src.main`.
PLANNING_TIMEOUT_S: int = 60

# Paths used by the Oracle executor and other modules.
DATA_INTERIM_PATH = str(INTERIM_DATA_DIR)

# Tolerances for real‑world execution (used by `src.executor`).
POSE_DEV_TOLERANCE_CM: float = 5.0
ORIENT_DEV_TOLERANCE_DEG: float = 15.0

# The real‑world split name used by the data loader.
REAL_WORLD_SPLIT: str = "real"
