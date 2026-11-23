"""
GPU Offload Logic for DiT Generation Tasks.

This module detects CPU failure on DiT generation tasks (specifically for FLUX.1-dev
and Wan 2.1 models) and triggers the Kaggle GPU offload mechanism.

It provides a robust check for CUDA availability and model compatibility, raising
a specific exception when CPU execution is detected for tasks that require GPU,
allowing the orchestration layer to trigger the offload.
"""

import os
import sys
import json
import logging
import torch
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for GPU Offload
OFFLOAD_FLAG_ENV = "LLMXIVE_GPU_OFFLOAD_TRIGGERED"
OFFLOAD_LOG_PATH = "state/gpu_offload_log.json"
OFFLOAD_RETRY_COUNT = 0
MAX_OFFLOAD_RETRIES = 1

class GPUOffloadError(RuntimeError):
    """
    Custom exception raised when a DiT generation task is detected on CPU
    but requires GPU. This signals the orchestration layer to trigger
    the Kaggle GPU offload mechanism.
    """
    def __init__(self, message: str, model_name: str, required_device: str = "cuda"):
        super().__init__(message)
        self.model_name = model_name
        self.required_device = required_device
        self.timestamp = torch.cuda.is_available() and torch.cuda.current_device() >= 0

def check_gpu_availability(model_name: str = "flux.1-dev") -> Tuple[bool, Optional[str]]:
    """
    Checks if a GPU is available and if the specified model can be loaded on it.

    Args:
        model_name: Name of the DiT model to check (e.g., "flux.1-dev", "wan-2.1")

    Returns:
        Tuple of (is_gpu_available, error_message)
        - is_gpu_available: True if GPU is available and compatible
        - error_message: None if successful, otherwise a descriptive error string
    """
    if not torch.cuda.is_available():
        return False, f"CUDA is not available. Model '{model_name}' requires GPU for DiT generation."

    try:
        # Check if we can actually allocate memory (sometimes CUDA is available but OOM)
        test_tensor = torch.zeros(1024, 1024).cuda()
        del test_tensor
        torch.cuda.empty_cache()
        return True, None
    except RuntimeError as e:
        return False, f"GPU memory allocation failed for '{model_name}': {str(e)}"

def trigger_offload_log(model_name: str, error: str) -> None:
    """
    Logs the offload trigger event to state/gpu_offload_log.json for audit and
    orchestration tracking.

    Args:
        model_name: The model that triggered the offload
        error: The error message that caused the trigger
    """
    log_path = Path("state") / OFFLOAD_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "model": model_name,
        "error": error,
        "timestamp": torch.cuda.is_available() and torch.cuda.current_device() >= 0,
        "action": "offload_triggered",
        "environment": os.getenv("KAGGLE_KERNEL_RUN_TYPE", "unknown")
    }

    # Append to log file
    log_data = []
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = []

    log_data.append(entry)

    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)

    logger.warning(f"Offload trigger logged to {log_path}: {error}")

def enforce_gpu_requirement(model_name: str, config: Optional[Config] = None) -> None:
    """
    Enforces the GPU requirement for DiT generation tasks.

    If GPU is not available, raises GPUOffloadError to trigger the offload mechanism.
    If the environment variable LLMXIVE_GPU_OFFLOAD_TRIGGERED is set, it assumes
    the offload has already been handled and proceeds (preventing infinite loops).

    Args:
        model_name: Name of the DiT model
        config: Optional Config instance for device settings

    Raises:
        GPUOffloadError: If GPU is required but not available
    """
    # Check if we are already in an offloaded environment
    if os.getenv(OFFLOAD_FLAG_ENV) == "1":
        logger.info(f"Running in offloaded GPU environment for '{model_name}'. Proceeding.")
        return

    is_available, error_msg = check_gpu_availability(model_name)

    if not is_available:
        logger.error(f"GPU requirement check failed for '{model_name}': {error_msg}")
        trigger_offload_log(model_name, error_msg)
        raise GPUOffloadError(
            message=f"GPU Offload Required: {error_msg}",
            model_name=model_name
        )

    logger.info(f"GPU verified available for '{model_name}'. Proceeding with generation.")

def get_offload_command(model_name: str) -> str:
    """
    Generates the command to re-run the current task in a GPU environment.
    This is used by the orchestration layer to trigger the offload.

    Args:
        model_name: The model being processed

    Returns:
        A shell command string to re-run the task with GPU offload flag
    """
    # Construct the command to re-run the current script with the offload flag
    script_path = sys.argv[0] if sys.argv[0] else sys.executable
    return f"{OFFLOAD_FLAG_ENV}=1 {sys.executable} {script_path} --model={model_name}"

def main():
    """
    Main entry point for GPU offload validation.
    This function is typically called at the start of DiT generation tasks
    (e.g., T017, T046) to ensure GPU availability before heavy computation.
    """
    config = Config()
    model_name = getattr(config, 'model_name', 'flux.1-dev')

    logger.info(f"Starting GPU offload validation for model: {model_name}")

    try:
        enforce_gpu_requirement(model_name, config)
        logger.info("GPU offload validation passed.")
        return True
    except GPUOffloadError as e:
        logger.error(f"GPU offload validation failed: {e}")
        # In a real orchestration context, this would trigger the offload
        # For this module, we just return False to indicate failure
        return False
    except Exception as e:
        logger.critical(f"Unexpected error during GPU validation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)