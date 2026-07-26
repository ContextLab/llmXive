"""
run_inference.py - Execute the full inference pipeline with comprehensive logging.

This script runs inference for all profiles x tasks x conditions.
It implements structured logging for start, progress, completion, and failures.
"""
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project API surface
from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug, log_event
from data_generation.profiles import load_profiles
from data_generation.tasks import load_tasks
from inference.prompts import build_prompt
from inference.engine import InferenceEngine, InferenceTimeoutError, InferenceOOMError, ModelLoadError

# Constants
CONDITIONS = ["Monolithic", "Separated", "Generic"]
OUTPUT_FILE = "data/interim/inference_outputs.jsonl"

def log_run_start(profile_count: int, task_count: int, conditions: List[str]):
    """Log the start of the inference run."""
    total_runs = profile_count * task_count * len(conditions)
    log_event(
        event_type="INFERENCE_START",
        message=f"Starting inference pipeline: {profile_count} profiles x {task_count} tasks x {len(conditions)} conditions = {total_runs} total runs.",
        metadata={
            "profile_count": profile_count,
            "task_count": task_count,
            "conditions": conditions,
            "total_runs": total_runs
        }
    )
    log_info("Inference pipeline initialized.")

def log_progress(current: int, total: int, profile_id: str, task_id: str, condition: str, elapsed: float):
    """Log progress of a single inference step."""
    percent = (current / total) * 100
    log_event(
        event_type="INFERENCE_PROGRESS",
        message=f"Progress: {percent:.1f}% ({current}/{total}) - {profile_id} / {task_id} / {condition}",
        metadata={
            "current": current,
            "total": total,
            "percent": round(percent, 2),
            "profile_id": profile_id,
            "task_id": task_id,
            "condition": condition,
            "elapsed_seconds": round(elapsed, 2)
        }
    )
    # Log every 10% or at specific milestones to avoid spam
    if percent % 10 < 1.0:
        log_info(f"Reached {percent:.0f}% completion.")

def log_completion(output_file: str, total_runs: int, success_count: int, failure_count: int):
    """Log the successful completion of the pipeline."""
    log_event(
        event_type="INFERENCE_COMPLETE",
        message=f"Inference pipeline completed successfully.",
        metadata={
            "output_file": str(output_file),
            "total_runs": total_runs,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_count / total_runs * 100, 2) if total_runs > 0 else 0
        }
    )
    log_info(f"Pipeline finished. Success: {success_count}, Failures: {failure_count}. Output: {output_file}")

def log_failure(profile_id: str, task_id: str, condition: str, error_type: str, error_msg: str):
    """Log a specific failure for a run."""
    log_event(
        event_type="INFERENCE_FAILURE",
        message=f"Failed to run inference for {profile_id}/{task_id}/{condition}: {error_type}",
        level="ERROR",
        metadata={
            "profile_id": profile_id,
            "task_id": task_id,
            "condition": condition,
            "error_type": error_type,
            "error_message": error_msg
        }
    )
    log_error(f"Run failed: {profile_id} / {task_id} / {condition} -> {error_type}: {error_msg}")

def build_prompt_template(profile: Dict[str, Any], task: Dict[str, Any], condition: str) -> str:
    """Build the prompt string based on the condition."""
    return build_prompt(profile, task, condition)

