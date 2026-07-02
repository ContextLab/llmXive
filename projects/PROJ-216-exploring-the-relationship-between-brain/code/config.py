"""
Environment configuration management for the llmXive science pipeline.

This module centralizes configuration for dataset IDs, sample limits,
and environment-specific overrides (CI vs Production).

Overrides Spec SC-001 (N=50) with Plan constraint (N=10) for CI environments.
"""
import os
from typing import List, Tuple

# Default Configuration
DEFAULT_DATASET_IDS: List[str] = ["ds000224", "ds000230"]
DEFAULT_SAMPLE_LIMIT: int = 50  # Spec SC-001 target

# CI Overrides (Plan constraint)
CI_SAMPLE_LIMIT: int = 10
CI_ENV_VAR: str = "CI"

# Environment Variables for Configuration
ENV_DATASET_IDS: str = "LMMXIVE_DATASET_IDS"
ENV_SAMPLE_LIMIT: str = "LMMXIVE_SAMPLE_LIMIT"


def get_dataset_ids() -> List[str]:
    """
    Retrieve the list of OpenNeuro dataset IDs to process.

    Priority:
    1. Environment variable `LMMXIVE_DATASET_IDS` (comma-separated)
    2. Default list: ["ds000224", "ds000230"]

    Returns:
        List[str]: Dataset IDs (e.g., ["ds000224", "ds000230"])
    """
    env_value = os.getenv(ENV_DATASET_IDS)
    if env_value:
        return [ds.strip() for ds in env_value.split(",") if ds.strip()]
    return DEFAULT_DATASET_IDS


def get_sample_limit() -> int:
    """
    Retrieve the maximum number of subjects to process.

    Logic:
    - If running in a CI environment (CI=true env var), return 10 (Plan override).
    - Otherwise, check for explicit env var override.
    - Fall back to Spec default (50).

    Returns:
        int: Maximum sample size (N).
    """
    # Check for CI environment override first (Plan constraint)
    if os.getenv(CI_ENV_VAR, "").lower() in ("1", "true", "yes"):
        return CI_SAMPLE_LIMIT

    # Check for explicit environment variable override
    env_value = os.getenv(ENV_SAMPLE_LIMIT)
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            # Log warning or ignore, fallback to default
            pass

    return DEFAULT_SAMPLE_LIMIT


def get_config_summary() -> Tuple[List[str], int]:
    """
    Returns a summary of the current configuration state.

    Returns:
        Tuple[List[str], int]: (dataset_ids, sample_limit)
    """
    return get_dataset_ids(), get_sample_limit()
