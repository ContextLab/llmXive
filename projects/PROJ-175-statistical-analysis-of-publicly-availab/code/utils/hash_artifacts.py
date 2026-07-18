import os
import sys
import json
import hashlib
from pathlib import Path

# Ensure the project root is in the path for imports if needed, 
# though this script uses standard library only.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FINAL_DIR = PROJECT_ROOT / "data" / "final"
DOCS_DIR = PROJECT_ROOT / "docs"
STATE_DIR = PROJECT_ROOT / "state"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files without loading entirely into memory
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def hash_artifacts():
    """
    Compute SHA-256 hashes for all final data artifacts and the final report.
    Writes results to state/final_artifacts_hashes.json.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    artifacts_to_hash = {}

    # 1. Hash all .parquet files in data/final/
    if DATA_FINAL_DIR.exists():
        for file_path in DATA_FINAL_DIR.glob("*.parquet"):
          relative_path = file_path.relative_to(PROJECT_ROOT)
          try:
              hash_val = compute_sha256(file_path)
              artifacts_to_hash[str(relative_path)] = hash_val
          except Exception as e:
              print(f"Error hashing {file_path}: {e}", file=sys.stderr)

    # 2. Hash all .json files in data/final/
    if DATA_FINAL_DIR.exists():
        for file_path in DATA_FINAL_DIR.glob("*.json"):
          relative_path = file_path.relative_to(PROJECT_ROOT)
          try:
              hash_val = compute_sha256(file_path)
              artifacts_to_hash[str(relative_path)] = hash_val
          except Exception as e:
              print(f"Error hashing {file_path}: {e}", file=sys.stderr)

    # 3. Hash the final report
    final_report_path = DOCS_DIR / "final_report.md"
    if final_report_path.exists():
        relative_path = final_report_path.relative_to(PROJECT_ROOT)
        try:
            hash_val = compute_sha256(final_report_path)
            artifacts_to_hash[str(relative_path)] = hash_val
        except Exception as e:
            print(f"Error hashing {final_report_path}: {e}", file=sys.stderr)
    else:
        print(f"Warning: Final report not found at {final_report_path}", file=sys.stderr)

    if not artifacts_to_hash:
        print("Warning: No artifacts found to hash.", file=sys.stderr)

    # Write the hash map to the state directory
    output_path = STATE_DIR / "final_artifacts_hashes.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(artifacts_to_hash, f, indent=2)

    print(f"Successfully hashed {len(artifacts_to_hash)} artifacts.")
    print(f"Output written to: {output_path}")
    return artifacts_to_hash

def main():
    hash_artifacts()

if __name__ == "__main__":
    main()
