"""
Configuration settings for the llmXive project.

This file is referenced by T003 and used by T006 (download.py) and others.
It defines paths, seeds, and dataset identifiers.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CODE_DIR = BASE_DIR / "code"
SPECS_DIR = BASE_DIR / "specs"

# Dataset Configuration
# These values must be updated with the REAL Hugging Face repo ID once confirmed
# For now, using a placeholder that will trigger a clear error if the repo doesn't exist
# The task T006 is designed to fail loudly if this repo is invalid.
DATASET_REPO = "llmXive/S-Agent-300K" 
DATASET_SUBSET = "spatial_reasoning"

# Expected SHA256 of the main data file (if known). 
# If None, checksum verification is skipped.
# In a real run, this should be populated from the dataset card or manifest.
DATASET_SHA256 = None 

# Paths
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_DERIVED_DIR = DATA_DIR / "derived"
DATA_RESULTS_DIR = DATA_DIR / "results"
STATE_FILE = BASE_DIR / "state" / "projects" / "PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml"

# Random Seeds
RANDOM_SEED = 42

# Sample Size
SAMPLE_SIZE = 1000

# Create a simple namespace-like object for access
class Config:
    def __init__(self):
        self.dataset_repo = DATASET_REPO
        self.dataset_subset = DATASET_SUBSET
        self.dataset_sha256 = DATASET_SHA256
        self.data_raw_dir = str(DATA_RAW_DIR)
        self.data_derived_dir = str(DATA_DERIVED_DIR)
        self.data_results_dir = str(DATA_RESULTS_DIR)
        self.state_file = str(STATE_FILE)
        self.random_seed = RANDOM_SEED
        self.sample_size = SAMPLE_SIZE
        self.base_dir = str(BASE_DIR)
        self.code_dir = str(CODE_DIR)
        self.specs_dir = str(SPECS_DIR)

    def get(self, key, default=None):
        return getattr(self, key, default)

CONFIG = Config()
