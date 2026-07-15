"""
CPU Guard Module.
Ensures that execution is restricted to CPU and prevents CUDA usage.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from logging_config import setup_logger, get_logger

def enforce_cpu_only():
    """Enforce CPU-only execution by setting environment variables."""
    logger = get_logger("cpu_guard")
    
    # Set CUDA_VISIBLE_DEVICES to empty string to disable GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Check if torch is installed and force CPU
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("PyTorch CUDA is available. Forcing CPU mode...")
            torch.set_num_threads(1) # Limit threads to reduce accidental GPU load
            # Note: We cannot force torch to not use GPU if code explicitly calls .cuda()
            # but we can prevent initialization if not needed.
            # The best we can do here is warn and set env vars.
            logger.warning("Environment variable CUDA_VISIBLE_DEVICES set to ''")
    except ImportError:
        logger.info("PyTorch not installed. Skipping torch-specific checks.")
        
    # Verify radon and pylint do not use CUDA
    # These are CPU-only tools by design, but we log confirmation
    logger.info("Radon and Pylint are CPU-only tools. No CUDA configuration needed.")
    
    logger.info("CPU-only mode enforced.")

def verify_no_cuda_usage():
    """Verify that no CUDA devices are being used."""
    logger = get_logger("cpu_guard")
    
    # Check environment variable
    cuda_dev = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cuda_dev == "":
        logger.info("CUDA_VISIBLE_DEVICES is empty. GPU access disabled.")
        return True
    elif cuda_dev is None:
        logger.warning("CUDA_VISIBLE_DEVICES is not set. Checking torch...")
        try:
            import torch
            if torch.cuda.is_available():
                logger.warning("CUDA is available but not explicitly disabled. Proceeding with caution.")
                return False # Warning state
        except ImportError:
            pass
    else:
        logger.warning(f"CUDA_VISIBLE_DEVICES is set to '{cuda_dev}'. GPU access may be enabled.")
        return False
        
    return True

def run_cpu_guard():
    """Run the full CPU guard workflow."""
    logger = setup_logger("cpu_guard", log_file="results/cpu_guard.log")
    logger.info("Running CPU Guard...")
    
    enforce_cpu_only()
    is_safe = verify_no_cuda_usage()
    
    if not is_safe:
        logger.error("CPU Guard check failed. GPU access detected or not properly disabled.")
        raise RuntimeError("CPU Guard Failed: GPU access detected.")
        
    logger.info("CPU Guard passed.")
    return True

def main():
    """Entry point."""
    try:
        run_cpu_guard()
        print("CPU Guard passed.")
    except RuntimeError as e:
        print(f"CPU Guard failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
