import os
import sys
import json
import hashlib
from pathlib import Path

def compute_sha256(file_path: str) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact not found for hashing: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error hashing file {file_path}: {e}")

def hash_artifacts(output_path: str = "state/final_artifacts_hashes.json") -> None:
    """
    Compute SHA-256 hashes for all final data artifacts and write to a JSON file.
    
    Artifacts to hash:
    - All .parquet files in data/final/
    - All .json files in data/final/
    - docs/final_report.md
    """
    project_root = Path(__file__).resolve().parents[2]
    final_data_dir = project_root / "data" / "final"
    docs_dir = project_root / "docs"
    state_dir = project_root / "state"
    
    artifacts_to_hash = []
    
    # Collect .parquet files from data/final/
    if final_data_dir.exists():
        for file_path in final_data_dir.glob("*.parquet"):
            artifacts_to_hash.append(str(file_path.relative_to(project_root)))
    
    # Collect .json files from data/final/
    if final_data_dir.exists():
        for file_path in final_data_dir.glob("*.json"):
            artifacts_to_hash.append(str(file_path.relative_to(project_root)))
    
    # Add final report
    final_report_path = docs_dir / "final_report.md"
    if final_report_path.exists():
        artifacts_to_hash.append(str(final_report_path.relative_to(project_root)))
    
    if not artifacts_to_hash:
        raise FileNotFoundError(
            "No artifacts found to hash. Ensure data/final/ contains parquet/json files "
            "and docs/final_report.md exists."
        )
    
    # Compute hashes
    hash_map = {}
    for rel_path in artifacts_to_hash:
        full_path = project_root / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact missing during hashing: {full_path}")
        hash_value = compute_sha256(str(full_path))
        hash_map[rel_path] = hash_value
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Write hashes to JSON
    output_file = state_dir / output_path
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(hash_map, f, indent=2, sort_keys=True)
    
    print(f"Successfully hashed {len(hash_map)} artifacts.")
    print(f"Hashes written to: {output_file}")

def main():
    """Entry point for the artifact hashing script."""
    try:
        hash_artifacts()
        print("Artifact hashing completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Artifact hashing failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()