"""
Environment configuration module for LlmXive pipeline.

This module enforces CPU-only execution by setting CUDA_VISIBLE_DEVICES
to an empty string at import time, preventing any accidental GPU usage.
"""
import os
import sys
import logging
from pathlib import Path

# Enforce CPU-only execution immediately upon import
# This prevents any accidental GPU allocation by PyTorch or other libraries
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Configure module-level logger
logger = logging.getLogger(__name__)

def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by ensuring CUDA_VISIBLE_DEVICES is empty.
    
    This function checks the current environment and forces the variable
    to be empty if it's not already set or is set to a non-empty value.
    
    Raises:
        RuntimeError: If the environment cannot be configured for CPU-only mode.
    """
    cuda_var = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_var != "":
        logger.warning(
            f"CUDA_VISIBLE_DEVICES was set to '{cuda_var}'. "
            "Overriding to enforce CPU-only execution."
        )
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Verify the enforcement
    if os.environ.get("CUDA_VISIBLE_DEVICES", "") != "":
        raise RuntimeError(
            "Failed to enforce CPU-only execution. "
            "CUDA_VISIBLE_DEVICES is not empty."
        )
    
    logger.info("CPU-only execution enforced successfully.")

def is_cpu_only_mode() -> bool:
    """
    Check if the environment is configured for CPU-only execution.
    
    Returns:
        bool: True if CUDA_VISIBLE_DEVICES is empty, False otherwise.
    """
    return os.environ.get("CUDA_VISIBLE_DEVICES", "") == ""

def log_environment_config() -> dict:
    """
    Log and return the current environment configuration.
    
    Returns:
        dict: A dictionary containing relevant environment variables.
    """
    config = {
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "cpu_only_mode": is_cpu_only_mode(),
    }
    
    logger.info(f"Environment configuration: {config}")
    return config

# Execute enforcement immediately when module is imported
enforce_cpu_only()
