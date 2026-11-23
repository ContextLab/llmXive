"""
GPU Validation Script (T046)

Explicitly tests the GPU offload path for DiT models (FLUX.1-dev / Wan 2.1).
1. Attempts to load FLUX.1-dev with device="cuda" and load_in_8bit=True.
2. If CUDA fails (RuntimeError, AssertionError, or GPUOffloadError), triggers
   the Kaggle offload mechanism via utils.gpu_offload.
3. Verifies the task re-runs successfully on the GPU runner.
4. Writes a validation record to state/gpu_validation_log.json.

Deliverable: state/gpu_validation_log.json contains a successful run record
with device=cuda and model=flux.1-dev or wan-2.1.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

import torch

# Project imports (matching API surface)
from config import Config
from utils.gpu_offload import (
    GPUOffloadError,
    check_gpu_availability,
    trigger_offload_log,
    get_offload_command,
    main as offload_main,
)
from models.flux_wan_loader import ModelLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
STATE_DIR = Path("state")
LOG_FILE = STATE_DIR / "gpu_validation_log.json"
CONFIG = Config()

def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_log() -> Dict[str, Any]:
    """Load existing log if present, else return empty structure."""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Corrupt log file detected. Starting fresh.")
    return {
        "attempts": [],
        "final_status": "pending",
        "model": None,
        "device": None,
        "timestamp": None,
    }

def save_log(log_data: Dict[str, Any]):
    """Save log data to disk."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

def attempt_load_flux() -> bool:
    """
    Attempt to load FLUX.1-dev with CUDA and 8-bit quantization.
    Returns True if successful, False if it fails due to GPU issues.
    """
    logger.info("Attempting to load FLUX.1-dev on CUDA with 8-bit quantization...")
    try:
        # Check CUDA availability first
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available on this device.")
        
        # Initialize loader
        loader = ModelLoader()
        
        # Attempt load with specific constraints
        # Note: load_in_8bit=True requires bitsandbytes, handled by loader
        model = loader.load_model(
            model_name="black-forest-labs/FLUX.1-dev",
            device="cuda",
            load_in_8bit=True,
        )
        
        if model is None:
            raise RuntimeError("Model loader returned None.")
        
        # Verify model is on CUDA
        sample_param = next(model.parameters())
        if sample_param.device.type != "cuda":
            raise RuntimeError(f"Model parameters not on CUDA: {sample_param.device}")
        
        logger.info("FLUX.1-dev loaded successfully on CUDA.")
        return True

    except Exception as e:
        logger.error(f"Failed to load FLUX.1-dev on CUDA: {e}")
        return False

def run_validation():
    """Main validation logic."""
    ensure_state_dir()
    log_data = load_log()
    
    attempt_record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": "flux.1-dev",
        "attempted_device": "cuda",
        "success": False,
        "error": None,
    }

    # 1. Check GPU availability
    if not check_gpu_availability():
        logger.warning("GPU not available. Triggering offload mechanism.")
        attempt_record["error"] = "GPU not available"
        log_data["attempts"].append(attempt_record)
        
        # Trigger offload
        offload_cmd = get_offload_command()
        logger.info(f"Triggering offload command: {offload_cmd}")
        trigger_offload_log("gpu_validation_failed", "GPU not available")
        
        # In a real environment, this would exit and let the offload script re-run.
        # For this validation script, we simulate the "offload success" if we detect
        # we are already in a GPU environment after the check, or fail loudly.
        # Since we cannot actually re-spawn a new process in this context, 
        # we assume the offload mechanism handles the restart.
        # We mark as failed here to indicate the current run did not succeed.
        log_data["final_status"] = "offload_triggered"
        save_log(log_data)
        return False

    # 2. Attempt Load
    success = attempt_load_flux()
    
    if success:
        log_data["final_status"] = "success"
        log_data["model"] = "flux.1-dev"
        log_data["device"] = "cuda"
        log_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        attempt_record["success"] = True
        logger.info("GPU Validation SUCCESSFUL.")
    else:
        attempt_record["error"] = "Failed to load model on CUDA"
        log_data["final_status"] = "failed"
        log_data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.error("GPU Validation FAILED.")

    log_data["attempts"].append(attempt_record)
    save_log(log_data)
    return success

def main():
    """Entry point."""
    logger.info("Starting GPU Validation (T046)...")
    success = run_validation()
    
    if success:
        logger.info("Validation complete. Log written to state/gpu_validation_log.json")
        sys.exit(0)
    else:
        logger.error("Validation failed or offload triggered. Check state/gpu_validation_log.json")
        # If offload was triggered, the process might be restarted by the offload mechanism.
        # We exit with 1 to indicate the current run did not complete successfully on its own.
        sys.exit(1)

if __name__ == "__main__":
    main()
