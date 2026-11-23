import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing APIs from project structure
from src.conditions.degraded import (
    DegradedConfig,
    configure_degraded_environment,
    run_degraded_condition_check
)
from src.sim.alfworld_runner import run_episode
from src.config.config import DATA_PATH, SEED
from src.sim.exclusion_logger import log_excluded_trajectory, set_exclusion_path

# Constants for batch processing
BATCH_SIZE = 50
MAX_BATCHES = 10
MAX_TOTAL_ATTEMPTS = MAX_BATCHES * BATCH_SIZE

def load_baseline_failures(input_path: str) -> List[Dict[str, Any]]:
    """
    Load baseline failure trajectories from the specified JSON file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Baseline failures file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of trajectories in {input_path}, got {type(data)}")
    
    return data

def run_degraded_simulation(
    baseline_failures: List[Dict[str, Any]],
    output_path: str,
    batch_size: int = BATCH_SIZE,
    max_batches: int = MAX_BATCHES
) -> List[Dict[str, Any]]:
    """
    Execute the re-simulation loop with batch limits on baseline failures.
    Re-runs ALFWorld episodes with WIA prediction horizon = 0.
    Saves results to the specified output path.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Set exclusion log path
    set_exclusion_path(os.path.join(DATA_PATH, "raw", "excluded_log.json"))
    
    degraded_config = DegradedConfig(wia_horizon=0)
    results = []
    total_attempts = 0
    batch_count = 0
    
    # Process in batches
    for batch_start in range(0, len(baseline_failures), batch_size):
        if batch_count >= max_batches:
            print(f"Reached MAX_BATCHES limit ({max_batches}). Stopping simulation.")
            break
        
        batch_end = min(batch_start + batch_size, len(baseline_failures))
        batch = baseline_failures[batch_start:batch_end]
        batch_count += 1
        
        print(f"Processing batch {batch_count}/{max_batches} (size: {len(batch)})")
        
        for idx, failure in enumerate(batch):
            if total_attempts >= MAX_TOTAL_ATTEMPTS:
                print(f"Reached MAX_TOTAL_ATTEMPTS limit ({MAX_TOTAL_ATTEMPTS}). Stopping.")
                break
            
            total_attempts += 1
            trajectory_id = failure.get('id', str(uuid.uuid4()))
            task_id = failure.get('task_id')
            
            if not task_id:
                log_excluded_trajectory(
                    trajectory_id=trajectory_id,
                    reason="missing_task_id",
                    details="Baseline failure entry missing task_id field"
                )
                continue
            
            try:
                # Configure degraded environment
                configure_degraded_environment(degraded_config)
                
                # Run the episode with the specific task and seed
                # We use the seed from the original failure if available, otherwise default
                seed = failure.get('seed', SEED)
                
                action_log, state_transitions = run_episode(task_id, seed)
                
                # Validate the trajectory against ground truth
                is_valid, reason = run_degraded_condition_check(
                    action_log, 
                    state_transitions,
                    failure
                )
                
                if not is_valid:
                    log_excluded_trajectory(
                        trajectory_id=trajectory_id,
                        reason="validation_failed",
                        details=reason
                    )
                    continue
                
                # Construct the result entry
                result_entry = {
                    "id": trajectory_id,
                    "task_id": task_id,
                    "condition": "degraded",
                    "seed": seed,
                    "timestamp": datetime.utcnow().isoformat(),
                    "action_log": action_log,
                    "state_transitions": state_transitions,
                    "original_failure_id": failure.get('id'),
                    "validation_status": "PASS"
                }
                
                results.append(result_entry)
                
            except Exception as e:
                log_excluded_trajectory(
                    trajectory_id=trajectory_id,
                    reason="simulation_error",
                    details=str(e)
                )
                continue
        
        if total_attempts >= MAX_TOTAL_ATTEMPTS:
            break
    
    print(f"Simulation complete. Processed {total_attempts} attempts, saved {len(results)} valid trajectories.")
    return results

def run(input_path: str, output_path: str) -> None:
    """
    Main entry point to run the degraded condition simulation.
    Loads baseline failures, runs simulation, and saves results.
    """
    print(f"Loading baseline failures from: {input_path}")
    baseline_failures = load_baseline_failures(input_path)
    print(f"Loaded {len(baseline_failures)} baseline failures.")
    
    if not baseline_failures:
        raise ValueError("No baseline failures found to process.")
    
    print(f"Starting degraded simulation. Output: {output_path}")
    results = run_degraded_simulation(baseline_failures, output_path)
    
    # Save results to disk
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Successfully saved {len(results)} degraded failures to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Degraded Condition Simulation")
    parser.add_argument(
        "--input", 
        type=str, 
        required=True,
        help="Path to baseline failures JSON file (e.g., data/raw/baseline_failures.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save degraded failures JSON file (e.g., data/raw/degraded_failures.json)"
    )
    
    args = parser.parse_args()
    run(args.input, args.output)

if __name__ == "__main__":
    main()