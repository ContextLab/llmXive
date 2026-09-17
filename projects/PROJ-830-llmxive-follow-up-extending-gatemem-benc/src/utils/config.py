"""
Configuration module for the GateMem benchmark project.
"""
import os

# Dataset Configuration
# Reads from environment variable DATASET_ID or defaults to None to trigger failure
DATASET_ID = os.environ.get("DATASET_ID")

# Paths
DATA_RAW_DIR = "data/raw"
STATE_DIR = "state"
ARTIFACT_HASHES_FILE = os.path.join(STATE_DIR, "artifact_hashes.yaml")

# Required fields for validation
REQUIRED_FIELDS = [
    "outcome",
    "predictors",
    "covariates",
    "leak-target",
    "roles",
    "domains"
]
