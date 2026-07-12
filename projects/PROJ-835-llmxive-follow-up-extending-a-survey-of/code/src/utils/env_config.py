"""
Environment configuration utilities.
Enforces CPU-only execution and manages environment variables.
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

# Enforce CPU-only at module load time
os.environ["CUDA_VISIBLE_DEVICES"] = ""


def enforce_cpu_only() -> None:
    """
    Explicitly enforce CPU-only execution by setting CUDA_VISIBLE_DEVICES.
    This should be called at the very beginning of the pipeline.
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    logger.info("Enforced CPU-only execution (CUDA_VISIBLE_DEVICES='').")


def is_cpu_only_mode() -> bool:
    """
    Check if CPU-only mode is currently enforced.
    
    Returns:
        True if CUDA_VISIBLE_DEVICES is empty or not set, False otherwise.
    """
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    return cuda_devices == ""


def log_environment_config() -> None:
    """
    Log the current environment configuration for debugging and auditing.
    """
    logger.info("Environment Configuration:")
    logger.info(f"  CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'NOT SET')}")
    logger.info(f"  CPU-only mode: {is_cpu_only_mode()}")
    
    # Log Python and system info
    logger.info(f"  Python version: {sys.version}")
    logger.info(f"  Platform: {sys.platform}")
