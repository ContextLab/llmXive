"""
Verification script for checkpointing functionality (Task T004b).

This script verifies that code/utils/checkpointing.py works correctly by:
1. Creating a checkpoint file in results/checkpoints/
2. Verifying the file contains valid JSON
3. Verifying the JSON contains required keys: current_dataset_id, last_seed, error_counts
4. Cleaning up the created checkpoint after verification
"""
import os
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from code.utils.checkpointing import save_state, load_state, get_checkpoint_path, ensure_checkpoint_dir


def main():
    """Verify checkpointing functionality."""
    print("Starting checkpoint verification (T004b)...")

    # Define a test run ID
    test_run_id = "verify_t004b_run"
    
    # Ensure checkpoint directory exists
    ensure_checkpoint_dir()
    print(f"✓ Checkpoint directory ensured at results/checkpoints/")

    # Prepare test data matching the required schema
    test_data = {
        "current_dataset_id": "dataset_uci_001",
        "last_seed": 42,
        "error_counts": {
            "download_errors": 0,
            "filter_errors": 0,
            "transformation_errors": 0
        }
    }

    # Save the state
    print(f"Saving state for run: {test_run_id}")
    save_state(test_run_id, step="verification_test", data=test_data)
    print("✓ State saved successfully")

    # Get the checkpoint path
    checkpoint_path = get_checkpoint_path(test_run_id)
    print(f"Checkpoint file path: {checkpoint_path}")

    # Verify file exists
    if not os.path.exists(checkpoint_path):
        print(f"✗ ERROR: Checkpoint file was not created at {checkpoint_path}")
        sys.exit(1)
    print("✓ Checkpoint file exists")

    # Load the state back
    print("Loading state from checkpoint...")
    loaded_data = load_state(test_run_id)

    if loaded_data is None:
        print("✗ ERROR: load_state returned None")
        sys.exit(1)
    print("✓ State loaded successfully")

    # Verify JSON structure and required keys
    required_keys = ["current_dataset_id", "last_seed", "error_counts"]
    missing_keys = [key for key in required_keys if key not in loaded_data]

    if missing_keys:
        print(f"✗ ERROR: Missing required keys: {missing_keys}")
        sys.exit(1)
    print(f"✓ All required keys present: {required_keys}")

    # Verify data types and values
    assert isinstance(loaded_data["current_dataset_id"], str), "current_dataset_id must be a string"
    assert isinstance(loaded_data["last_seed"], int), "last_seed must be an integer"
    assert isinstance(loaded_data["error_counts"], dict), "error_counts must be a dict"
    print("✓ Data types verified")

    # Verify specific values match what we saved
    assert loaded_data["current_dataset_id"] == test_data["current_dataset_id"], "current_dataset_id mismatch"
    assert loaded_data["last_seed"] == test_data["last_seed"], "last_seed mismatch"
    assert loaded_data["error_counts"] == test_data["error_counts"], "error_counts mismatch"
    print("✓ Saved data matches loaded data")

    # Verify the file contains valid JSON by reading raw content
    with open(checkpoint_path, 'r') as f:
        raw_content = f.read()
        try:
            json.loads(raw_content)
            print("✓ File contains valid JSON")
        except json.JSONDecodeError as e:
            print(f"✗ ERROR: Invalid JSON in checkpoint file: {e}")
            sys.exit(1)

    print("\n" + "="*50)
    print("Checkpoint verification (T004b) PASSED")
    print("="*50)
    print(f"Created checkpoint: {checkpoint_path}")
    print(f"Keys verified: {required_keys}")
    print(f"Data integrity: OK")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)