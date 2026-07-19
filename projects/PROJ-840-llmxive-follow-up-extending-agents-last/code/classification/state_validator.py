import json
import os
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.config import load_config
from utils.seeds import verify_pairing
from classification.parser import parse_ale_trace
from classification.heuristics import normalize_state

# Constants
GOLDEN_SUBSET_PATH = "data/raw/golden_subset.json"
RAW_LOGS_DIR = "data/raw/ale_logs"
OUTPUT_REPORT_PATH = "data/processed/state_validation_report.json"
ACCURACY_THRESHOLD = 0.95

def load_golden_subset(path: str = GOLDEN_SUBSET_PATH) -> List[Dict[str, Any]]:
    """Load the golden subset of traces with ground truth labels."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Golden subset not found at {path}. "
            f"Run T015 (code/data/generator.py) first to generate real data."
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Golden subset must be a list of trace objects.")
    
    return data

def calculate_reconstruction_accuracy(
    golden_data: List[Dict[str, Any]],
    raw_logs_dir: str = RAW_LOGS_DIR
) -> Tuple[float, int, int]:
    """
    Calculate reconstruction accuracy by comparing parsed trace states
    against the ground truth in the golden subset.
    
    FR-009: Must calculate accuracy against data/raw/golden_subset.json.
    
    This function:
    1. Loads the golden subset (ground truth).
    2. Parses the corresponding raw ALE logs for each trace.
    3. Normalizes both the ground truth state and the parsed state.
    4. Compares them using a strict equality check (after normalization).
    
    Returns:
        Tuple of (accuracy, total_steps, correct_steps)
    """
    if not golden_data:
        return 0.0, 0, 0

    total_steps = 0
    correct_steps = 0
    errors = []

    for item in golden_data:
        trace_id = item.get("trace_id")
        if not trace_id:
            errors.append(f"Missing trace_id in golden data: {item}")
            continue

        ground_truth_state = item.get("step_state")
        if ground_truth_state is None:
            errors.append(f"Missing step_state in golden data for trace {trace_id}")
            continue

        # Locate the corresponding raw log file
        # Assumption: T015 generates logs named {trace_id}.json in data/raw/ale_logs/
        log_path = Path(raw_logs_dir) / f"{trace_id}.json"
        
        if not log_path.exists():
            # If the log file is missing, we cannot validate reconstruction.
            # This counts as a reconstruction failure (0/1 for this trace's steps).
            # In a real scenario, we might skip, but for accuracy calculation, 
            # missing data is a failure to reconstruct.
            step_count = len(ground_truth_state) if isinstance(ground_truth_state, list) else 1
            total_steps += step_count
            continue

        try:
            # Parse the raw log to get the reconstructed state
            parsed_result = parse_ale_trace(str(log_path))
            
            # Extract the reconstructed state from the parser output
            # The parser returns a dict with 'state' or similar key depending on implementation
            reconstructed_state = parsed_result.get("state") or parsed_result.get("step_state")
            
            if reconstructed_state is None:
                errors.append(f"Parser returned no state for {trace_id}")
                step_count = len(ground_truth_state) if isinstance(ground_truth_state, list) else 1
                total_steps += step_count
                continue

            # Normalize both states using the T011 heuristic (1e-6 tolerance)
            normalized_gt = normalize_state(ground_truth_state)
            normalized_parsed = normalize_state(reconstructed_state)

            # Compare the normalized states
            # We perform a deep comparison allowing for float tolerance
            is_match = deep_compare_states(normalized_gt, normalized_parsed)

            # Count steps
            if isinstance(ground_truth_state, list):
                step_count = len(ground_truth_state)
            else:
                step_count = 1
            
            total_steps += step_count
            if is_match:
                correct_steps += step_count
            else:
                errors.append(f"Mismatch for trace {trace_id}: GT={normalized_gt}, Parsed={normalized_parsed}")

        except Exception as e:
            errors.append(f"Error processing {trace_id}: {str(e)}")
            # Count as failure
            step_count = len(ground_truth_state) if isinstance(ground_truth_state, list) else 1
            total_steps += step_count

    if total_steps == 0:
        return 0.0, 0, 0

    accuracy = correct_steps / total_steps
    return accuracy, total_steps, correct_steps

def deep_compare_states(state1: Any, state2: Any, tolerance: float = 1e-6) -> bool:
    """
    Recursively compare two state dictionaries/structures.
    Floats are compared with tolerance.
    """
    if type(state1) != type(state2):
        return False

    if isinstance(state1, float):
        return math.isclose(state1, state2, rel_tol=tolerance, abs_tol=tolerance)
    
    if isinstance(state1, list):
        if len(state1) != len(state2):
            return False
        return all(deep_compare_states(s1, s2, tolerance) for s1, s2 in zip(state1, state2))
    
    if isinstance(state1, dict):
        if set(state1.keys()) != set(state2.keys()):
            return False
        return all(deep_compare_states(state1[k], state2[k], tolerance) for k in state1.keys())
    
    return state1 == state2

def main():
    """
    Execute State Reconstruction validation.
    Gate: Halt pipeline if accuracy < 0.95.
    """
    config = load_config("code/utils/config_schema.yaml")
    
    # Ensure pairing is valid before proceeding (T004b requirement)
    try:
        verify_pairing(task_id="T013", seed_path="data/seeds/pairing_seed.json")
    except FileNotFoundError:
        print("Warning: Pairing seed not found. Proceeding with validation.")
    except Exception as e:
        print(f"ERROR: Pairing verification failed: {e}")
        sys.exit(1)

    print(f"Loading golden subset from {GOLDEN_SUBSET_PATH}...")
    try:
        golden_data = load_golden_subset()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not golden_data:
        print("ERROR: Golden subset is empty.")
        sys.exit(1)

    print(f"Calculating reconstruction accuracy on {len(golden_data)} traces...")
    accuracy, total_steps, correct_steps = calculate_reconstruction_accuracy(golden_data)
    
    print(f"Reconstruction Accuracy: {accuracy:.4f} ({correct_steps}/{total_steps} steps correct)")
    
    # Prepare report
    report = {
        "task_id": "T013",
        "reconstruction_accuracy": accuracy,
        "threshold": ACCURACY_THRESHOLD,
        "status": "PASS" if accuracy >= ACCURACY_THRESHOLD else "FAIL",
        "total_traces": len(golden_data),
        "total_steps": total_steps,
        "correct_steps": correct_steps,
        "timestamp": "2023-10-27T10:00:00Z" 
    }

    # Ensure output directory exists
    output_dir = Path(OUTPUT_REPORT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Report written to {OUTPUT_REPORT_PATH}")

    # GATE LOGIC: Halt if accuracy < 0.95
    if accuracy < ACCURACY_THRESHOLD:
        print(f"CRITICAL: Reconstruction accuracy ({accuracy:.4f}) is below threshold ({ACCURACY_THRESHOLD}).")
        print("HALTING PIPELINE.")
        sys.exit(1)
    
    print("Gate passed. Pipeline can proceed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
