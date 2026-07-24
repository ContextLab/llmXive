"""
T032: Integrate hash_artifacts.py to hash final data/results/final_metrics.json.

This script computes the SHA256 hash of the final metrics file and updates the
manifest in data/results/ to ensure data integrity and traceability (Constitution Principle V).
It is a specific integration of the generic `utils.hash_artifacts` module.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

from utils.hash_artifacts import compute_sha256, generate_manifest
from config import get_config_summary, get_path


def hash_final_metrics_file() -> Dict[str, Any]:
    """
    Computes the SHA256 hash of the final_metrics.json file.

    Returns:
        Dict containing the file path, hash, and timestamp.
    """
    metrics_path = get_path("results", "final_metrics.json")
    
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Final metrics file not found at {metrics_path}. "
            "Ensure T030c (Multiplicty Correction) has been run to generate this file."
        )

    file_hash = compute_sha256(metrics_path)
    
    result = {
        "file": str(metrics_path),
        "hash": file_hash,
        "status": "hashed"
    }
    
    print(f"Hashed final_metrics.json: {file_hash}")
    return result


def main() -> int:
    """Main entry point for T032."""
    try:
        config_summary = get_config_summary()
        print(f"Running T032: Hashing Final Metrics (Config: {config_summary})")
        
        # Hash the specific file
        hash_result = hash_final_metrics_file()
        
        # Generate/Update the manifest for the results directory
        results_dir = get_path("results")
        manifest = generate_manifest(results_dir)
        
        # Save manifest to results directory
        manifest_path = results_dir / "MANIFEST.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Manifest updated at {manifest_path}")
        print(f"Task T032 completed successfully.")
        
        return 0
    except Exception as e:
        print(f"Error during T032 execution: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
