"""
Environment configuration utilities for LlmXive project.

This module enforces CPU-only execution by setting the CUDA_VISIBLE_DEVICES
environment variable to an empty string at module import time.
"""
import os
import sys
import logging
from pathlib import Path

# CRITICAL: Enforce CPU-only execution immediately upon import
# This must happen before any CUDA-related libraries (torch, etc.) are imported
if "CUDA_VISIBLE_DEVICES" not in os.environ or os.environ["CUDA_VISIBLE_DEVICES"] != "":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    logging.getLogger(__name__).info("Enforced CPU-only execution: CUDA_VISIBLE_DEVICES set to ''")

def enforce_cpu_only() -> None:
    """
    Explicitly enforce CPU-only execution by setting CUDA_VISIBLE_DEVICES to empty.
    
    This function can be called explicitly to ensure CPU-only mode, though the
    environment variable is already set at module import time.
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    logging.getLogger(__name__).info("Enforced CPU-only execution: CUDA_VISIBLE_DEVICES set to ''")

def is_cpu_only_mode() -> bool:
    """
    Check if the environment is configured for CPU-only execution.
    
    Returns:
        bool: True if CUDA_VISIBLE_DEVICES is empty or not set, False otherwise.
    """
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    return cuda_devices == ""

def log_environment_config(logger: Optional[logging.Logger] = None) -> None:
    """
    Log the current environment configuration for debugging and verification.
    
    Args:
        logger: Optional logger instance. If None, uses the module's logger.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("Environment Configuration:")
    logger.info(f"  CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'NOT SET')}")
    logger.info(f"  CPU-only mode: {is_cpu_only_mode()}")
    
    # Log additional relevant environment variables
    relevant_vars = [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]
    for var in relevant_vars:
        if var in os.environ:
            logger.info(f"  {var}: {os.environ[var]}")

# Auto-log environment config when module is imported in debug mode
if os.environ.get("LLMXIVE_DEBUG", "").lower() in ("1", "true", "yes"):
    log_environment_config()
