import os
from typing import List, Tuple, Optional
import yaml
from pathlib import Path

# Configuration for the llmXive project: Brain Network Dynamics and Fluid Intelligence
# This module manages dataset selection and sample limits as per the amended spec.

# Primary dataset ID (OpenNeuro) focused on Fluid Intelligence
PRIMARY_DATASET_ID = "ds000224"

# Fallback dataset ID (OpenNeuro) - used only if primary fails or lacks data
FALLBACK_DATASET_ID = "ds000230"

# Sample limit for Continuous Integration (CI) runs
# Per SC-001 and T008b: N=10 baseline
CI_SAMPLE_LIMIT = 10

# Maximum subjects for full analysis (if not in CI mode)
# Per SC-001
MAX_SUBJECTS = 50

def get_dataset_ids() -> Tuple[str, str]:
    """
    Returns the primary and fallback dataset IDs.
    
    Returns:
        Tuple[str, str]: (primary_dataset_id, fallback_dataset_id)
    """
    return (PRIMARY_DATASET_ID, FALLBACK_DATASET_ID)

def get_sample_limit() -> int:
    """
    Returns the sample limit for the current environment.
    If CI environment variable is set, returns CI_SAMPLE_LIMIT (10).
    Otherwise, returns MAX_SUBJECTS (50).
    
    Returns:
        int: The maximum number of subjects to process.
    """
    if os.getenv("CI", "").lower() in ("true", "1", "yes"):
        return CI_SAMPLE_LIMIT
    return MAX_SUBJECTS

def get_config_summary() -> dict:
    """
    Returns a summary of the current configuration.
    
    Returns:
        dict: Configuration summary including dataset IDs and limits.
    """
    return {
        "primary_dataset": PRIMARY_DATASET_ID,
        "fallback_dataset": FALLBACK_DATASET_ID,
        "ci_limit": CI_SAMPLE_LIMIT,
        "max_subjects": MAX_SUBJECTS,
        "current_limit": get_sample_limit()
    }

def validate_config() -> bool:
    """
    Validates that the configuration is sensible.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    if not PRIMARY_DATASET_ID or not FALLBACK_DATASET_ID:
        return False
    if PRIMARY_DATASET_ID == FALLBACK_DATASET_ID:
        return False
    if CI_SAMPLE_LIMIT <= 0 or MAX_SUBJECTS <= 0:
        return False
    if CI_SAMPLE_LIMIT > MAX_SUBJECTS:
        return False
    return True
