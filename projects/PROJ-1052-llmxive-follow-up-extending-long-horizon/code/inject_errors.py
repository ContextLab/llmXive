import json
import logging
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any

# Ensure the project root is in the path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_state_mismatch(step_index: int) -> str:
    """
    Generates a semantic contradiction string to be injected.
    Matches the requirement: 'ERROR: State mismatch detected at step X'
    """
    return f"ERROR: State mismatch detected at step {step_index}"

def inject_errors_into_trajectory(trajectory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Injects a semantic contradiction into the last observation of a trajectory.
    
    The task specifies modifying the 'observations' field.
    We assume the trajectory structure contains a list of observations.
    The injection happens at the **last observation** (index -1), 
    which is the point immediately before the final success/failure state.
    
    Args:
        trajectory: A dictionary representing a single trajectory from the dataset.
                    Expected keys: 'observations' (List[str]), 'task_id', etc.
                    
    Returns:
        Modified trajectory dictionary with injected error in the last observation.
    """
    if not trajectory:
        raise ValueError("Trajectory cannot be empty")

    if 'observations' not in trajectory:
        logger.warning(f"Trajectory missing 'observations' key. Task ID: {trajectory.get('task_id', 'unknown')}")
        # If no observations, we cannot inject into the last one. 
        # We return the trajectory as is but log a warning.
        # However, for strict adherence to T013, we might want to ensure we fail loudly 
        # if the data structure is invalid for injection. 
        # For now, we log and return.
        return trajectory

    observations = trajectory['observations']
    
    if not observations:
        logger.warning(f"Observations list is empty. Task ID: {trajectory.get('task_id', 'unknown')}")
        return trajectory

    # Identify the last observation index
    last_obs_index = len(observations) - 1
    original_last_obs = observations[last_obs_index]
    
    # Generate the error string
    error_string = generate_state_mismatch(last_obs_index)
    
    # Append the error to the existing observation
    # The requirement says "Append a semantic contradiction string"
    # We append to the end of the text to maintain context while adding the error signal.
    new_observation = f"{original_last_obs}\n\n{error_string}"
    
    # Create a copy to avoid mutating the original source if it's shared, 
    # though in a stream we often just build the new object.
    modified_trajectory = trajectory.copy()
    modified_observations = observations.copy()
    modified_observations[last_obs_index] = new_observation
    modified_trajectory['observations'] = modified_observations
    
    # Log the injection for traceability
    logger.info(f"Injected error into Task ID {trajectory.get('task_id', 'unknown')} at observation index {last_obs_index}")
    
    return modified_trajectory

def main():
    """
    Main entry point for T013.
    Reads clean trajectories from data/processed/baseline_execution_logs.csv (T012 output),
    injects errors, and writes to data/processed/injected_trajectories.jsonl.
    """
    input_path = Path("data/processed/baseline_execution_logs.csv")
    output_path = Path("data/processed/injected_trajectories.jsonl")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("T012 (baseline execution) must be completed first to generate the input file.")
        sys.exit(1)

    logger.info(f"Starting error injection from {input_path} to {output_path}")
    
    injected_count = 0
    skipped_count = 0
    
    # We need to read the CSV, convert rows to trajectory dicts, inject, and write JSONL.
    # The baseline execution logs from T012 are expected to contain the trajectory data.
    # Assuming the CSV has columns like: task_id, success, trajectory (JSON string), ...
    # Or it might be a flattened list of steps. 
    # Given T012 description: "full trajectory", it likely stores the trajectory as a JSON string or a list of dicts.
    # We will assume the CSV contains a 'trajectory' column that is a JSON string representation of the trajectory.
    
    import csv
    
    # Prepare output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
         
         reader = csv.DictReader(infile)
         
         # Verify required columns exist
         if 'trajectory' not in reader.fieldnames:
             # Fallback: maybe the trajectory is split? Or maybe the whole row IS the trajectory?
             # Based on T012 "full trajectory", it's most likely a JSON string in a column.
             # If not, we try to reconstruct from other columns if they exist (observations, actions).
             # But strict T012 output usually has a 'trajectory' column.
             # Let's assume 'trajectory' is the column name. If not, we look for 'observations'.
             if 'observations' in reader.fieldnames:
                 # Reconstruct trajectory dict from CSV columns
                 # This is a heuristic. If the CSV is flat, we might need to group.
                 # However, T012 says "full trajectory", implying a nested structure or JSON string.
                 # We will assume 'trajectory' column exists. If not, we raise error.
                 raise ValueError("Input CSV must contain a 'trajectory' column (JSON string) or 'observations' column to reconstruct.")
             else:
                 raise ValueError(f"Input CSV missing expected 'trajectory' or 'observations' column. Found: {reader.fieldnames}")

         for row_num, row in enumerate(reader):
             try:
                 # Parse the trajectory JSON
                 if 'trajectory' in row:
                     trajectory = json.loads(row['trajectory'])
                 elif 'observations' in row:
                     # Fallback: reconstruct minimal trajectory dict
                     # This handles cases where T012 output might be flattened differently
                     obs_list_str = row['observations']
                     # If it's a JSON string
                     if obs_list_str.startswith('['):
                         obs_list = json.loads(obs_list_str)
                     else:
                         # Maybe it's a pipe-separated list? Or just a single string?
                         # T012 "full trajectory" implies structure. 
                         # We assume it's a JSON list of strings or dicts.
                         # If it's a single string, we wrap it.
                         obs_list = [obs_list_str]
                     
                     trajectory = {
                         "task_id": row.get('task_id', f"unknown_{row_num}"),
                         "observations": obs_list,
                         "success": row.get('success', False)
                     }
                 else:
                     continue
                 
                 # Inject error
                 modified_trajectory = inject_errors_into_trajectory(trajectory)
                 
                 # Write to JSONL
                 outfile.write(json.dumps(modified_trajectory, ensure_ascii=False) + '\n')
                 injected_count += 1
                 
             except json.JSONDecodeError as e:
                 logger.error(f"Failed to parse JSON in row {row_num}: {e}")
                 skipped_count += 1
             except Exception as e:
                 logger.error(f"Unexpected error processing row {row_num}: {e}")
                 skipped_count += 1

    logger.info(f"Error injection complete. Injected: {injected_count}, Skipped: {skipped_count}")
    logger.info(f"Output written to: {output_path}")
    
    # Verify output exists and is not empty
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("Verification: Output file created successfully.")
    else:
        logger.error("Verification failed: Output file is missing or empty.")
        sys.exit(1)

if __name__ == "__main__":
    main()
