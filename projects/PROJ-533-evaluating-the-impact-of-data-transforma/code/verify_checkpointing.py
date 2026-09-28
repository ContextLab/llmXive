"""
Verification script for T004b: Verify code/utils/checkpointing.py works.

This script creates a checkpoint file in results/checkpoints/ and verifies
it contains valid JSON with the required keys:
- current_dataset_id (str)
- last_seed (int)
- error_counts (dict)
"""
import os
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.checkpointing import save_state, load_state, get_checkpoint_path, ensure_checkpoint_dir


def main():
    run_id = "test_run_t004b"
    checkpoint_dir = project_root / "results" / "checkpoints"
    
    # Ensure checkpoint directory exists
    ensure_checkpoint_dir(checkpoint_dir)
    
    # Prepare test data with required keys
    test_data = {
        "current_dataset_id": "test_dataset_001",
        "last_seed": 42,
        "error_counts": {
            "download_errors": 0,
            "filter_errors": 0,
            "transformation_errors": 0
        }
    }
    
    # Save the checkpoint
    save_path = save_state(run_id, "initialization", test_data)
    
    print(f"Checkpoint saved to: {save_path}")
    
    # Verify the file exists
    if not os.path.exists(save_path):
        print("ERROR: Checkpoint file was not created")
        return 1
    
    # Load and verify the checkpoint
    loaded_state = load_state(run_id)
    
    if loaded_state is None:
        print("ERROR: Failed to load checkpoint state")
        return 1
    
    # Verify required keys exist
    required_keys = ["current_dataset_id", "last_seed", "error_counts"]
    missing_keys = [key for key in required_keys if key not in loaded_state]
    
    if missing_keys:
        print(f"ERROR: Missing required keys in checkpoint: {missing_keys}")
        return 1
    
    # Verify data types
    if not isinstance(loaded_state["current_dataset_id"], str):
        print("ERROR: current_dataset_id must be a string")
        return 1
    
    if not isinstance(loaded_state["last_seed"], int):
        print("ERROR: last_seed must be an integer")
        return 1
    
    if not isinstance(loaded_state["error_counts"], dict):
        print("ERROR: error_counts must be a dictionary")
        return 1
    
    # Verify content matches
    if loaded_state["current_dataset_id"] != test_data["current_dataset_id"]:
        print("ERROR: current_dataset_id mismatch")
        return 1
    
    if loaded_state["last_seed"] != test_data["last_seed"]:
        print("ERROR: last_seed mismatch")
        return 1
    
    if loaded_state["error_counts"] != test_data["error_counts"]:
        print("ERROR: error_counts mismatch")
        return 1
    
    # Verify the file contains valid JSON
    with open(save_path, 'r') as f:
        try:
            json_content = json.load(f)
            print(f"Checkpoint is valid JSON with keys: {list(json_content.keys())}")
        except json.JSONDecodeError as e:
            print(f"ERROR: Checkpoint file is not valid JSON: {e}")
            return 1
    
    print("SUCCESS: Checkpointing verification passed!")
    print(f"  - File exists: {save_path}")
    print(f"  - Valid JSON: Yes")
    print(f"  - Required keys present: {required_keys}")
    print(f"  - Data integrity: Verified")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())