"""
Environment checking utilities for llmXive.

Provides functions to detect CUDA availability and enforce CPU-only execution constraints.
"""
import logging
import torch
from typing import Tuple, Optional
from utils.logger import get_logger_for_task

def detect_cuda_availability(forced_device: str = "cpu") -> Tuple[bool, str]:
    """
    Check if CUDA is available and log a warning if it is when CPU is forced.
    
    This function is critical for the execution gate to distinguish between:
    1. An intentional CPU run (CUDA available but ignored)
    2. An accidental GPU fallback (CUDA used when it shouldn't be)
    
    Args:
        forced_device: The device string that was forced in the configuration.
                       Expected value: "cpu"
    
    Returns:
        A tuple of (is_cuda_available, status_message)
        - is_cuda_available: True if torch.cuda.is_available() returns True
        - status_message: A descriptive string about the CUDA status
    """
    is_cuda_available = torch.cuda.is_available()
    logger = get_logger_for_task("T050", "env_check")
    
    if is_cuda_available and forced_device == "cpu":
        cuda_device_count = torch.cuda.device_count()
        cuda_device_name = torch.cuda.get_device_name(0) if cuda_device_count > 0 else "Unknown"
        
        warning_msg = (
            f"CUDA IS AVAILABLE but device is forced to 'cpu'. "
            f"Detected {cuda_device_count} GPU(s): {cuda_device_name}. "
            f"Execution will proceed on CPU only. If this was unintended, "
            f"remove the 'device=cpu' constraint to utilize GPU acceleration."
        )
        logger.warning(warning_msg)
        return True, warning_msg
    
    elif is_cuda_available and forced_device != "cpu":
        cuda_device_count = torch.cuda.device_count()
        cuda_device_name = torch.cuda.get_device_name(0) if cuda_device_count > 0 else "Unknown"
        info_msg = (
            f"CUDA is available and will be used. "
            f"Detected {cuda_device_count} GPU(s): {cuda_device_name}."
        )
        logger.info(info_msg)
        return True, info_msg
    
    else:
        info_msg = (
            "CUDA is NOT available. Execution will proceed on CPU only. "
            "Ensure this is the intended configuration for the experiment."
        )
        logger.info(info_msg)
        return False, info_msg

def enforce_cpu_only() -> str:
    """
    Enforce CPU-only execution by checking CUDA availability and raising an error if found.
    
    This is a stricter version of detect_cuda_availability that fails the execution
    if any GPU is detected, ensuring the experiment runs strictly on CPU as required
    by the project constraints.
    
    Returns:
        A success message if CPU-only execution is confirmed
    
    Raises:
        RuntimeError: If CUDA is detected
    """
    is_cuda_available, msg = detect_cuda_availability(forced_device="cpu")
    if is_cuda_available:
        raise RuntimeError(
            f"CPU-only execution enforced but CUDA is available. "
            f"This violates the project constraints. "
            f"Detected GPU: {msg}"
        )
    return "CPU-only execution confirmed. No CUDA devices detected."

def main():
    """
    Main entry point for standalone execution of environment checks.
    Useful for debugging and verification of the execution environment.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger("env_check_main")
    logger.info("Starting environment check for llmXive...")
    
    is_available, status = detect_cuda_availability(forced_device="cpu")
    logger.info(f"CUDA Status: {status}")
    
    if not is_available:
        logger.info("Environment check passed: CPU-only execution confirmed.")
    else:
        logger.warning("Environment check warning: CUDA detected but CPU forced.")
    
    return 0

if __name__ == "__main__":
    exit(main())