def run_inference_batch(
    profiles: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    engine: InferenceEngine,
    output_file: Path
) -> Dict[str, int]:
    """
    Run inference for all combinations and write to output file.
    Returns a dict with success and failure counts.
    """
    total_runs = len(profiles) * len(tasks) * len(CONDITIONS)
    current_run = 0
    success_count = 0
    failure_count = 0

    log_run_start(len(profiles), len(tasks), CONDITIONS)

    start_time = time.time()

    # Open file for appending (or creating)
    with open(output_file, 'w') as f:
        for profile in profiles:
            for task in tasks:
                for condition in CONDITIONS:
                    current_run += 1
                    run_start = time.time()
                    profile_id = profile.get('id', 'unknown')
                    task_id = task.get('id', 'unknown')

                    try:
                        # Build prompt
                        prompt = build_prompt_template(profile, task, condition)

                        # Run inference
                        output_text = engine.generate(prompt, timeout=300)
                        latency = time.time() - run_start

                        # Log progress
                        log_progress(current_run, total_runs, profile_id, task_id, condition, time.time() - start_time)

                        # Record success
                        record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "latency": round(latency, 2),
                            "success_flag": True,
                            "output_text": output_text,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        f.write(json.dumps(record) + '\n')
                        success_count += 1

                    except InferenceTimeoutError as e:
                        log_failure(profile_id, task_id, condition, "TIMEOUT", str(e))
                        record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "latency": round(time.time() - run_start, 2),
                            "success_flag": False,
                            "output_text": None,
                            "error": "timeout",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        f.write(json.dumps(record) + '\n')
                        failure_count += 1

                    except InferenceOOMError as e:
                        log_failure(profile_id, task_id, condition, "OOM", str(e))
                        record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "latency": round(time.time() - run_start, 2),
                            "success_flag": False,
                            "output_text": None,
                            "error": "oom",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        f.write(json.dumps(record) + '\n')
                        failure_count += 1

                    except ModelLoadError as e:
                        log_failure(profile_id, task_id, condition, "MODEL_LOAD", str(e))
                        record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "latency": 0,
                            "success_flag": False,
                            "output_text": None,
                            "error": "model_load",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        f.write(json.dumps(record) + '\n')
                        failure_count += 1

                    except Exception as e:
                        # Catch-all for unexpected errors
                        log_failure(profile_id, task_id, condition, "UNEXPECTED", str(e))
                        record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "latency": round(time.time() - run_start, 2),
                            "success_flag": False,
                            "output_text": None,
                            "error": "unexpected",
                            "error_details": str(e),
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        f.write(json.dumps(record) + '\n')
                        failure_count += 1

    total_elapsed = time.time() - start_time
    log_completion(output_file, total_runs, success_count, failure_count)
    log_info(f"Total time elapsed: {total_elapsed:.2f} seconds")

    return {"success": success_count, "failure": failure_count}

def main():
    """Main entry point for the inference script."""
    logger = get_logger("run_inference")
    logger.info("Starting run_inference script.")

    # Set seed for reproducibility
    set_global_seed(42)

    project_root = get_project_root()
    data_dir = get_data_dir()

    # Ensure output directory exists
    output_path = project_root / OUTPUT_FILE
    ensure_dir(output_path.parent)

    # Load data
    profiles_path = data_dir / "raw" / "profiles.json"
    tasks_path = data_dir / "raw" / "tasks.json"

    if not profiles_path.exists():
        log_error(f"Profiles file not found: {profiles_path}")
        sys.exit(1)

    if not tasks_path.exists():
        log_error(f"Tasks file not found: {tasks_path}")
        sys.exit(1)

    profiles = load_profiles(profiles_path)
    tasks = load_tasks(tasks_path)

    if not profiles:
        log_error("No valid profiles loaded.")
        sys.exit(1)

    if not tasks:
        log_error("No valid tasks loaded.")
        sys.exit(1)

    log_info(f"Loaded {len(profiles)} profiles and {len(tasks)} tasks.")

    # Initialize engine
    # Note: In a real run, model path and params would be args.
    # For now, we assume the engine is configured or we use a default.
    # The engine implementation handles the actual loading.
    try:
        engine = InferenceEngine()
        # If specific model args are needed, they should be passed here or via config
        # e.g., engine = InferenceEngine(model_path="...", device="cpu")
    except Exception as e:
        log_error(f"Failed to initialize inference engine: {e}")
        sys.exit(1)

    # Run inference
    try:
        results = run_inference_batch(profiles, tasks, engine, output_path)
        log_info(f"Inference batch completed. Results: {results}")
    except Exception as e:
        log_error(f"Fatal error during inference batch: {e}")
        sys.exit(1)

    logger.info("run_inference script finished.")

if __name__ == "__main__":
    main()