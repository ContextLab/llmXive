"""
T022: Generate a fresh set of failed trajectories with WIA=0 config (Degraded Cohort).

This script generates a new cohort of 500 failed trajectories specifically for the
Degraded condition (WIA horizon = 0). It does NOT re-process baseline data.

Output: data/raw/degraded_failures.json
"""
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.conditions.degraded import (
    DegradedConfig,
    configure_degraded_environment,
    get_degraded_prompt_template,
    run_degraded_condition_check
)
from src.sim.alfworld_runner import run_episode
from src.sim.validation import validate_trajectory
from src.sim.exclusion_logger import set_exclusion_path, log_excluded_trajectory
from src.config.config import SEED, DATA_PATH, MODEL_ID

# Constants
TARGET_COUNT = 500
OUTPUT_PATH = "data/raw/degraded_failures.json"
EXCLUSION_LOG_PATH = "data/raw/excluded_degraded.log"
MAX_RETRIES_PER_TASK = 10
MAX_TOTAL_RETRIES = 5000  # Safety cap

def generate_degraded_failures(target_count: int = TARGET_COUNT) -> List[Dict[str, Any]]:
    """
    Generate a fresh set of failed trajectories with WIA=0 config.
    
    Args:
        target_count: Number of validated failures to collect.
        
    Returns:
        List of validated failure trajectory dictionaries.
    """
    failures = []
    excluded_trajectories = []
    retry_count = 0
    
    # Initialize exclusion logger for this run
    set_exclusion_path(EXCLUSION_LOG_PATH)
    
    # Configure degraded environment (WIA=0)
    config = DegradedConfig(
        wia_horizon=0,
        seed=SEED,
        model_id=MODEL_ID,
        data_path=DATA_PATH
    )
    
    # Configure the environment for degraded condition
    env_config = configure_degraded_environment(config)
    
    task_id_counter = 0
    
    while len(failures) < target_count and retry_count < MAX_TOTAL_RETRIES:
        task_id_counter += 1
        retry_count += 1
        
        # Generate a unique task ID for this attempt
        attempt_id = f"degraded_{task_id_counter}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Run episode with degraded configuration
            # Note: run_episode is expected to handle the WIA=0 logic internally
            # or be configured via env_config
            trajectory_data = run_episode(
                task_id=attempt_id,
                seed=SEED,
                config=config,
                env_config=env_config
            )
            
            if trajectory_data is None:
                # Episode failed to run (timeout, error, etc.)
                log_excluded_trajectory({
                    "id": attempt_id,
                    "reason": "episode_execution_failed",
                    "timestamp": datetime.now().isoformat(),
                    "details": "Episode failed to execute"
                })
                continue
            
            action_log = trajectory_data.get("action_log", [])
            state_transitions = trajectory_data.get("state_transitions", [])
            
            if not action_log or not state_transitions:
                log_excluded_trajectory({
                    "id": attempt_id,
                    "reason": "empty_trajectory",
                    "timestamp": datetime.now().isoformat(),
                    "details": "Trajectory has no actions or state transitions"
                })
                continue
            
            # Validate against ground truth
            is_valid, validation_details = validate_trajectory(action_log, state_transitions)
            
            if not is_valid:
                # This is a failure trajectory - record it
                failure_record = {
                    "id": attempt_id,
                    "condition": "degraded",
                    "wia_horizon": 0,
                    "timestamp": datetime.now().isoformat(),
                    "action_log": action_log,
                    "state_transitions": state_transitions,
                    "validation_details": validation_details,
                    "failure_reason": validation_details.get("failure_reason", "unknown"),
                    "metadata": {
                        "config": {
                            "wia_horizon": config.wia_horizon,
                            "seed": config.seed
                        }
                    }
                }
                
                failures.append(failure_record)
                print(f"✓ Collected failure #{len(failures)}/{target_count} (ID: {attempt_id})")
                
            else:
                # Trajectory succeeded - we wanted failures, so discard
                log_excluded_trajectory({
                    "id": attempt_id,
                    "reason": "trajectory_succeeded",
                    "timestamp": datetime.now().isoformat(),
                    "details": "Trajectory did not fail (we need failures)"
                })
                
        except Exception as e:
            # Log the error and continue
            log_excluded_trajectory({
                "id": attempt_id,
                "reason": "exception_during_generation",
                "timestamp": datetime.now().isoformat(),
                "details": str(e),
                "error_type": type(e).__name__
            })
            continue
    
    return failures

def save_degraded_failures(failures: List[Dict[str, Any]], output_path: str = OUTPUT_PATH) -> None:
    """
    Save the generated degraded failures to a JSON file.
    
    Args:
        failures: List of failure trajectory dictionaries.
        output_path: Path to save the JSON file.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create output structure with metadata
    output_data = {
        "metadata": {
            "condition": "degraded",
            "wia_horizon": 0,
            "total_count": len(failures),
            "generated_at": datetime.now().isoformat(),
            "seed": SEED
        },
        "failures": failures
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(failures)} degraded failures to {output_path}")

def run() -> None:
    """
    Main entry point for generating degraded failures.
    """
    print("=" * 60)
    print("T022: Generating Degraded Cohort (WIA=0)")
    print("=" * 60)
    print(f"Target: {TARGET_COUNT} validated failures")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Seed: {SEED}")
    print("-" * 60)
    
    if not os.path.exists(DATA_PATH):
        print(f"ERROR: Data path not found: {DATA_PATH}")
        sys.exit(1)
    
    try:
        failures = generate_degraded_failures(TARGET_COUNT)
        
        if len(failures) < TARGET_COUNT:
            print(f"⚠ WARNING: Only collected {len(failures)}/{TARGET_COUNT} failures")
            print("  This may indicate issues with the degraded condition configuration.")
        
        save_degraded_failures(failures)
        
        print("-" * 60)
        print(f"✓ T022 COMPLETE: Generated {len(failures)} degraded failures")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run()
