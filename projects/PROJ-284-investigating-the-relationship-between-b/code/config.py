"""
Configuration management for the llmXive brain-proprioception-correlation pipeline.

This module centralizes all environment variables and constants required for
data acquisition, processing, and analysis. It ensures consistent configuration
across the pipeline and provides safe access to sensitive credentials.
"""

import os
from typing import Dict, Any, Optional

# --- Constants ---
# Memory limit set to 7GB as per project requirements
MEMORY_LIMIT_GB: float = 7.0
MEMORY_LIMIT_BYTES: int = int(MEMORY_LIMIT_GB * 1024**3)

# Batch size default (can be overridden by environment)
BATCH_SIZE: int = 10

# HCP API Configuration
HCP_API_VERSION: str = "1.0"
HCP_BASE_URL: str = "https://db.humanconnectome.org/api"

# Schaefer Atlas Configuration
# URL for the 400-node, 7-network Schaefer atlas (1mm MNI152)
SCHAEFER_ATLAS_URL: str = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/"
    "stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/"
    "MNI/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_1mm.nii.gz"
)

# --- Credential Management ---
# Sensitive credentials should be set via environment variables
# Do not hardcode credentials in this file or commit them to version control

def get_hcp_credentials() -> Dict[str, str]:
    """
    Retrieve HCP API credentials from environment variables.

    Returns:
        Dict containing 'username' and 'password' if both are set.

    Raises:
        ValueError: If HCP credentials are not configured in the environment.
    """
    username = os.getenv("HCP_USERNAME")
    password = os.getenv("HCP_PASSWORD")

    if not username or not password:
        raise ValueError(
            "HCP credentials not found. Please set HCP_USERNAME and HCP_PASSWORD "
            "environment variables."
        )

    return {
        "username": username,
        "password": password,
    }

def get_config() -> Dict[str, Any]:
    """
    Retrieve the full configuration dictionary.

    Returns:
        Dict containing all configuration keys with their current values.
    """
    return {
        "MEMORY_LIMIT_GB": MEMORY_LIMIT_GB,
        "MEMORY_LIMIT_BYTES": MEMORY_LIMIT_BYTES,
        "BATCH_SIZE": BATCH_SIZE,
        "HCP_API_VERSION": HCP_API_VERSION,
        "HCP_BASE_URL": HCP_BASE_URL,
        "SCHAEFER_ATLAS_URL": SCHAEFER_ATLAS_URL,
        "HCP_CREDENTIALS": get_hcp_credentials(),
    }

# --- Validation ---
def validate_config() -> bool:
    """
    Validate that all required configuration is present and valid.

    Returns:
        True if configuration is valid, False otherwise.
    """
    try:
        config = get_config()
        # Basic validation checks
        assert config["MEMORY_LIMIT_GB"] > 0, "Memory limit must be positive"
        assert config["BATCH_SIZE"] > 0, "Batch size must be positive"
        assert config["HCP_API_VERSION"], "HCP API version cannot be empty"
        assert config["SCHAEFER_ATLAS_URL"], "Schaefer atlas URL cannot be empty"
        return True
    except (ValueError, AssertionError) as e:
        print(f"Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    # Simple validation script
    if validate_config():
        print("Configuration validated successfully.")
        config = get_config()
        print(f"Memory Limit: {config['MEMORY_LIMIT_GB']} GB")
        print(f"Batch Size: {config['BATCH_SIZE']}")
        print(f"HCP API Version: {config['HCP_API_VERSION']}")
    else:
        print("Configuration validation failed.")
        exit(1)
