"""
hash_artifacts.py
-----------------
Compute SHA‑256 checksums for every file under the project's ``data/`` directory
and write a manifest JSON file to ``data/artifact_hashes.json``.

This script satisfies **Task T007a**. Per platform constraints, it writes 
only to project-owned directories (``data/``) and avoids the platform-owned 
``state/`` directory to prevent shadowing.

The script can be invoked as a module:
    python -m code.scripts.hash_artifacts
"""

import hashlib
import json
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of ``file_path``.

    Parameters
    ----------
    file_path: Path
        Path to the file whose hash should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    # Read in binary mode, 4 KB chunks to avoid loading large files into memory.
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def collect_data_files(base_dir: Path) -> list[Path]:
    """
    Recursively collect all regular files under ``base_dir``.

    Parameters
    ----------
    base_dir: Path
        Directory to search (typically ``<project_root>/data``).

    Returns
    -------
    list[Path]
        Sorted list of file paths (absolute).
    """
    if not base_dir.is_dir():
        print(f"Warning: Data directory {base_dir} does not exist.", file=sys.stderr)
        return []

    files = [p for p in base_dir.rglob("*") if p.is_file()]
    # Sorting provides deterministic output across runs.
    return sorted(files)


def main() -> None:
    """
    Entry point for artifact‑hash generation.

    The manifest is written to ``data/artifact_hashes.json`` inside the
    project repository. The function prints progress information to stdout.
    """
    # Resolve the project root: <project_root>/code/scripts/hash_artifacts.py
    script_path = Path(__file__).resolve()
    # Path parents: [0] is code/scripts, [1] is code, [2] is <project_root>
    project_root = script_path.parents[2]

    data_dir = project_root / "data"
    manifest_path = data_dir / "artifact_hashes.json"

    # Ensure the output directory exists.
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scanning data directory: {data_dir}")
    all_files = collect_data_files(data_dir)

    # Exclude the manifest file itself to avoid a circular reference.
    files_to_hash = [p for p in all_files if p != manifest_path]

    if not files_to_hash:
        print("No data files found to hash.")
        manifest = {
            "status": "empty",
            "total_files": 0,
            "checksum_file": str(manifest_path),
            "files": {}
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return

    print(f"Found {len(files_to_hash)} files. Computing checksums...")

    checksums = {}
    for file_path in files_to_hash:
        # Compute hash relative to the project root for readability.
        rel_path = str(file_path.relative_to(project_root))
        try:
            hash_val = compute_sha256(file_path)
            checksums[rel_path] = hash_val
            # Show a short preview of the hash for progress monitoring.
            print(f"  {rel_path}: {hash_val[:16]}...")
        except Exception as exc:
            print(f"Error hashing {rel_path}: {exc}", file=sys.stderr)

    manifest = {
        "status": "success",
        "total_files": len(checksums),
        "checksum_file": str(manifest_path),
        "files": checksums
    }

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Checksum manifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()
