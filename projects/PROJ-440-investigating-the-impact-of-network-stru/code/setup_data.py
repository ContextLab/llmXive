import os
import sys
import json
from pathlib import Path

# Ensure the project root is in the path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.checksums import setup_data_directories, generate_checksum_file


def main():
    """
    Main entry point for setting up data directories and generating initial checksums.
    This script ensures the directory structure exists and creates a manifest for
    tracking data integrity.
    """
    print("Setting up data directory structure...")
    setup_data_directories()

    # Define the directories we expect to manage checksums for
    data_dirs = ["data/raw", "data/processed", "data/analysis"]
    checksum_files = []

    for d in data_dirs:
        dir_path = Path(d)
        if dir_path.exists():
            # Create a placeholder checksum file for each directory if one doesn't exist
            checksum_path = dir_path / "checksums.json"
            if not checksum_path.exists():
                # Create an empty manifest initially
                generate_checksum_file([], str(checksum_path))
                print(f"Created initial checksum manifest: {checksum_path}")
            checksum_files.append(str(checksum_path))
        else:
            print(f"Warning: Directory {d} does not exist and could not be created.")

    # Create a root manifest if needed
    root_manifest = Path("data/checksum_manifest.json")
    if not root_manifest.exists():
        # We can't checksum directories directly, but we can list the manifest locations
        manifest_content = {
            "version": "1.0",
            "generated_by": "setup_data.py",
            "sub_manifests": checksum_files
        }
        with open(root_manifest, "w") as f:
            json.dump(manifest_content, f, indent=2)
        print(f"Created root manifest: {root_manifest}")

    print("Data directory setup complete.")


if __name__ == "__main__":
    main()
