"""
Updated hash_artifacts utility.

The original version attempted to write a platform‑owned state file
under `state/`, which is prohibited.  This revision computes SHA‑256
hashes for all files under the `data/` and `code/` directories and
writes the resulting mapping to a JSON file inside the project’s
own data area: `data/processed/artifact_hashes.json`.

The script exits with status 0 on success and non‑zero on failure.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Use the project‑wide logger
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def collect_files(root: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """Recursively collect files under *root* optionally filtered by *extensions*."""
    files: List[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            p = Path(dirpath) / fn
            if extensions is None or p.suffix in extensions:
                files.append(p)
    return sorted(files)

def hash_directory(root: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Compute SHA‑256 hashes for all files under *root*.

    Returns a mapping from path‑relative‑to‑project‑root to hex digest.
    """
    hashes: Dict[str, str] = {}
    for file_path in collect_files(root, extensions):
        # Path relative to the project root (two levels up from this file)
        rel_path = file_path.relative_to(Path(__file__).parents[2])
        hashes[str(rel_path)] = compute_file_hash(file_path)
        logger.debug(f"Hashed {rel_path}")
    return hashes

def main() -> int:
    """
    Entry point: hash the ``data`` and ``code`` trees and write the
    results to ``data/processed/artifact_hashes.json``.
    """
    project_root = Path(__file__).resolve().parents[2]

    data_dir = project_root / "data"
    code_dir = project_root / "code"

    try:
        logger.info("Hashing data directory")
        data_hashes = hash_directory(data_dir, extensions=[
            ".csv", ".json", ".nwk", ".pkl", ".png", ".txt", ".log"
        ])

        logger.info("Hashing code directory")
        code_hashes = hash_directory(code_dir, extensions=[
            ".py", ".sh", ".yaml", ".yml", ".toml"
        ])

        all_hashes = {**data_hashes, **code_hashes}

        output_path = project_root / "data" / "processed" / "artifact_hashes.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_hashes, f, indent=2)

        logger.info(f"Artifact hashes written to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to compute artifact hashes: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())