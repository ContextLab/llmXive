"""
CPU-only execution guard module.

This module ensures that the pipeline runs strictly on CPU:
1. Verifies torch is not used for inference (no CUDA device assignment).
2. Ensures radon and pylint execute without GPU acceleration.
3. Sets environment variables to force CPU-only execution if torch is available.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from logging_config import setup_logger, get_logger

# Initialize logger
logger = get_logger("cpu_guard")

def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by setting environment variables
    and verifying no CUDA usage.
    
    This function:
    1. Sets CUDA_VISIBLE_DEVICES to empty string to hide GPUs.
    2. Sets TORCH_USE_CPU_ONLY environment variable.
    3. Verifies torch is not available or not using CUDA.
    """
    logger.info("Enforcing CPU-only execution mode")
    
    # Hide CUDA devices
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Set torch CPU-only flag if available
    os.environ["TORCH_USE_CPU_ONLY"] = "1"
    
    # Check if torch is installed and if it tries to use CUDA
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available but will be disabled for this run")
            # Force torch to use CPU
            if torch.cuda.device_count() > 0:
                torch.cuda.set_device(-1)  # Invalid device ID to force CPU
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            logger.info("Successfully disabled CUDA for torch")
    except ImportError:
        logger.info("PyTorch not installed, skipping torch-specific checks")
    
    # Ensure radon and pylint are not configured for GPU
    # These tools are CPU-only by design, but we verify no GPU env vars are set
    if "PYTORCH_CUDA_ALLOC_CONF" in os.environ:
        logger.warning("Removing PYTORCH_CUDA_ALLOC_CONF to ensure CPU-only execution")
        del os.environ["PYTORCH_CUDA_ALLOC_CONF"]
        
    logger.info("CPU-only execution enforced successfully")

def verify_no_cuda_usage() -> bool:
    """
    Verify that no CUDA device is being used by any loaded libraries.
    
    Returns:
        bool: True if no CUDA usage detected, False otherwise
    """
    logger.info("Verifying no CUDA usage")
    
    # Check torch
    try:
        import torch
        if torch.cuda.is_available():
            # Check if any tensors are on CUDA
            if torch.cuda.device_count() > 0:
                logger.error("CUDA is available and may be in use")
                return False
    except ImportError:
        pass  # torch not installed, that's fine
    
    # Check if any GPU-related environment variables are set
    gpu_vars = [
        "CUDA_VISIBLE_DEVICES",
        "CUDA_DEVICE_ORDER",
        "PYTORCH_CUDA_ALLOC_CONF",
        "CUDA_LAUNCH_BLOCKING"
    ]
    
    for var in gpu_vars:
        if var in os.environ and os.environ[var]:
            # Empty string is acceptable (means "no GPUs")
            if os.environ[var] != "":
                logger.warning(f"Environment variable {var} is set to non-empty value: {os.environ[var]}")
                # For CUDA_VISIBLE_DEVICES, empty string is the correct way to disable
                if var == "CUDA_VISIBLE_DEVICES" and os.environ[var] == "":
                    continue
                # For others, warn but don't fail unless they explicitly enable GPU
                if "1" in os.environ[var] or "0" in os.environ[var]:
                    logger.error(f"GPU-related environment variable {var} appears to enable GPU usage")
                    return False
    
    logger.info("No CUDA usage detected")
    return True

def run_cpu_guard() -> bool:
    """
    Run the complete CPU guard workflow.
    
    Returns:
        bool: True if CPU-only guard passed, False otherwise
    """
    logger.info("Starting CPU-only execution guard")
    
    # Step 1: Enforce CPU-only mode
    enforce_cpu_only()
    is_safe = verify_no_cuda_usage()
    
    # Step 2: Verify no CUDA usage
    if not verify_no_cuda_usage():
        logger.error("CPU-only guard failed: CUDA usage detected or cannot be disabled")
        return False
    
    # Step 3: Verify radon and pylint are CPU-only
    # radon is pure Python, pylint uses ast which is CPU-only
    # We just verify they can be imported without GPU dependencies
    try:
        import radon
        logger.info("radon imported successfully (CPU-only)")
    except ImportError:
        logger.error("radon not installed, cannot verify CPU-only execution")
        return False
        
    try:
        import pylint
        logger.info("pylint imported successfully (CPU-only)")
    except ImportError:
        logger.error("pylint not installed, cannot verify CPU-only execution")
        return False
    
    logger.info("CPU-only execution guard passed successfully")
    return True

def main():
    """Main entry point for CPU guard verification."""
    logger.info("Running CPU-only execution guard as main")
    success = run_cpu_guard()
    if success:
        logger.info("CPU-only guard: PASSED")
        sys.exit(0)
    else:
        logger.error("CPU-only guard: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
