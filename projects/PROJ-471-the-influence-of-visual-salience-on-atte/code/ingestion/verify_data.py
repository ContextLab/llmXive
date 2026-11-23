"""
Verify that the Moral Foundations Eye-Tracking dataset (OpenNeuro ds003123) is
present under `data/raw/ds003123/` and generate a SHA-256 checksum manifest
at `data/raw/checksums.json`.

The script aborts loudly with a RuntimeError containing the code
`DATA_MISSING_001: ds003123 incomplete` if any of the following are not met:
  1. `data/raw/ds003123/` must exist.
  2. `data/raw/ds003123/stimuli/` must exist.
  3. At least one `sub-*/` participant folder must exist and contain at least one file.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def gather_files(root: Path) -> List[Path]:
    """Recursively collect all regular files under root."""
    return [p for p in root.rglob("*") if p.is_file()]

def main() -> None:
    """
    Verify dataset presence and integrity.
    """
    # Resolve paths
    raw_root: Path = paths.data("raw")
    dataset_dir: Path = raw_root / "ds003123"
    stimuli_dir = dataset_dir / "stimuli"
    checksum_path = raw_root / "checksums.json"

    # 1. Confirm data/raw/ds003123/ exists
    if not dataset_dir.is_dir():
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # 2. Confirm stimuli/ exists
    if not stimuli_dir.is_dir():
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # 3. Require at least one sub-*/ participant folder containing files
    sub_dirs = sorted(dataset_dir.glob("sub-*"))
    if not sub_dirs:
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    participant_files: List[Path] = []
    for sub in sub_dirs:
        participant_files.extend(gather_files(sub))

    if not participant_files:
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # 4. Compute SHA-256 checksums for all files under stimuli/ and sub-*/
    stimuli_files = gather_files(stimuli_dir)
    all_files_to_hash = stimuli_files + participant_files

    if not all_files_to_hash:
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    manifest: Dict = {"files": {}}
    for f in all_files_to_hash:
        # Path relative to data/raw
        rel_path = f.relative_to(raw_root).as_posix()
        manifest["files"][rel_path] = compute_sha256(f)

    # Write the manifest
    with checksum_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Dataset verification succeeded. Checksums written to {checksum_path}")
    print("Dataset verification succeeded")

if __name__ == "__main__":
    main()
