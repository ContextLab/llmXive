"""
T032: Integrate hash_artifacts.py to hash final_metrics.json.

This script computes the SHA256 hash of the final metrics file and generates
a manifest for traceability and integrity verification (Constitution Principle V).
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Import from sibling modules based on provided API surface
from utils.hash_artifacts import compute_sha256, generate_manifest
from config import get_config_summary, get_path


def hash_final_metrics_file() -> Dict[str, Any]:
    """
    Compute the SHA256 hash of data/results/final_metrics.json.
    
    Returns:
        Dict containing the hash, file path, and metadata.
    
    Raises:
        FileNotFoundError: If final_metrics.json does not exist.
    """
    config = get_config_summary()
    metrics_path = get_path("results", "final_metrics.json")
    
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Final metrics file not found at {metrics_path}. "
            "Ensure T030c (multiplicity correction) has been executed to generate this file."
        )
    
    # Compute hash
    file_hash = compute_sha256(metrics_path)
    
    # Load content for metadata
    with open(metrics_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    # Prepare metadata
    metadata = {
        "file": str(metrics_path),
        "algorithm": "sha256",
        "hash": file_hash,
        "size_bytes": metrics_path.stat().st_size,
        "metrics_summary": {
            "num_issues": len(content.get("issues", [])),
            "coverage_p_value": content.get("coverage", {}).get("bonferroni_adjusted_p_value"),
            "ranking_p_value": content.get("ranking", {}).get("bonferroni_adjusted_p_value"),
            "statistical_method": content.get("statistical_method")
        }
    }
    
    # Generate manifest
    manifest = generate_manifest([metrics_path], metadata)
    
    return {
        "success": True,
        "hash": file_hash,
        "manifest": manifest,
        "file_path": str(metrics_path)
    }
    
    print(f"Hashed final_metrics.json: {file_hash}")
    return result


def main():
    """Entry point for T032."""
    print("Starting T032: Hashing final_metrics.json...")
    try:
        result = hash_final_metrics_file()
        print(f"Success! Hash: {result['hash']}")
        print(f"Manifest generated at: {Path(get_path('results', 'manifest_final_metrics.json'))}")
        
        # Save manifest to disk for persistence
        manifest_path = get_path("results", "manifest_final_metrics.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(result["manifest"], f, indent=2)
        
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error during hashing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
