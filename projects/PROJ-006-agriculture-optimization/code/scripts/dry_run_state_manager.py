import os
import tempfile
from pathlib import Path
import sys
from src.utils import state_manager
import hashlib

def main():
    """
    Dry-run verification of the state manager.
    Creates a dummy file, updates state, and verifies the hash mechanism.
    """
    # Ensure project root is in path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    # Import constants relative to project
    data_raw_dir = project_root / "data" / "raw"
    state_file = project_root / "state" / "projects" / "PROJ-006-agriculture-optimization.yaml"

    # Create dummy file if it doesn't exist
    dummy_file = data_raw_dir / "dummy.txt"
    if not dummy_file.exists():
        data_raw_dir.mkdir(parents=True, exist_ok=True)
        with open(dummy_file, "w") as f:
            f.write("Dummy content for state manager verification.")
        print(f"Created dummy file: {dummy_file}")

    # Compute hash manually to verify
    sha256_hash = hashlib.sha256()
    with open(dummy_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    expected_hash = sha256_hash.hexdigest()

    # Run state manager update
    print("Updating state manager...")
    state_manager.update_artifact_hashes()

    # Load state and verify
    state = state_manager.load_state()
    if "artifact_hashes" in state and "data/raw" in state["artifact_hashes"]:
        raw_hashes = state["artifact_hashes"]["data/raw"]
        if "dummy.txt" in raw_hashes:
          stored_hash = raw_hashes["dummy.txt"]
          if stored_hash == expected_hash:
              print("SUCCESS: Hash matches expected value.")
              return 0
          else:
              print(f"FAILURE: Hash mismatch. Expected {expected_hash}, got {stored_hash}")
              return 1
        else:
            print("FAILURE: dummy.txt not found in state hashes.")
            return 1
    else:
        print("FAILURE: State structure invalid.")
        return 1

if __name__ == "__main__":
    exit(main())
