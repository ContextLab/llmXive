"""
Environment validation and device detection utility.

This module strictly enforces CPU-only execution per Plan constraints.
It does NOT enable GPU offloading or detect GPU drivers for training.
It always defaults to 'cpu' and writes this configuration to the runtime config.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import from project config
from config import get_path_results, ensure_directory, load_runtime_config, save_runtime_config

# Import logging infrastructure
from logging_config import get_logger, log_event

logger = get_logger(__name__)


def check_cuda_visible_devices() -> bool:
    """
    Check if CUDA_VISIBLE_DEVICES environment variable is set and non-empty.
    
    NOTE: This check is performed for diagnostic/logging purposes only.
    The task constraints mandate CPU-only execution regardless of this check.

    Returns:
        bool: True if the variable is set to a non-empty string, False otherwise.
    """
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    return bool(cuda_visible and cuda_visible.strip() != "")


def check_nvidia_smi() -> bool:
    """
    Check if nvidia-smi is available and returns valid GPU information.
    
    NOTE: This check is performed for diagnostic/logging purposes only.
    The task constraints mandate CPU-only execution regardless of this check.

    Returns:
        bool: True if nvidia-smi is found and returns success, False otherwise.
    """
    import shutil
    import subprocess

    if not shutil.which("nvidia-smi"):
        return False

    try:
        # Run nvidia-smi with a simple query to check GPU availability
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


def check_torch_cuda() -> bool:
    """
    Check if PyTorch is available and CUDA is supported.
    
    NOTE: This check is performed for diagnostic/logging purposes only.
    The task constraints mandate CPU-only execution regardless of this check.

    Returns:
        bool: True if PyTorch is installed and CUDA is available, False otherwise.
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
    except Exception as e:
        logger.warning(f"Error checking torch.cuda.is_available(): {e}")
        return False


def detect_training_device() -> str:
    """
    Detect the appropriate training device based on environment.
    
    CRITICAL CONSTRAINT: Per Plan constraints, this function strictly enforces
    CPU-only execution. It does NOT enable GPU offloading. It always returns "cpu".
    
    Diagnostic checks (CUDA_VISIBLE_DEVICES, nvidia-smi, torch.cuda) are performed
    only to log the environment state, not to influence the device selection.

    Returns:
        str: Always returns "cpu" to enforce Plan constraints.
    """
    # Diagnostic: Log environment state
    if check_cuda_visible_devices():
        logger.info("WARNING: CUDA_VISIBLE_DEVICES detected, but CPU-only mode enforced.")
    elif check_nvidia_smi():
        logger.info("WARNING: nvidia-smi detected, but CPU-only mode enforced.")
    elif check_torch_cuda():
        logger.info("WARNING: PyTorch CUDA support detected, but CPU-only mode enforced.")
    else:
        logger.info("No GPU detected or GPU disabled.")

    # Enforce CPU-only per Plan constraints
    logger.info("Enforcing CPU-only execution per Plan constraints.")
    return "cpu"


def write_runtime_config(device: str) -> Dict[str, Any]:
    """
    Write the training device configuration to the runtime config file.
    
    This function ensures the 'training_device' key is set in the runtime config.
    The device argument is expected to be 'cpu' as per the enforceable constraint.

    Args:
        device (str): The training device configuration (expected "cpu").

    Returns:
        Dict[str, Any]: The updated runtime configuration.
    """
    results_dir = get_path_results()
    ensure_directory(results_dir)

    config_path = Path(results_dir) / "runtime_config.json"

    # Load existing config if it exists, otherwise start fresh
    try:
        current_config = load_runtime_config()
    except FileNotFoundError:
        current_config = {}

    # Update with the detected device
    current_config["training_device"] = device
    current_config["device_detected_at"] = datetime.now().isoformat()
    current_config["cpu_only_enforced"] = True

    # Save the updated config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current_config, f, indent=2)

    logger.info(f"Runtime config written to {config_path}: {current_config}")
    return current_config


def main() -> int:
    """
    Main entry point for environment validation and device detection.
    
    This function enforces CPU-only execution and writes the configuration.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        logger.info("Starting environment validation and device detection.")

        # Detect the training device (enforced to CPU)
        device = detect_training_device()

        # Write the configuration
        config = write_runtime_config(device)

        logger.info(f"Environment validation complete. Device: {device} (CPU-only enforced)")
        return 0

    except Exception as e:
        logger.error(f"Error during environment validation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)