import json
import logging
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_state_mismatch(step_index: int, context: Optional[str] = None) -> str:
    """
    Generates a semantic contradiction string for injection.
    
    Args:
        step_index: The step index where the error is injected.
        context: Optional context string (not used in this simple version but kept for API consistency).
    
    Returns:
        A string representing a state mismatch error.
    """
    return f"ERROR: State mismatch detected at step {step_index}"

def inject_errors_into_trajectory(trajectory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Injects a semantic contradiction into the last observation of a trajectory.
    
    The error is appended to the last observation string, which represents the
    state immediately before the final success/failure decision.
    
    Args:
        trajectory: A dictionary representing a single trajectory with 'observations' key.
    
    Returns:
        The modified trajectory with the injected error.
    
    Raises:
        ValueError: If 'observations' is missing or empty.
    """
    if "observations" not in trajectory:
        raise ValueError("Trajectory missing 'observations' field")
    
    observations = trajectory["observations"]
    if not observations or not isinstance(observations, list) or len(observations) == 0:
        raise ValueError("Trajectory 'observations' must be a non-empty list")
    
    # Identify the last observation index
    last_obs_index = len(observations) - 1
    
    # Generate the error string
    error_msg = generate_state_mismatch(last_obs_index)
    
    # Append the error to the last observation
    # We assume observations are strings. If they are dicts/objects, we might need to adjust.
    # Based on the schema and typical trajectory logs, they are strings.
    original_obs = observations[last_obs_index]
    if not isinstance(original_obs, str):
        original_obs = str(original_obs)
    
    # Inject the error
    injected_obs = f"{original_obs} | {error_msg}"
    
    # Update the trajectory
    modified_trajectory = trajectory.copy()
    modified_trajectory["observations"] = observations.copy()
    modified_trajectory["observations"][last_obs_index] = injected_obs
    
    # Mark the injected error explicitly for verification
    modified_trajectory["injected_error"] = error_msg
    
    logger.debug(f"Injected error '{error_msg}' at index {last_obs_index}")
    
    return modified_trajectory

def main():
    """
    Main entry point for T013: Error Injection.
    Reads clean baseline execution logs (CSV or JSONL), injects errors,
    and writes the result to data/processed/injected_trajectories.jsonl.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "baseline_execution_logs.csv"
    output_file = project_root / "data" / "processed" / "injected_trajectories.jsonl"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T012 has generated data/processed/baseline_execution_logs.csv")
        sys.exit(1)
    
    logger.info(f"Reading clean trajectories from {input_file}")
    
    injected_count = 0
    error_count = 0
    
    try:
        import csv
        with open(input_file, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            
            # Prepare output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f_out:
                for row_idx, row in enumerate(reader):
                    try:
                        # Reconstruct trajectory object from CSV row
                        # We expect the CSV to have columns: task_id, success, trajectory_json (or similar)
                        # If the CSV stores observations as a JSON string in a column, we parse it.
                        # If the CSV has flattened columns, we need to reconstruct.
                        
                        # Assumption based on T012 description: "full trajectory"
                        # If the CSV has a 'trajectory' or 'observations' column as JSON string:
                        if "observations" in row:
                            try:
                                obs_list = json.loads(row["observations"])
                            except json.JSONDecodeError:
                                # Fallback if it's a raw string representation or comma-separated
                                # For robustness, treat as a single-item list if it's a string
                                obs_list = [row["observations"]]
                        else:
                            # If no observations column, try to find a column that looks like trajectory data
                            # Or skip if we can't reconstruct
                            logger.warning(f"Row {row_idx} missing 'observations' column, skipping.")
                            continue
                        
                        # Reconstruct the trajectory dict
                        trajectory = {
                            "task_id": row.get("task_id", f"unknown_{row_idx}"),
                            "observations": obs_list,
                            "success": row.get("success", False) == "True" if "success" in row else None,
                            "actions": json.loads(row.get("actions", "[]")) if "actions" in row else []
                        }
                        
                        # Inject error
                        modified_trajectory = inject_errors_into_trajectory(trajectory)
                        
                        # Write as JSONL
                        f_out.write(json.dumps(modified_trajectory) + "\n")
                        injected_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing row {row_idx}: {e}")
                        error_count += 1
                        continue
    
        logger.info(f"Injection complete. Processed {injected_count} trajectories, {error_count} errors.")
        logger.info(f"Output written to {output_file}")
        
        # Verify output exists and is not empty
        if not output_file.exists() or output_file.stat().st_size == 0:
            logger.error("Output file is missing or empty!")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Fatal error during injection process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
