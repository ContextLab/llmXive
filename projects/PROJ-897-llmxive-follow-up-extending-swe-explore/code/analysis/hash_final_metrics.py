"""
hash_final_metrics.py

Implements T033: Integrate hash_artifacts.py to hash final data/results/final_metrics.json.

This script ensures the integrity of the final metrics output by computing a SHA256
hash and generating a manifest file. It depends on the existence of
data/results/final_metrics.json (produced by T031c).
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Import from the shared utils module as per API surface
from utils.hash_artifacts import compute_sha256, generate_manifest
from config import get_config_summary, get_path


def hash_final_metrics_file(metrics_path: Path) -> Dict[str, Any]:
    """
    Computes the SHA256 hash of the final metrics JSON file and generates a manifest.

    Args:
        metrics_path: Path to data/results/final_metrics.json

    Returns:
        A dictionary containing the hash, file path, and manifest data.

    Raises:
        FileNotFoundError: If the metrics file does not exist.
        ValueError: If the file is not valid JSON.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Required artifact missing for hashing: {metrics_path}. "
            "Ensure T031c (stats.py) has run and generated final_metrics.json."
        )

    # Compute the hash
    file_hash = compute_sha256(metrics_path)

    # Read content to include in manifest metadata
    with open(metrics_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Basic validation that it is valid JSON
    try:
        json_content = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {metrics_path}: {e}")

    # Generate manifest
    manifest = generate_manifest(
        file_path=metrics_path,
        hash_value=file_hash,
        file_type="json",
        description="Final statistical metrics and associational analysis results",
        metadata={
            "bytes": len(content.encode('utf-8')),
            "lines": len(content.splitlines()),
            "key_count": len(json_content.keys()) if isinstance(json_content, dict) else 0
        }
    )

    return {
        "file_path": str(metrics_path),
        "hash": file_hash,
        "manifest": manifest
    }


def main() -> int:
    """
    Main entry point for T033.
    Validates that final_metrics.json exists, hashes it, and saves the manifest.
    """
    print("Starting T033: Hashing final metrics artifact...")
    
    config = get_config_summary()
    print(f"Using config: {config}")

    # Define paths relative to project root
    results_dir = get_path("results")
    metrics_file = results_dir / "final_metrics.json"
    manifest_file = results_dir / "final_metrics_manifest.json"

    try:
        # Perform the hashing
        result = hash_final_metrics_file(metrics_file)
        
        # Write the manifest to disk
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(result["manifest"], f, indent=2)
        
        print(f"SUCCESS: Hashed {metrics_file}")
        print(f"  SHA256: {result['hash']}")
        print(f"  Manifest saved to: {manifest_file}")
        
        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("HINT: T031c (stats.py) must run successfully to generate data/results/final_metrics.json before T033 can run.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected failure during hashing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())