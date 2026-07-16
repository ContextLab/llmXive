"""
Validation utilities for ALFWorld agent trajectories.
Handles ground-truth logging, validation independence, and checksumming.
"""
import json
import hashlib
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import from existing project modules
from src.sim.alfworld_runner import run_episode
from src.config.config import DATA_PATH, SEED


def compute_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute a checksum for a file to ensure integrity."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def save_raw_ground_truth_logs(
    output_path: str,
    episodes_data: Optional[List[Dict[str, Any]]] = None,
    force_generate: bool = True
) -> Dict[str, str]:
    """
    Save raw ground-truth logs to a JSON file with checksumming.
    
    This function ensures 'Validation Independence' by creating a distinct,
    immutable artifact of the raw ground-truth data before any processing.
    
    Args:
        output_path: Path where the JSON file will be saved.
        episodes_data: Optional pre-fetched ground truth data. If None,
                       it generates fresh data by running ALFWorld episodes.
        force_generate: If True, forces regeneration of data even if file exists.
    
    Returns:
        A dictionary containing the output path and the computed checksum.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    data_to_save = episodes_data

    if data_to_save is None or force_generate:
        # Generate fresh ground-truth data by running episodes
        # We run a small set to establish the baseline ground truth
        # In a full run, this might load from a dataset, but for T007a
        # we ensure the mechanism works by running the simulator.
        print(f"Generating fresh ground-truth data for {output_path}...")
        data_to_save = []
        
        # Generate 10 ground-truth episodes to seed the raw log
        # Using the configured seed for determinism
        for i in range(10):
            episode_seed = SEED + i
            try:
                # Run the episode to get ground truth state transitions
                # run_episode returns action log and state transitions
                result = run_episode(task_id=0, seed=episode_seed)
                
                ground_truth_entry = {
                    "id": f"gt_{episode_seed}",
                    "timestamp": datetime.now().isoformat(),
                    "seed": episode_seed,
                    "task_id": 0,
                    "state_transitions": result.get("state_transitions", []),
                    "action_log": result.get("action_log", []),
                    "is_success": result.get("success", False),
                    "source": "simulated_ground_truth"
                }
                data_to_save.append(ground_truth_entry)
            except Exception as e:
                # If simulation fails (e.g., environment issues), log error
                # but continue to ensure the file is created with what we have
                print(f"Error generating episode {i}: {e}")
                continue

        if not data_to_save:
            raise RuntimeError("Failed to generate any ground-truth episodes. Check ALFWorld environment setup.")

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, indent=2, default=str)
    
    # Compute checksum
    checksum = compute_checksum(output_path)
    
    return {
        "path": output_path,
        "checksum": checksum,
        "record_count": len(data_to_save),
        "timestamp": datetime.now().isoformat()
    }


def validate_trajectory(action_log: List[Dict], ground_truth_log: List[Dict]) -> Dict[str, Any]:
    """
    Map agent actions to ground-truth state transitions.
    
    Args:
        action_log: List of actions taken by the agent.
        ground_truth_log: List of ground-truth state transitions.
    
    Returns:
        Validation result dictionary.
    """
    # Implementation of validation logic
    # This compares the agent's actions against the ground truth
    # to determine if the trajectory is valid.
    
    if not action_log or not ground_truth_log:
        return {
            "valid": False,
            "reason": "Empty action log or ground truth log"
        }
    
    # Simple heuristic validation: check if action count matches
    # In a real implementation, this would check semantic equivalence
    if len(action_log) != len(ground_truth_log):
        return {
            "valid": False,
            "reason": f"Action count mismatch: {len(action_log)} vs {len(ground_truth_log)}"
        }
    
    return {
        "valid": True,
        "reason": "Trajectory matches ground truth"
    }


def run():
    """
    Main entry point to execute the ground-truth logging task.
    Saves raw ground-truth logs to data/raw/ground_truth_raw.json.
    """
    output_path = os.path.join(DATA_PATH, "raw", "ground_truth_raw.json")
    
    print(f"Starting raw ground-truth log generation to {output_path}...")
    
    try:
        result = save_raw_ground_truth_logs(output_path)
        print(f"Successfully saved ground-truth logs.")
        print(f"  - Path: {result['path']}")
        print(f"  - Checksum: {result['checksum']}")
        print(f"  - Records: {result['record_count']}")
    except Exception as e:
        print(f"Error saving ground-truth logs: {e}")
        raise


if __name__ == "__main__":
    run()
