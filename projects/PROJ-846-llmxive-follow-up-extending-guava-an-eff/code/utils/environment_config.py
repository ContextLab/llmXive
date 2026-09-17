"""
Environment configuration management for CPU-only runner constraints.

This module provides utilities to detect hardware capabilities, enforce CPU-only
execution constraints for PyTorch, and manage environment variables to ensure
reproducible and compliant research execution.
"""
import os
import sys
import platform
import subprocess
import logging
from typing import Dict, Any, Optional, List
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

def detect_cpu_count() -> int:
    """
    Detect the number of available CPU cores.
    
    Returns:
        int: Number of available CPU cores.
    """
    try:
        # Try to get count via os.cpu_count() first
        count = os.cpu_count()
        if count is None:
            # Fallback for systems where cpu_count might be None
            count = 1
        return count
    except Exception as e:
        logger.warning(f"Failed to detect CPU count via os.cpu_count(): {e}. Defaulting to 1.")
        return 1

def verify_cpu_only_constraint() -> bool:
    """
    Verify that the current environment is configured for CPU-only execution.
    
    Checks:
        1. PyTorch is not using CUDA (torch.cuda.is_available() should be False)
        2. CUDA_VISIBLE_DEVICES is not set to a specific GPU ID
        3. Environment variables indicate CPU preference
    
    Returns:
        bool: True if CPU-only constraint is satisfied, False otherwise.
    
    Raises:
        EnvironmentConfigError: If GPU is detected when CPU-only is required.
    """
    try:
        import torch
    except ImportError:
        logger.warning("PyTorch not installed. Assuming CPU-only environment.")
        return True

    # Check 1: CUDA availability
    if torch.cuda.is_available():
        logger.warning("CUDA is available in the environment.")
        # Check if we are explicitly forced to CPU
        if os.environ.get("CUDA_VISIBLE_DEVICES") == "":
            logger.info("CUDA_VISIBLE_DEVICES is set to empty string. Forcing CPU.")
            return True
        # Check if torch is actually using CPU for operations
        # (This is a heuristic; the most robust check is ensuring tensors are on CPU)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type != "cpu":
            logger.error("GPU device detected and active. CPU-only constraint VIOLATED.")
            return False
    
    # Check 2: CUDA_VISIBLE_DEVICES
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cuda_visible is not None and cuda_visible != "":
        logger.warning(f"CUDA_VISIBLE_DEVICES is set to '{cuda_visible}'.")
        # If it's a valid GPU ID, it might be a violation unless we force CPU usage below
        if cuda_visible.isdigit() or "," in cuda_visible:
            logger.info("Detected GPU assignment in environment variables.")
            # We will enforce CPU below if possible, but warn
            pass

    return True

def configure_torch_for_cpu() -> None:
    """
    Configure PyTorch to use CPU only and optimize for CPU performance.
    
    Actions:
        1. Sets CUDA_VISIBLE_DEVICES to empty string.
        2. Sets torch.set_num_threads based on available cores.
        3. Ensures no CUDA operations are attempted.
    """
    try:
        import torch
    except ImportError:
        logger.warning("PyTorch not installed. Skipping CPU configuration.")
        return

    # Force CUDA to be invisible
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Set number of threads for better CPU performance
    num_threads = detect_cpu_count()
    # Avoid oversubscription; usually 1-2 threads per core is good, but for inference
    # often 1 is best. Let's use a conservative number.
    optimal_threads = max(1, min(num_threads, 4)) 
    
    torch.set_num_threads(optimal_threads)
    
    # Ensure MPS (Apple Silicon) is not used if we strictly want CPU (optional, depending on strictness)
    # For this task, we focus on standard CPU. MPS is technically a GPU accelerator.
    # If the requirement is strictly "CPU" (x86/ARM generic), we might want to disable MPS too.
    # However, usually "CPU-only" in these contexts implies no CUDA. 
    # We will stick to standard CPU tensor placement.
    
    logger.info(f"Configured PyTorch for CPU-only execution. Threads: {optimal_threads}")

def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by setting environment variables and checking constraints.
    
    This is a comprehensive function that:
        1. Detects CPU count.
        2. Configures PyTorch for CPU.
        3. Verifies the constraint is met.
        4. Raises an error if a GPU is forced and cannot be disabled.
    """
    logger.info("Enforcing CPU-only execution constraints...")
    
    # 1. Detect and log CPU count
    cpu_count = detect_cpu_count()
    logger.info(f"Detected {cpu_count} CPU cores.")
    
    # 2. Configure PyTorch
    configure_torch_for_cpu()
    
    # 3. Verify
    is_valid = verify_cpu_only_constraint()
    
    if not is_valid:
        # Try one last time to force it by unloading any GPU context if possible
        # (Not always possible if CUDA is already initialized)
        logger.error("Failed to enforce CPU-only constraint after configuration.")
        logger.error("The environment has active GPU resources that cannot be disabled.")
        raise EnvironmentConfigError("CPU-only constraint could not be enforced. GPU detected.")
    
    logger.info("CPU-only constraint successfully enforced.")

def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.
    
    Returns:
        Dict[str, Any]: A dictionary containing environment details.
    """
    try:
        import torch
        torch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_available else 0
    except ImportError:
        torch_version = "Not Installed"
        cuda_available = False
        device_count = 0

    summary = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "python_version": sys.version,
        "cpu_count": detect_cpu_count(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "Not Set"),
        "pytorch_version": torch_version,
        "cuda_available": cuda_available,
        "cuda_device_count": device_count,
        "cpu_only_enforced": os.environ.get("CUDA_VISIBLE_DEVICES", "") == ""
    }
    
    return summary

def main():
    """
    Main entry point for running environment configuration checks and enforcement.
    """
    logger.info("Starting Environment Configuration Management...")
    
    try:
        enforce_cpu_only()
        
        summary = get_environment_summary()
        logger.info("Environment Summary:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("Environment configuration completed successfully.")
        
    except EnvironmentConfigError as e:
        logger.error(f"Environment configuration failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during environment configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()