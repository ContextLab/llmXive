"""
Configuration constants for the GateMem benchmark data loader.
"""
import os
from pathlib import Path

# Identifier of the HuggingFace dataset
DATASET_ID = os.getenv("GATEMEM_DATASET_ID", "Ray368/GateMem")

# Directories for raw data and state artifacts
DATA_RAW_DIR = os.getenv("GATEMEM_DATA_RAW_DIR", "data/raw")
STATE_DIR = os.getenv("GATEMEM_STATE_DIR", "state")

# Path to the artifact hashes file (managed by the platform; kept here for compatibility)
ARTIFACT_HASHES_FILE = os.path.join(STATE_DIR, "artifact_hashes.yaml")

# Fields that must be present in each episode
REQUIRED_FIELDS = [
    "id",
    "domain",
    "leak-target",
    "role",
    "outcome",
    "authorization_boundaries"
]