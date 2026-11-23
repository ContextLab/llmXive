"""
Manifest generation script for the project.

This script scans the ``data`` directory for all files (excluding the manifest
itself), computes their SHA‑256 hashes, writes a JSON manifest to
``data/manifest.json`` and validates the manifest using the companion validator
in ``utils/validate_manifest.py``.

The manifest format is a simple mapping from relative file paths (POSIX style,
relative to the repository root) to their hexadecimal SHA‑256 hash strings, e.g.:

{
    "data/raw/stimuli.csv": "a3b2c1d4...",
    "data/processed/anonymised_ratings.csv": "f5e4d3c2..."
}

The script is intended to be run after any artifact creation step.
"""

import json
import sys
from pathlib import Path
from typing import Dict

from config import get_project_root, get_data_dir
from utils.validate_manifest import validate_manifest

def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hash of the file at *file_path* as a hex string."""
    import hashlib

    hasher = hashlib.sha256()
    # Read in chunks to support large files without excessive memory use.
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_manifest() -> Dict[str, str]:
    """
    Walk the project's ``data`` directory and produce a mapping of
    relative file paths to SHA‑256 hashes.

    The manifest file itself (``data/manifest.json``) is excluded from the
    calculation to avoid a circular dependency.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    manifest_path = data_dir / "manifest.json"

    manifest: Dict[str, str] = {}
    for file_path in data_dir.rglob("*"):
        if file_path.is_file() and file_path != manifest_path:
            # Store paths using forward slashes relative to the repository root.
            rel_path = str(file_path.relative_to(project_root)).replace("\\", "/")
            manifest[rel_path] = compute_sha256(file_path)
    return manifest

def save_manifest(manifest: Dict[str, str]) -> None:
    """Write *manifest* as pretty‑printed JSON to ``data/manifest.json``."""
    manifest_path = get_data_dir() / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

def main(argv: list = None) -> int:
    """
    Entry‑point for the manifest generation script.

    Returns exit code ``0`` on success; any validation error results in a
    non‑zero exit code and an error message printed to ``stderr``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # No command‑line options are required for now; the script always
    # (re)generates the full manifest.
    manifest = generate_manifest()
    save_manifest(manifest)

    try:
        # Validate immediately so CI can catch mismatches early.
        validate_manifest()
    except Exception as exc:
        sys.stderr.write(f"Manifest validation failed: {exc}\\n")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
