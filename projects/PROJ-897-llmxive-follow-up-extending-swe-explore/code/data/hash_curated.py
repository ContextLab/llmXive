"""
Task T016: Integrate hash_artifacts.py to hash data/curated/ files after generation.

This script computes SHA256 hashes for all files in the data/curated/ directory
and generates a manifest file (manifest.json) containing the hashes and metadata.
It ensures data integrity for the curated dataset artifacts as per Constitution Principle V.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Import the hash_artifacts utilities
from utils.hash_artifacts import hash_directory, generate_manifest, get_config_summary

def main() -> int:
    """
    Main entry point for hashing curated data artifacts.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    # Get configuration
    config = get_config_summary()
    curated_dir = Path(config["paths"]["curated"])
    output_dir = Path(config["paths"]["results"])
    
    print(f"Hashing curated data artifacts from: {curated_dir}")
    
    if not curated_dir.exists():
        print(f"Error: Curated directory does not exist: {curated_dir}")
        return 1
    
    # Hash the curated directory
    try:
        hashes = hash_directory(curated_dir)
        
        # Generate manifest
        manifest = generate_manifest(hashes, curated_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write manifest to data/results/manifest_curated.json
        manifest_path = output_dir / "manifest_curated.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        
        print(f"Manifest written to: {manifest_path}")
        print(f"Hashed {len(hashes)} files in curated directory")
        
        return 0
        
    except Exception as e:
        print(f"Error hashing curated directory: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())