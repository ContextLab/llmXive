"""
Run Inference Script for llmXive Project (T015)

This script segments the workload into parallel jobs (Monolithic, Separated, Generic),
iterates over profiles and tasks, runs inference using the engine, and logs detailed
status updates (start, progress, completion, failures) to the project logger and console.

Outputs:
    data/interim/inference_outputs.jsonl: Records of inference results with metadata.
"""
import json
import time
import sys
import random
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project imports based on API surface
from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug, log_event
from data_generation.profiles import load_profiles
from data_generation.tasks import load_tasks
from inference.prompts import build_prompt, get_monolithic_prompt, get_separated_tracks_prompt, get_generic_baseline_prompt
from inference.engine import InferenceEngine, InferenceTimeoutError, InferenceOOMError, ModelLoadError

# Constants
CONDITIONS = ["monolithic", "separated", "generic"]
OUTPUT_FILENAME = "inference_outputs.jsonl"

# Logger setup
logger = get_logger("run_inference")

def log_run_start(profile_count: int, task_count: int):
    """Log the start of the inference run."""
    total_runs = profile_count * task_count * len(CONDITIONS)
    log_event(
        event_type="INFERENCE_RUN_START",
        message=f"Starting inference run for {profile_count} profiles, {task_count} tasks, {len(CONDITIONS)} conditions.",
        details={
            "profile_count": profile_count,
            "task_count": task_count,
            "condition_count": len(CONDITIONS),
            "total_expected_runs": total_runs,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    log_info(f"Inference run started. Total expected runs: {total_runs}")

def log_progress(current: int, total: int, current_profile_id: str, current_task_id: str, condition: str):
    """Log progress of the current inference step."""
    percent = (current / total) * 100
    log_event(
        event_type="INFERENCE_PROGRESS",
        message=f"Processing {current}/{total} ({percent:.1f}%)",
        details={
            "current": current,
            "total": total,
            "profile_id": current_profile_id,
            "task_id": current_task_id,
            "condition": condition,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    # Only print to console every 10% or at milestones to avoid spam
    if int(percent) % 10 == 0 or current == 1 or current == total:
        log_info(f"Progress: {current}/{total} | {condition} | Profile: {current_profile_id} | Task: {current_task_id}")

def log_completion(record: Dict[str, Any]):
    """Log successful completion of a single inference step."""
    log_event(
        event_type="INFERENCE_SUCCESS",
        message=f"Successfully generated response for {record['profile_id']}/{record['task_id']} ({record['condition']})",
        details={
            "profile_id": record["profile_id"],
            "task_id": record["task_id"],
            "condition": record["condition"],
            "latency": record.get("latency", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    log_debug(f"Success: {record['profile_id']} - {record['task_id']} ({record['condition']})")

def log_failure(profile_id: str, task_id: str, condition: str, error: Exception):
    """Log a failure during inference."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    log_event(
        event_type="INFERENCE_FAILURE",
        message=f"Failed to generate response for {profile_id}/{task_id} ({condition}): {error_type}",
        details={
            "profile_id": profile_id,
            "task_id": task_id,
            "condition": condition,
            "error_type": error_type,
            "error_message": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    log_error(f"Failure: {profile_id} - {task_id} ({condition}) -> {error_type}: {error_msg}")

def build_prompt_template(profile: Dict[str, Any], task: Dict[str, Any], condition: str) -> str:
    """Build the prompt string based on the condition."""
    # Unpack profile and task details
    domain = profile.get("domain", "general")
    behavior_keywords = profile.get("behavior_keywords", [])
    capability_rules = profile.get("capability_rules", "")
    task_text = task.get("text", "")
    
    if condition == "monolithic":
        return get_monolithic_prompt(domain, behavior_keywords, task_text)
    elif condition == "separated":
        return get_separated_tracks_prompt(capability_rules, behavior_keywords, task_text)
    elif condition == "generic":
        return get_generic_baseline_prompt(task_text)
    else:
        raise ValueError(f"Unknown condition: {condition}")

def run_inference_batch(
    engine: InferenceEngine,
    profiles: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    output_path: Path
):
    """
    Run inference for all profiles, tasks, and conditions.
    Logs start, progress, completion, and failures.
    """
    total_runs = len(profiles) * len(tasks) * len(CONDITIONS)
    current_run = 0

    # Ensure output directory exists
    ensure_dir(output_path.parent)

    # Open file for appending results
    with open(output_path, 'a', encoding='utf-8') as f_out:
        for profile in profiles:
            for task in tasks:
                for condition in CONDITIONS:
                    current_run += 1
                    profile_id = profile.get("id")
                    task_id = task.get("id")

                    # Log Progress
                    log_progress(current_run, total_runs, profile_id, task_id, condition)

                    try:
                        # Build Prompt
                        prompt_text = build_prompt_template(profile, task, condition)
                        
                        # Run Inference
                        start_time = time.time()
                        response_text = engine.generate(prompt_text)
                        end_time = time.time()
                        latency = end_time - start_time

                        # Construct Record
                        record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "prompt": prompt_text,
                            "response": response_text,
                            "latency": latency,
                            "success_flag": True,
                            "timestamp": datetime.utcnow().isoformat()
                        }

                        # Write to disk
                        f_out.write(json.dumps(record) + '\n')
                        f_out.flush()

                        # Log Success
                        log_completion(record)

                    except (InferenceTimeoutError, InferenceOOMError, ModelLoadError) as e:
                        log_failure(profile_id, task_id, condition, e)
                        # Write failure record to ensure data integrity
                        failure_record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "prompt": None, # Do not log prompt on failure to save space if needed, or keep for debugging
                            "response": None,
                            "latency": 0,
                            "success_flag": False,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        f_out.write(json.dumps(failure_record) + '\n')
                        f_out.flush()
                    except Exception as e:
                        # Catch-all for unexpected errors
                        log_failure(profile_id, task_id, condition, e)
                        failure_record = {
                            "profile_id": profile_id,
                            "task_id": task_id,
                            "condition": condition,
                            "prompt": None,
                            "response": None,
                            "latency": 0,
                            "success_flag": False,
                            "error": f"UnexpectedError: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        f_out.write(json.dumps(failure_record) + '\n')
                        f_out.flush()

    log_info(f"Inference batch complete. Results saved to {output_path}")

def main():
    """Main entry point for the inference script."""
    set_global_seed(42)
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    # Define paths
    profiles_path = data_dir / "profiles.json"
    tasks_path = data_dir / "tasks.json"
    output_path = data_dir / "interim" / OUTPUT_FILENAME

    log_run_start(0, 0) # Placeholder counts, updated after loading

    # Load Data
    if not profiles_path.exists():
        log_error(f"Profiles file not found: {profiles_path}")
        sys.exit(1)
    if not tasks_path.exists():
        log_error(f"Tasks file not found: {tasks_path}")
        sys.exit(1)

    profiles = load_profiles(profiles_path)
    tasks = load_tasks(tasks_path)
    
    # Update start log with actual counts
    logger.handlers.clear() # Reset to ensure clean state if reused
    # Re-attach handlers if needed, but get_logger usually handles singleton
    # We just log the corrected start
    total_expected = len(profiles) * len(tasks) * len(CONDITIONS)
    log_info(f"Loaded {len(profiles)} profiles and {len(tasks)} tasks. Total runs: {total_expected}")

    # Initialize Engine
    # Assuming default model config or env vars as per T009
    try:
        engine = InferenceEngine(model_name="Llama-8B-Q4", device="cpu")
        log_info("Inference engine initialized successfully.")
    except Exception as e:
        log_error(f"Failed to initialize inference engine: {e}")
        sys.exit(1)

    # Run Batch
    run_inference_batch(engine, profiles, tasks, output_path)

    log_event(
        event_type="INFERENCE_RUN_COMPLETE",
        message="All inference jobs completed.",
        details={"timestamp": datetime.utcnow().isoformat()}
    )

if __name__ == "__main__":
    main()