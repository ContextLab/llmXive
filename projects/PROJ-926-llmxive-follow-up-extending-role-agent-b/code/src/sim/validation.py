"""
Validation module for ALFWorld trajectory analysis.

Implements ground-truth extraction, validation mapping, and ambiguity handling.
This module focuses on extracting raw ground-truth logs and applying validation rules.
"""
import json
import os
import hashlib
import argparse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.config.config import DATA_PATH, SEED

# Ensure data directories exist
RAW_DATA_PATH = os.path.join(DATA_PATH, "raw")
DERIVED_DATA_PATH = os.path.join(DATA_PATH, "derived")
os.makedirs(RAW_DATA_PATH, exist_ok=True)
os.makedirs(DERIVED_DATA_PATH, exist_ok=True)


def compute_checksum(data: str) -> str:
    """Compute SHA-256 checksum for data integrity verification."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def extract_ground_truth_from_simulator(
    simulator_logs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract raw ground-truth state transitions from ALFWorld simulator logs.
    
    This function processes the raw logs from the simulator to extract the 
    ground-truth state transitions. It does NOT apply any validation rules 
    or priority mappings here - that is done in T007c/T007b.
    
    Args:
        simulator_logs: List of raw simulator log entries from ALFWorld
        
    Returns:
        List of extracted ground-truth state transitions in JSON format
    """
    ground_truth_transitions = []
    
    for idx, log_entry in enumerate(simulator_logs):
        # Extract state transition information
        transition = {
            "id": f"gt_{idx:06d}",
            "step": log_entry.get("step", idx),
            "state": log_entry.get("state", {}),
            "action": log_entry.get("action", ""),
            "observation": log_entry.get("observation", ""),
            "reward": log_entry.get("reward", 0),
            "done": log_entry.get("done", False),
            "ground_truth_action": log_entry.get("ground_truth_action", log_entry.get("action", "")),
            "timestamp": datetime.now().isoformat()
        }
        ground_truth_transitions.append(transition)
    
    return ground_truth_transitions


def load_ground_truth_raw(filepath: str) -> List[Dict[str, Any]]:
    """
    Load raw ground-truth data from a JSON file.
    
    Args:
        filepath: Path to the JSON file containing raw ground-truth data
        
    Returns:
        List of ground-truth state transitions
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground-truth file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def save_ground_truth_raw(
    transitions: List[Dict[str, Any]], 
    output_path: str,
    include_checksum: bool = True
) -> Dict[str, Any]:
    """
    Save raw ground-truth transitions to a JSON file with checksumming.
    
    Args:
        transitions: List of ground-truth state transitions
        output_path: Path where the JSON file will be saved
        include_checksum: Whether to include checksum metadata
        
    Returns:
        Metadata dictionary about the saved file
    """
    json_content = json.dumps(transitions, indent=2, ensure_ascii=False)
    
    if include_checksum:
        checksum = compute_checksum(json_content)
    else:
        checksum = None
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    metadata = {
        "output_path": output_path,
        "record_count": len(transitions),
        "timestamp": datetime.now().isoformat(),
        "checksum": checksum,
        "status": "saved"
    }
    
    return metadata


def validate_trajectory(
    trajectory: Dict[str, Any],
    ground_truth: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate a single trajectory against ground-truth data.
    
    Args:
        trajectory: The trajectory to validate
        ground_truth: List of ground-truth transitions to compare against
        
    Returns:
        Tuple of (is_valid, failure_reason, failure_step_index)
    """
    # Basic validation logic - check if trajectory has required fields
    required_fields = ["id", "steps", "actions"]
    for field in required_fields:
        if field not in trajectory:
            return False, f"Missing required field: {field}", None
    
    # Compare trajectory actions against ground-truth
    trajectory_steps = trajectory.get("steps", [])
    for idx, step in enumerate(trajectory_steps):
        if idx < len(ground_truth):
            gt_action = ground_truth[idx].get("ground_truth_action", "")
            traj_action = step.get("action", "")
            
            if traj_action != gt_action:
                return False, f"Action mismatch at step {idx}", idx
    
    return True, None, None


def process_trajectory_for_ambiguity(
    trajectory: Dict[str, Any],
    ground_truth: List[Dict[str, Any]]
) -> bool:
    """
    Check if a trajectory contains ambiguous elements that prevent clear validation.
    
    Args:
        trajectory: The trajectory to check
        ground_truth: List of ground-truth transitions
        
    Returns:
        True if trajectory is ambiguous, False otherwise
    """
    # Check for ambiguous states (e.g., multiple valid actions)
    steps = trajectory.get("steps", [])
    for step in steps:
        if step.get("ambiguous", False):
            return True
        
        # Check for missing critical information
        if not step.get("action") and not step.get("observation"):
            return True
    
    return False


