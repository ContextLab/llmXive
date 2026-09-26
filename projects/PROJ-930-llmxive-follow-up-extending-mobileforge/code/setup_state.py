"""
Setup script to initialize the `state/` directory structure for artifact
checksums and versioning (Constitution Principle III).

This script creates the necessary directory hierarchy and an initial
metadata file to track artifact versions and checksums.
"""

import os
import sys
from pathlib import Path

# Define the state directory relative to the project root
# The project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"


def initialize_state_structure() -> bool:
    """
    Creates the `state/` directory and subdirectories if they don't exist.
    Initializes a `manifest.json` file to track artifact versions and checksums.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    try:
        # Create the main state directory
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] State directory created/verified at: {STATE_DIR}")

        # Create subdirectories for different types of artifacts
        subdirs = [
            "checksums",
            "versions",
            "manifests"
        ]

        for subdir in subdirs:
            subdir_path = STATE_DIR / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Subdirectory created: {subdir_path}")

        # Initialize the main manifest file if it doesn't exist
        manifest_path = STATE_DIR / "manifest.json"
        if not manifest_path.exists():
            initial_manifest = {
                "version": "1.0.0",
                "created_at": None,  # Will be set by the first registration
                "artifacts": {}
            }
            import json
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(initial_manifest, f, indent=2)
            print(f"[INFO] Initial manifest created at: {manifest_path}")
        else:
            print(f"[INFO] Manifest already exists at: {manifest_path}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to initialize state structure: {e}", file=sys.stderr)
        return False


def main():
    """
    Entry point for the script.
    """
    print("Initializing state directory structure for artifact versioning...")
    success = initialize_state_structure()
    if success:
        print("State directory initialization completed successfully.")
        sys.exit(0)
    else:
        print("State directory initialization failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
