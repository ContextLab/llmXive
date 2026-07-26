"""
Dependency Check Module for CPU-Only Execution Verification.

This module performs a dry-run inference on Base and RL-Unified models
to ensure they can load and execute on CPU without triggering CUDA kernels.
"""

import sys
import torch
from pathlib import Path
from typing import Dict, Any, Optional

from config import PROJECT_ROOT
from utils.logger import get_logger
from inference.inference import load_model, generate_image

logger = get_logger(__name__)

# Model identifiers as defined in config/download logic
MODEL_IDS = {
    "base": "Qwen/Qwen-Image-2.0",
    "rl_unified": "Qwen/Qwen-Image-2.0-RL"
}

def check_cpu_compatibility() -> Dict[str, Any]:
    """
    Performs a dry-run inference on Base and RL-Unified models using CPU-only execution.
    
    This function attempts to load the models with `device_map="cpu"` and `torch_dtype=torch.float16`.
    It then attempts a single generation step (dry-run) to verify no CUDA kernels are triggered.
    
    Returns:
        Dict[str, Any]: A dictionary containing the status of the check and any error messages.
        
    Raises:
        SystemExit: If the dry-run triggers CUDA kernels or fails to load on CPU.
    """
    results = {
        "status": "success",
        "models_checked": [],
        "errors": []
    }

    logger.info("Starting CPU compatibility dry-run check...")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    # Check CUDA availability to ensure we are not on a GPU environment by accident
    if torch.cuda.is_available():
        logger.warning("CUDA is available. Enforcing CPU-only execution for this check.")
    
    for model_key, model_id in MODEL_IDS.items():
        logger.info(f"Checking model: {model_key} ({model_id})")
        try:
            # Attempt to load the model with CPU constraints
            # We use float16 as per the project's inference strategy, but force CPU
            pipe = load_model(
                model_id=model_id,
                device_map="cpu",
                torch_dtype=torch.float16
            )
            
            logger.info(f"Model {model_key} loaded successfully on CPU.")

            # Perform a minimal dry-run generation
            # We use a very short prompt and minimal steps to speed up the check
            dry_run_prompt = "a simple test image"
            dry_run_steps = 1
            
            logger.info(f"Performing dry-run generation for {model_key}...")
            
            # Generate image with CPU constraint
            # Note: load_model returns the pipeline, we call generate_image on it
            # We wrap in try-except to catch any CUDA allocation errors
            try:
                _ = generate_image(
                    pipe=pipe,
                    prompt=dry_run_prompt,
                    num_inference_steps=dry_run_steps,
                    height=64,  # Minimal size for speed
                    width=64,
                    device="cpu",
                    seed=42
                )
                logger.info(f"Dry-run generation for {model_key} completed successfully on CPU.")
                results["models_checked"].append(model_key)
            except RuntimeError as e:
                if "CUDA" in str(e) or "cuda" in str(e):
                    error_msg = f"[CRITICAL] CUDA kernel triggered during dry-run for {model_key}: {str(e)}"
                    logger.critical(error_msg)
                    results["status"] = "failed"
                    results["errors"].append(error_msg)
                    raise SystemExit(1)
                else:
                    # Re-raise if it's a different runtime error
                    raise

        except SystemExit:
            # Re-raise if we already triggered an exit
            raise
        except Exception as e:
            error_msg = f"[CRITICAL] Failed to load or run dry-run for {model_key}: {str(e)}"
            logger.critical(error_msg)
            results["status"] = "failed"
            results["errors"].append(error_msg)
            # Abort immediately as per requirements
            raise SystemExit(1)

    if results["status"] == "success":
        logger.info("CPU compatibility check PASSED for all models.")
        print(json.dumps(results, indent=2))
        return results
    else:
        logger.error("CPU compatibility check FAILED.")
        print(json.dumps(results, indent=2))
        raise SystemExit(1)

def main():
    """Entry point for the dependency check script."""
    import json
    try:
        check_cpu_compatibility()
        logger.info("Dependency check completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Dependency check failed with exit code {e.code}")
            sys.exit(e.code)
        sys.exit(0)

if __name__ == "__main__":
    main()