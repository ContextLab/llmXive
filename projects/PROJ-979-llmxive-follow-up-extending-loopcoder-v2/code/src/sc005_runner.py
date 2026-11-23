"""
SC-005 Full GPU Analysis Runner.

Executes the full inference and entropy pipeline on the GPU,
capturing resource metrics and saving them to data/processed/sc005_metrics.json.

This script assumes:
1. The model is available at CODELLAMA_GPU_PATH (or defaults to a valid public ID).
2. The filtered dataset exists at data/processed/filtered_splits.json.
3. GPU hardware is available (torch.cuda.is_available()).
"""
import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import torch
import psutil

# Project imports (matching API surface)
from src.utils import capture_metrics, save_resource_metrics
from src.entropy import extract_entropy, load_model as load_entropy_model
from src.inference import run_iterative_inference, load_model as load_inference_model, load_input_problems

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_PATH = Path("data/processed/sc005_metrics.json")
ENTROPY_OUTPUT = Path("data/processed/entropy_results.csv")
CONVERGENCE_OUTPUT = Path("data/processed/convergence_results.csv")
FILTERED_SPLIT_PATH = Path("data/processed/filtered_splits.json")

# Model Path Configuration
# Default to a public ID if env var is missing, but prioritize env var
DEFAULT_GPU_MODEL = "codellama/CodeLlama-7b-Instruct-hf"
MODEL_PATH = os.getenv("CODELLAMA_GPU_PATH", DEFAULT_GPU_MODEL)

