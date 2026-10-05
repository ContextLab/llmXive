"""
Environment validation and device detection utility.

This module checks for CUDA availability and writes the detected
training device configuration to the runtime config file.
"""
import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

# Import from project config
from config import get_path_results, ensure_directory, load_runtime_config, save_runtime_config

# Import logging infrastructure
from logging_config import get_logger, log_event

logger = get_logger(__name__)


def check_cuda_visible_devices() -> bool:
    """
    Check if CUDA_VISIBLE_DEVICES environment variable is set and non-empty.

    Returns:
        bool: True if the variable is set to a non-empty string, False otherwise.
    """
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    return bool(cuda_visible and cuda_visible.strip() != "")


def check_nvidia_smi() -> bool:
    """
    Check if nvidia-smi is available and returns valid GPU information.

    Returns:
        bool: True if nvidia-smi is found and returns success, False otherwise.
    """
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

    Checks in order:
    1. CUDA_VISIBLE_DEVICES environment variable
    2. nvidia-smi availability and GPU presence
    3. PyTorch CUDA availability

    Returns:
        str: "cuda" if GPU is detected, "cpu" otherwise.
    """
    # Check 1: Environment variable
    if check_cuda_visible_devices():
        logger.info("CUDA_VISIBLE_DEVICES environment variable detected.")
        return "cuda"

    # Check 2: nvidia-smi
    if check_nvidia_smi():
        logger.info("nvidia-smi detected available GPU(s).")
        return "cuda"

    # Check 3: PyTorch CUDA
    if check_torch_cuda():
        logger.info("PyTorch CUDA support detected.")
        return "cuda"

    logger.info("No GPU detected. Defaulting to CPU.")
    return "cpu"


def write_runtime_config(device: str) -> Dict[str, Any]:
    """
    Write the training device configuration to the runtime config file.

    Args:
        device (str): The detected training device ("cuda" or "cpu").

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

    # Save the updated config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(current_config, f, indent=2)

    logger.info(f"Runtime config written to {config_path}: {current_config}")
    return current_config


def main() -> int:
    """
    Main entry point for environment validation and device detection.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        logger.info("Starting environment validation and device detection.")

        # Detect the training device
        device = detect_training_device()

        # Write the configuration
        config = write_runtime_config(device)

        logger.info(f"Environment validation complete. Device: {device}")
        return 0

    except Exception as e:
        logger.error(f"Error during environment validation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    from datetime import datetime  # Local import to avoid circular issues if any

    exit_code = main()
    sys.exit(exit_code)