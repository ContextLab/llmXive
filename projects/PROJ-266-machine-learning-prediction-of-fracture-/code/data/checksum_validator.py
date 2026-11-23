"""
Task T053b: Compute and record SHA-256 checksum of data/raw/metadata.json.

This script ensures data integrity for the synthetic dataset metadata.
It reads the metadata file, computes the SHA-256 hash, and writes the
result to data/benchmarks/metadata_checksum.json.

Verification:
  python -c "import json, hashlib, pathlib; p=pathlib.Path('data/raw/metadata.json'); h=hashlib.sha256(p.read_bytes()).hexdigest(); d=json.load(open('data/benchmarks/metadata_checksum.json')); assert d['metadata_file'] == 'data/raw/metadata.json'; assert d['sha256'] == h; print('Checksum verified')"
"""
import json
import hashlib
import pathlib
import sys
import os

# Ensure we can import from code/
if 'code' not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def compute_sha256(file_path: pathlib.Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def main():
    """Compute checksum and write to data/benchmarks/metadata_checksum.json."""
    # Define paths relative to project root
    project_root = pathlib.Path(__file__).parent.parent.parent
    metadata_path = project_root / "data" / "raw" / "metadata.json"
    checksum_path = project_root / "data" / "benchmarks" / "metadata_checksum.json"

    # Verify metadata file exists
    if not metadata_path.exists():
        print(f"ERROR: Metadata file not found at {metadata_path}")
        sys.exit(1)

    # Compute checksum
    print(f"Computing SHA-256 checksum for {metadata_path}...")
    checksum = compute_sha256(metadata_path)
    print(f"Checksum computed: {checksum}")

    # Ensure output directory exists
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    # Write checksum manifest
    checksum_data = {
        "metadata_file": str(metadata_path.relative_to(project_root)),
        "sha256": checksum
    }

    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)

    print(f"Checksum written to {checksum_path}")
    print("Verification command:")
    print(f"  python -c \"import json, hashlib, pathlib; p=pathlib.Path('{metadata_path}'); h=hashlib.sha256(p.read_bytes()).hexdigest(); d=json.load(open('{checksum_path}')); assert d['metadata_file'] == '{metadata_path.relative_to(project_root)}'; assert d['sha256'] == h; print('Checksum verified')\"")

if __name__ == "__main__":
    main()