def run_validation_with_ambiguity_handling(
    trajectories: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run validation on multiple trajectories with ambiguity handling.
    
    Args:
        trajectories: List of trajectories to validate
        ground_truth: List of ground-truth transitions
        
    Returns:
        Dictionary containing validation results
    """
    results = {
        "total_trajectories": len(trajectories),
        "valid": 0,
        "invalid": 0,
        "ambiguous": 0,
        "details": []
    }
    
    for trajectory in trajectories:
        is_ambiguous = process_trajectory_for_ambiguity(trajectory, ground_truth)
        
        if is_ambiguous:
            results["ambiguous"] += 1
            results["details"].append({
                "trajectory_id": trajectory.get("id"),
                "status": "AMBIGUOUS",
                "reason": "Trajectory contains ambiguous elements"
            })
        else:
            is_valid, reason, step_idx = validate_trajectory(trajectory, ground_truth)
            
            if is_valid:
                results["valid"] += 1
                results["details"].append({
                    "trajectory_id": trajectory.get("id"),
                    "status": "PASS",
                    "reason": None
                })
            else:
                results["invalid"] += 1
                results["details"].append({
                    "trajectory_id": trajectory.get("id"),
                    "status": "FAIL",
                    "reason": reason,
                    "failure_step": step_idx
                })
    
    return results


def extract_ground_truth_from_task_bank(
    task_bank_path: str,
    task_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extract ground-truth state transitions from the ALFWorld task bank.
    
    This function reads the task bank (JSON/SQLite) and extracts the 
    ground-truth state transitions for specified tasks.
    
    Args:
        task_bank_path: Path to the task bank file
        task_ids: Optional list of specific task IDs to extract
                
    Returns:
        List of ground-truth state transitions
    """
    if not os.path.exists(task_bank_path):
        raise FileNotFoundError(f"Task bank not found: {task_bank_path}")
    
    with open(task_bank_path, 'r', encoding='utf-8') as f:
        task_bank = json.load(f)
    
    ground_truth_list = []
    
    tasks = task_bank.get("tasks", [])
    for task in tasks:
        if task_ids is None or task.get("id") in task_ids:
            transitions = task.get("ground_truth_transitions", [])
            for idx, transition in enumerate(transitions):
                gt_entry = {
                    "task_id": task.get("id"),
                    "step": idx,
                    "state": transition.get("state", {}),
                    "action": transition.get("action", ""),
                    "observation": transition.get("observation", ""),
                    "reward": transition.get("reward", 0),
                    "done": transition.get("done", False),
                    "id": f"{task.get('id')}_gt_{idx:06d}"
                }
                ground_truth_list.append(gt_entry)
    
    return ground_truth_list


def run(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for ground-truth extraction and validation.
    
    This function orchestrates the extraction of ground-truth data from 
    the ALFWorld simulator and saves it to the raw data directory.
    
    Args:
        args: Optional argparse namespace with command-line arguments
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Extract and validate ground-truth data")
        parser.add_argument("--input", type=str, default=None, help="Input simulator log file")
        parser.add_argument("--output", type=str, default=None, help="Output file for raw ground-truth")
        parser.add_argument("--task-bank", type=str, default=None, help="Path to task bank file")
        parser.add_argument("--task-ids", type=str, default=None, help="Comma-separated list of task IDs")
        args = parser.parse_args()
    
    print(f"[T007a] Starting ground-truth extraction at {datetime.now().isoformat()}")
    
    try:
        # If task bank is provided, extract from there
        if args.task_bank:
            task_ids = None
            if args.task_ids:
                task_ids = [tid.strip() for tid in args.task_ids.split(",")]
            
            print(f"[T007a] Extracting ground-truth from task bank: {args.task_bank}")
            ground_truth = extract_ground_truth_from_task_bank(args.task_bank, task_ids)
        
        # Otherwise, load from simulator logs
        elif args.input:
            print(f"[T007a] Loading simulator logs from: {args.input}")
            with open(args.input, 'r', encoding='utf-8') as f:
                simulator_logs = json.load(f)
            
            print(f"[T007a] Extracting ground-truth from {len(simulator_logs)} simulator entries")
            ground_truth = extract_ground_truth_from_simulator(simulator_logs)
        
        else:
            # Default: extract from standard task bank location
            default_task_bank = os.path.join(DATA_PATH, "raw", "alfworld_task_bank.json")
            if os.path.exists(default_task_bank):
                print(f"[T007a] Using default task bank: {default_task_bank}")
                ground_truth = extract_ground_truth_from_task_bank(default_task_bank)
            else:
                raise FileNotFoundError(
                    "No input provided and default task bank not found. "
                    "Please provide --input or --task-bank argument."
                )
        
        # Determine output path
        output_path = args.output
        if not output_path:
            output_path = os.path.join(RAW_DATA_PATH, "ground_truth_raw.json")
        
        # Save with checksumming
        print(f"[T007a] Saving {len(ground_truth)} ground-truth transitions to {output_path}")
        metadata = save_ground_truth_raw(ground_truth, output_path)
        
        print(f"[T007a] Ground-truth extraction complete!")
        print(f"  - Records: {metadata['record_count']}")
        print(f"  - Checksum: {metadata['checksum']}")
        print(f"  - Output: {metadata['output_path']}")
        
        # Log to validation log
        validation_log_path = os.path.join(RAW_DATA_PATH, "validation_log.json")
        log_entry = {
            "task_id": "T007a",
            "timestamp": datetime.now().isoformat(),
            "operation": "ground_truth_extraction",
            "status": "SUCCESS",
            "output_path": output_path,
            "record_count": metadata['record_count'],
            "checksum": metadata['checksum']
        }
        
        # Append to validation log
        existing_logs = []
        if os.path.exists(validation_log_path):
            with open(validation_log_path, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        
        existing_logs.append(log_entry)
        
        with open(validation_log_path, 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, indent=2)
        
    except Exception as e:
        print(f"[T007a] ERROR: {str(e)}")
        
        # Log failure
        validation_log_path = os.path.join(RAW_DATA_PATH, "validation_log.json")
        log_entry = {
            "task_id": "T007a",
            "timestamp": datetime.now().isoformat(),
            "operation": "ground_truth_extraction",
            "status": "FAILED",
            "error_message": str(e)
        }
        
        existing_logs = []
        if os.path.exists(validation_log_path):
            with open(validation_log_path, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        
        existing_logs.append(log_entry)
        
        with open(validation_log_path, 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, indent=2)
        
        raise


def main():
    """CLI entry point."""
    run()


if __name__ == "__main__":
    main()