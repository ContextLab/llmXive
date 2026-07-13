import os
import sys
import logging
from pathlib import Path
from typing import Optional

from logging_config import setup_logger, get_logger

# Configure logger for this module
logger = get_logger(__name__)

def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by setting environment variables
    and verifying no CUDA usage is configured.
    
    This function:
    1. Sets CUDA_VISIBLE_DEVICES to empty string to disable GPU usage
    2. Checks if torch is imported and if CUDA is available
    3. Raises an error if CUDA is detected or configured
    """
    # Force CPU-only environment variable
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    
    # Check if torch is available and if it thinks CUDA is available
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available in torch but will be disabled via environment variables")
            # Double check that we've effectively disabled it
            if torch.cuda.device_count() > 0:
                logger.error("CUDA devices still detected after setting environment variables")
                raise RuntimeError("CUDA devices detected despite CPU-only enforcement")
    except ImportError:
        # torch not installed, which is fine for this task
        logger.info("PyTorch not installed, skipping CUDA checks")
        pass

    # Verify radon and pylint don't require CUDA
    # These are static analysis tools and should never use CUDA
    try:
        import radon
        logger.debug("radon imported successfully (CPU-only static analysis)")
    except ImportError:
        logger.error("radon not installed, required for metric extraction")
        raise

    try:
        import pylint
        logger.debug("pylint imported successfully (CPU-only static analysis)")
    except ImportError:
        logger.error("pylint not installed, required for metric extraction")
        raise

    logger.info("CPU-only execution enforced successfully")

def verify_no_cuda_usage() -> bool:
    """
    Verify that no CUDA-related operations are being attempted.
    
    Returns:
        bool: True if no CUDA usage detected, False otherwise
    """
    # Check environment variables
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_visible != "":
        logger.warning(f"CUDA_VISIBLE_DEVICES is set to: {cuda_visible}")
        return False

    # Check torch status if available
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("torch.cuda.is_available() returned True")
            return False
        if torch.cuda.device_count() > 0:
            logger.warning(f"torch reports {torch.cuda.device_count()} CUDA devices")
            return False
    except ImportError:
        pass  # torch not installed, which is fine

    # Verify radon and pylint are available (they don't use CUDA)
    try:
        import radon
        import pylint
        logger.info("radon and pylint are available (CPU-only tools)")
        return True
    except ImportError as e:
        logger.error(f"Required static analysis tool not available: {e}")
        return False

def run_cpu_guard() -> None:
    """
    Main entry point for CPU-only guard.
    
    This function:
    1. Enforces CPU-only execution
    2. Verifies no CUDA usage
    3. Raises an error if verification fails
    """
    logger.info("Starting CPU-only execution guard")
    
    enforce_cpu_only()
    
    if not verify_no_cuda_usage():
        error_msg = "CPU-only guard verification failed: CUDA usage detected or required tools missing"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("CPU-only guard verification passed")

def main():
    """
    Command-line entry point for CPU-only guard.
    
    This allows the guard to be run as a standalone script:
    python code/cpu_guard.py
    """
    # Setup logger for standalone execution
    setup_logger(level=logging.INFO)
    
    try:
        run_cpu_guard()
        logger.info("CPU-only guard completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"CPU-only guard failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()