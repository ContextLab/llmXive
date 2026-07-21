import os
import random
import hashlib
import json
import pickle
from typing import Optional, Dict, Any, Tuple, List

def set_seed(seed: int):
    """
    Sets the random seed for reproducibility.
    """
    random.seed(seed)

def get_seed_state() -> Dict[str, Any]:
    """
    Returns the current state of the random number generator.
    """
    return {
        "seed": random.getstate()
    }

def restore_seed_state(state: Dict[str, Any]):
    """
    Restores the state of the random number generator.
    """
    random.setstate(state["seed"])

def verify_seed(seed: int) -> bool:
    """
    Verifies that a seed is valid.
    """
    return isinstance(seed, int) and seed >= 0

def generate_task_seed(base_seed: int, task_index: int) -> int:
    """
    Generates a unique seed for a task based on the base seed and task index.
    """
    return base_seed + task_index

def save_seed_state(seed: int, state: Dict[str, Any], path: str):
    """
    Saves the seed and state to a file.
    """
    data = {
        "seed": seed,
        "state": state
    }
    with open(path, 'w') as f:
        json.dump(data, f)

def load_seed_state(path: str) -> Tuple[int, Dict[str, Any]]:
    """
    Loads the seed and state from a file.
    """
    with open(path, 'r') as f:
        data = json.load(f)
    return data["seed"], data["state"]

def verify_pairing(trace_id: str, task_instance: Dict[str, Any]) -> bool:
    """
    Verifies that a trace_id is correctly paired with a task_instance.
    Implements FR-008 precondition.
    """
    if not isinstance(task_instance, dict):
        raise ValueError("task_instance must be a dictionary")
    
    if "trace_id" not in task_instance:
        raise ValueError("task_instance must contain 'trace_id'")
    
    if "seed" not in task_instance:
        raise ValueError("task_instance must contain 'seed'")
    
    stored_trace_id = task_instance["trace_id"]
    stored_seed = task_instance["seed"]
    
    # Verify that the trace_id matches the one in the task_instance
    if stored_trace_id != trace_id:
        return False
    
    # Generate the expected trace_id from the seed
    expected_trace_id = hashlib.md5(f"trace_{stored_seed}".encode()).hexdigest()[:16]
    
    return expected_trace_id == trace_id

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test seed utilities")
    parser.add_argument("--seed", type=int, default=42, help="Base seed")
    
    args = parser.parse_args()
    
    set_seed(args.seed)
    state = get_seed_state()
    
    print(f"Seed: {args.seed}")
    print(f"State saved: {bool(state)}")
    
    # Test pairing
    trace_id = hashlib.md5(f"trace_{args.seed}".encode()).hexdigest()[:16]
    task_instance = {"trace_id": trace_id, "seed": args.seed}
    
    is_valid = verify_pairing(trace_id, task_instance)
    print(f"Pairing valid: {is_valid}")

if __name__ == "__main__":
    main()