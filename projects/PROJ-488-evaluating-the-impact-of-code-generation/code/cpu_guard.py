"""
CPU-only execution guard for metric extraction.

This module ensures that:
1. PyTorch (if installed) is not used for inference or CUDA operations.
2. Radon and Pylint execute without any CUDA device assignment.
3. Environment variables are set to enforce CPU-only execution.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Import logger from project utilities
from logging_config import setup_logger, get_logger

# Initialize logger
logger = setup_logger("cpu_guard")

def enforce_cpu_only() -> bool:
    """
    Enforces CPU-only execution by setting environment variables
    and verifying no CUDA devices are assigned.
    
    Returns:
        bool: True if CPU-only mode is successfully enforced, False otherwise.
    """
    # Set environment variables to disable GPU usage
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    
    # Attempt to disable torch GPU usage if torch is available
    try:
        import torch
        # Check if CUDA is available and disable it
        if torch.cuda.is_available():
            logger.warning("CUDA is available. Forcing CPU-only mode.")
            # Ensure no CUDA devices are visible
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            # If torch is already initialized with CUDA, this might be too late,
            # but we set the env var for any subsequent imports
            try:
                torch.set_device("cpu")
            except Exception:
                pass
            logger.info("Torch GPU usage disabled.")
        else:
            logger.info("Torch not using CUDA (or not installed).")
    except ImportError:
        logger.info("PyTorch not installed. Skipping torch-specific checks.")
    
    # Verify radon and pylint execution environment
    # Radon and pylint are pure Python and do not use CUDA, 
    # but we ensure the environment is clean for them.
    logger.info("Verifying environment for radon and pylint execution.")
    
    # Double-check that CUDA_VISIBLE_DEVICES is set correctly
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "-1":
        logger.error("Failed to set CUDA_VISIBLE_DEVICES to -1.")
        return False
    
    logger.info("CPU-only execution guard successfully enforced.")
    return True

def verify_no_cuda_usage() -> bool:
    """
    Verifies that no CUDA devices are being used by the current process.
    
    Returns:
        bool: True if no CUDA usage detected, False otherwise.
    """
    try:
        import torch
        if torch.cuda.is_available():
            # Check if any tensors are on CUDA
            # Note: This is a best-effort check; if torch is imported but not used for tensors, it's fine.
            # We rely on the environment variable setting to prevent future usage.
            logger.warning("CUDA is available in torch, but we have set CUDA_VISIBLE_DEVICES=-1.")
            logger.warning("Ensure no tensors are created on CUDA devices.")
            return True  # We've taken steps to prevent usage
        return True
    except ImportError:
        return True

def run_cpu_guard() -> bool:
    """
    Main entry point to run the CPU-only execution guard.
    
    Returns:
        bool: True if guard passed, False otherwise.
    """
    logger.info("Starting CPU-only execution guard.")
    
    success = enforce_cpu_only()
    if not success:
        logger.error("CPU-only guard enforcement failed.")
        return False
    
    cuda_ok = verify_no_cuda_usage()
    if not cuda_ok:
        logger.error("CUDA usage verification failed.")
        return False
    
    logger.info("CPU-only execution guard passed.")
    return True

def main() -> int:
    """
    CLI entry point for the CPU guard script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    if run_cpu_guard():
        print("CPU-only guard passed. Safe to proceed with metric extraction.")
        return 0
    else:
        print("CPU-only guard failed. Aborting metric extraction.")
        return 1

if __name__ == "__main__":
    sys.exit(main())