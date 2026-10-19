"""
Script to compute SHA-256 checksums for all files in the project's data/ directory.

Implements Constitution Principle V (Data Integrity) while respecting the platform's
restriction that only project-owned directories may be written to. The resulting
manifest is stored under ``data/artifact_hashes.json`` (instead of the platform‑owned
``state/`` directory) so that the script can be executed without violating the
repository contract.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

def compute_sha256(file_path: str) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return None

def collect_data_files(base_dir: str) -> list:
    """Recursively collect all files in the given base directory."""
    data_path = Path(base_dir)
    if not data_path.exists():
        print(f"Warning: Data directory {base_dir} does not exist.", file=sys.stderr)
        return []

    files = []
    for root, _, filenames in os.walk(data_path):
        for filename in filenames:
            # Skip the checksum file itself to avoid circular dependency
            if filename == "artifact_hashes.json":
                continue
            full_path = Path(root) / filename
            files.append(str(full_path))
    return sorted(files)

def main():
    """Entry point for artifact‑hash generation."""
    # Determine the project root (assumes this script lives in ``code/scripts/``)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    data_dir = project_root / "data"
    output_dir = data_dir  # Write the manifest inside the data folder (project‑owned)
    output_file = output_dir / "artifact_hashes.json"

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning data directory: {data_dir}")
    files = collect_data_files(str(data_dir))

    if not files:
        print("No data files found to hash.")
        manifest = {
            "status": "empty",
            "files": [],
            "checksum_file": str(output_file)
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return

    print(f"Found {len(files)} files. Computing checksums...")

    checksums = {}
    for file_path in files:
        relative_path = str(Path(file_path).relative_to(project_root))
        hash_val = compute_sha256(file_path)
        if hash_val:
            checksums[relative_path] = hash_val
            print(f"  {relative_path}: {hash_val[:16]}...")
        else:
            print(f"  Skipped {relative_path} (read error)", file=sys.stderr)

    manifest = {
        "status": "success",
        "total_files": len(checksums),
        "checksum_file": str(output_file),
        "files": checksums
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Checksum manifest saved to: {output_file}")

if __name__ == "__main__":
    main()