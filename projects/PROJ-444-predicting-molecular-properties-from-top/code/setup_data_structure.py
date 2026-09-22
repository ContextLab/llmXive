"""
Task T004: Setup data directory structure and state tracking.

Creates the required directory hierarchy:
- data/raw/
- data/processed/
- state/

And verifies their existence on script exit.
"""

import os
import json
from pathlib import Path
from typing import List


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists. Create it if it doesn't.

    Args:
        path: The Path object for the directory to ensure.

    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False


def initialize_file(path: Path, initial_content: dict = None) -> bool:
    """
    Initialize a JSON state file if it doesn't exist.

    Args:
        path: The Path object for the file to initialize.
        initial_content: A dictionary of initial content for the JSON file.

    Returns:
        True if the file was created or already exists, False on error.
    """
    try:
        if not path.exists():
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(initial_content or {}, f, indent=2)
        return True
    except OSError as e:
        print(f"Error initializing file {path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for T004.

    Creates the data directory structure and state tracking files.
    Verifies all required directories exist before exiting.

    Returns:
        0 on success, 1 on failure.
    """
    # Define project root (assuming this script is in code/ directory)
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    state_dir = project_root / "state"
    state_file = state_dir / "pipeline_state.json"

    # Define required directories
    required_dirs: List[Path] = [raw_dir, processed_dir, state_dir]

    # Create directories
    print("Creating directory structure...")
    all_created = True
    for dir_path in required_dirs:
        if ensure_directory(dir_path):
            print(f"  [OK] Created/Verified: {dir_path}")
        else:
            print(f"  [FAIL] Failed to create: {dir_path}")
            all_created = False

    # Initialize state file if it doesn't exist
    if all_created:
        print("Initializing state tracking file...")
        initial_state = {
            "initialized_at": None,
            "last_run": None,
            "checksums_validated": False,
            "data_ingestion_complete": False,
            "tda_computation_complete": False,
            "model_training_complete": False,
            "diagnostics_complete": False
        }
        if initialize_file(state_file, initial_state):
            print(f"  [OK] Initialized state file: {state_file}")
        else:
            print(f"  [FAIL] Failed to initialize state file: {state_file}")
            all_created = False

    # Verification step: Ensure all directories exist
    print("\nVerifying directory structure...")
    verification_failed = False
    for dir_path in required_dirs:
        if not dir_path.is_dir():
            print(f"  [FAIL] Verification failed: {dir_path} is not a directory")
            verification_failed = True
        else:
            print(f"  [OK] Verified: {dir_path}")

    if not verification_failed and state_file.exists():
        print(f"  [OK] Verified: {state_file} exists")
    elif not state_file.exists():
        print(f"  [FAIL] Verification failed: {state_file} does not exist")
        verification_failed = True

    if all_created and not verification_failed:
        print("\n✅ T004 Setup completed successfully.")
        return 0
    else:
        print("\n❌ T004 Setup failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())