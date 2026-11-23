"""
Verification script for Task T004.
This script demonstrates the functionality of state_manager.py by:
1. Creating a test file (if not exists).
2. Computing its SHA-256 hash.
3. Updating the state/...yaml file with the hash.
4. Verifying the hash matches.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.state_manager import update_artifact_state, verify_artifact, load_state, compute_sha256

def main():
    print("=== T004 Verification Script ===")

    # Define paths relative to project root
    test_file_path = PROJECT_ROOT / "data" / "raw" / "test_state_file.txt"
    state_file_path = PROJECT_ROOT / "state" / "pipeline_state.yaml"

    # Ensure the test file exists
    if not test_file_path.exists():
        print(f"Creating test file: {test_file_path}")
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        test_file_path.write_text("This is a test file for T004 verification.\nIt ensures state_manager.py works correctly.\n")
    else:
        print(f"Test file exists: {test_file_path}")

    # Step 1: Update state with the test file hash
    print(f"\n1. Updating state for: {test_file_path}")
    try:
        updated_state = update_artifact_state(test_file_path, state_file_path, description="T004 Verification Test File")
        print(f"   State updated successfully.")
        print(f"   Current artifacts in state: {list(updated_state['artifacts'].keys())}")
    except Exception as e:
        print(f"   ERROR: Failed to update state: {e}")
        sys.exit(1)

    # Step 2: Verify the hash in the state matches the file
    print(f"\n2. Verifying artifact integrity...")
    # Load the state to get the expected hash
    current_state = load_state(state_file_path)
    rel_path = str(test_file_path.relative_to(PROJECT_ROOT))
    if rel_path not in current_state.get("artifacts", {}):
        print(f"   ERROR: Artifact not found in state file: {rel_path}")
        sys.exit(1)

    expected_hash = current_state["artifacts"][rel_path]["hash"]
    is_valid = verify_artifact(test_file_path, expected_hash, state_file_path)

    if is_valid:
        print(f"   SUCCESS: Hash verification passed.")
        print(f"   Hash: {expected_hash}")
    else:
        print(f"   ERROR: Hash verification failed!")
        print(f"   Expected: {expected_hash}")
        print(f"   Computed: {compute_sha256(test_file_path)}")
        sys.exit(1)

    print("\n=== T004 Verification Complete ===")
    print("state_manager.py is working correctly.")

if __name__ == "__main__":
    main()