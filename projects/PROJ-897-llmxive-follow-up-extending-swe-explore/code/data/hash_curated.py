"""
Hash curated data artifacts in data/curated/ after generation.

This script integrates utils.hash_artifacts to compute SHA256 hashes
for all files in the curated directory and generates a manifest file.

Output:
    data/curated/manifest.json: Contains file paths and their SHA256 hashes.
    data/curated/.manifest.sha256: Checksum of the manifest itself.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

from utils.hash_artifacts import hash_directory, generate_manifest
from config import get_config_summary, get_path


def main() -> int:
    """
    Main entry point for hashing curated data artifacts.
    
    Returns:
        0 on success, 1 on failure.
    """
    config_summary = get_config_summary()
    print(f"Starting hash generation for curated artifacts...")
    print(f"Config: {config_summary}")

    curated_dir = get_path("data_curated")
    if not curated_dir.exists():
        print(f"ERROR: Curated directory does not exist: {curated_dir}")
        return 1

    print(f"Scanning directory: {curated_dir}")
    
    # Hash all files in the curated directory
    try:
        hash_result = hash_directory(curated_dir)
    except Exception as e:
        print(f"ERROR: Failed to hash directory: {e}")
        return 1

    if not hash_result["success"]:
        print(f"ERROR: Hashing failed: {hash_result.get('error', 'Unknown error')}")
        return 1

    files_hashed = hash_result["files"]
    print(f"Successfully hashed {len(files_hashed)} files:")
    for file_info in files_hashed:
        print(f"  - {file_info['path']}: {file_info['sha256'][:16]}...")

    # Generate and save manifest
    manifest_path = get_path("data_curated") / "manifest.json"
    try:
        manifest_content = generate_manifest(files_hashed, str(curated_dir))
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_content, f, indent=2)
        print(f"Manifest saved to: {manifest_path}")
    except Exception as e:
        print(f"ERROR: Failed to save manifest: {e}")
        return 1

    # Verify the manifest was created
    if not manifest_path.exists():
        print(f"ERROR: Manifest file not created: {manifest_path}")
        return 1

    print("Curated artifacts hashing completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