def ensure_output_dirs():
    """Ensure the output directory exists."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENTROPY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def run_full_gpu_analysis():
    """
    Executes the full pipeline on GPU and returns metrics.

    Steps:
    1. Verify GPU availability.
    2. Load Model.
    3. Load Data.
    4. Run Entropy Extraction (T012a-d).
    5. Run Convergence Inference (T013a-d).
    6. Capture Resource Metrics (T005e).
    7. Compile and Save SC-005 Metrics.
    """
    start_time = time.time()
    metrics: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_PATH,
        "gpu_available": False,
        "status": "running",
        "error": None,
        "details": {}
    }

    # 1. Verify GPU
    if not torch.cuda.is_available():
        metrics["status"] = "failed"
        metrics["error"] = "No GPU available. SC-005 requires GPU execution."
        logger.error(metrics["error"])
        return metrics

    gpu_name = torch.cuda.get_device_name(0)
    metrics["gpu_name"] = gpu_name
    metrics["gpu_available"] = True
    logger.info(f"GPU Detected: {gpu_name}")

    # 2. Load Model
    logger.info(f"Loading model: {MODEL_PATH} on CUDA")
    try:
        # We use the shared load_model from inference/entropy context
        # Assuming they handle device placement internally or we pass it
        # Since the API surface shows `load_model` in both, we need to be careful.
        # We will assume the inference one is the primary for the loop.
        model = load_inference_model(MODEL_PATH, device="cuda")
        metrics["model_loaded"] = True
    except Exception as e:
        metrics["status"] = "failed"
        metrics["error"] = f"Failed to load model: {str(e)}"
        logger.error(f"Model load failed: {e}")
        traceback.print_exc()
        return metrics

    # 3. Load Data
    if not FILTERED_SPLIT_PATH.exists():
        metrics["status"] = "failed"
        metrics["error"] = f"Filtered splits not found at {FILTERED_SPLIT_PATH}. Run T004f first."
        logger.error(metrics["error"])
        return metrics

    try:
        with open(FILTERED_SPLIT_PATH, 'r') as f:
            data = json.load(f)
        # Expecting 'test' or 'train' key, usually 'test' for evaluation
        problems = data.get("test", data.get("train", []))
        if not problems:
            metrics["status"] = "failed"
            metrics["error"] = "No problems found in filtered splits."
            return metrics
        logger.info(f"Loaded {len(problems)} problems.")
    except Exception as e:
        metrics["status"] = "failed"
        metrics["error"] = f"Failed to load data: {str(e)}"
        return metrics

    # 4. Run Entropy Extraction (T012a-d)
    # Note: T012a-d are the functions in entropy.py. We call extract_entropy for each.
    # Since running full entropy on full dataset might be heavy, we iterate.
    # The task asks to "Execute full dataset". We assume the dataset fits in the time budget
    # or we process it in a batch. For SC-005, we measure the resource usage of this.
    logger.info("Starting Entropy Extraction...")
    entropy_results = []
    try:
        for i, problem in enumerate(problems):
            # Extract entropy for this problem
            # extract_entropy expects (prompt, model, n_samples)
            # We use the model loaded above
            entropy_val = extract_entropy(
                prompt=problem['prompt'],
                model=model,
                n_samples=10
            )
            entropy_results.append({
                "task_id": problem['task_id'],
                "entropy": entropy_val
            })
            
            # Progress log
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1}/{len(problems)} entropy samples.")

        # Save entropy results to CSV (as required by downstream consumers)
        import csv
        with open(ENTROPY_OUTPUT, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "entropy"])
            writer.writeheader()
            writer.writerows(entropy_results)
        metrics["entropy_file_written"] = str(ENTROPY_OUTPUT)
        metrics["entropy_count"] = len(entropy_results)
    except Exception as e:
        metrics["status"] = "failed"
        metrics["error"] = f"Entropy extraction failed: {str(e)}"
        logger.error(f"Entropy extraction failed: {e}")
        traceback.print_exc()
        return metrics

    # 5. Run Convergence Inference (T013a-d)
    logger.info("Starting Convergence Inference...")
    convergence_results = []
    try:
        for i, problem in enumerate(problems):
            # Run iterative inference
            # run_iterative_inference returns a list of trajectories or a dict
            # Based on API: run_iterative_inference(prompt, model, k)
            # We run for k=1, 2, 3 as per T013a
            trajectory = run_iterative_inference(
                prompt=problem['prompt'],
                model=model,
                k=3
            )
            # trajectory is likely a list of dicts or a dict of lists
            # We normalize to the expected CSV schema: task_id, k, converged, step
            if isinstance(trajectory, list):
                for t in trajectory:
                    convergence_results.append({
                        "task_id": problem['task_id'],
                        "k": t.get('k'),
                        "converged": t.get('converged', False),
                        "step": t.get('first_correct_step'),
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                # Handle single dict case if API varies
                convergence_results.append({
                    "task_id": problem['task_id'],
                    "k": trajectory.get('k'),
                    "converged": trajectory.get('converged', False),
                    "step": trajectory.get('first_correct_step'),
                    "timestamp": datetime.now().isoformat()
                })

            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1}/{len(problems)} convergence samples.")

        # Save convergence results
        import csv
        with open(CONVERGENCE_OUTPUT, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "k", "converged", "step", "timestamp"])
            writer.writeheader()
            writer.writerows(convergence_results)
        metrics["convergence_file_written"] = str(CONVERGENCE_OUTPUT)
        metrics["convergence_count"] = len(convergence_results)
    except Exception as e:
        metrics["status"] = "failed"
        metrics["error"] = f"Convergence inference failed: {str(e)}"
        logger.error(f"Convergence inference failed: {e}")
        traceback.print_exc()
        return metrics

    # 6. Capture Resource Metrics (T005e)
    logger.info("Capturing resource metrics...")
    try:
        # Capture metrics at the end of the run
        resource_metrics = capture_metrics()
        # Ensure runtime is calculated
        end_time = time.time()
        resource_metrics['runtime_s'] = end_time - start_time
        
        # Save to the standard location
        save_resource_metrics(resource_metrics)
        metrics["resource_metrics"] = resource_metrics
    except Exception as e:
        logger.warning(f"Failed to capture detailed metrics: {e}")
        # Fallback: record basic runtime
        metrics["resource_metrics"] = {
            "runtime_s": time.time() - start_time,
            "ram_gb": psutil.virtual_memory().used / (1024**3),
            "gpu_util_pct": torch.cuda.utilization(),
            "gpu_memory_gb": torch.cuda.memory_allocated(0) / (1024**3)
        }

    # 7. Compile and Save SC-005 Metrics
    metrics["status"] = "completed"
    metrics["runtime_s"] = time.time() - start_time
    metrics["total_problems"] = len(problems)
    
    # Save final SC-005 metrics
    try:
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        logger.info(f"SC-005 metrics saved to {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to save SC-005 metrics: {e}")
        # Still return metrics even if file save fails
    
    return metrics

def main():
    ensure_output_dirs()
    logger.info("Starting SC-005 Full GPU Analysis...")
    metrics = run_full_gpu_analysis()
    
    # Exit with error code if status is failed
    if metrics.get("status") != "completed":
        logger.error(f"Analysis failed: {metrics.get('error')}")
        sys.exit(1)
    else:
        logger.info("Analysis completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()