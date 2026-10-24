"""
Verify that the Moral Foundations Eye‑Tracking dataset (OpenNeuro ds003123) is
present under ``data/raw/ds003123/`` and generate a SHA‑256 checksum manifest
at ``data/raw/checksums.json``.

The script aborts loudly with a ``RuntimeError`` containing the code
``DATA_MISSING_001`` if any of the required conditions are not met:
  1. ``data/raw/ds003123/`` must exist.
  2. ``stimuli/`` sub‑directory must exist.
  3. At least one ``sub‑*`` participant directory must exist and contain at
     least one file (eye‑tracking logs or related data).
  4. All files under ``stimuli/`` and under each ``sub‑*`` directory are
     hashed with SHA‑256 and recorded.

The manifest format is:
{
    "files": {
        "<relative/path>": "<hex_sha256>",
        ...
    }
}
where ``<relative/path>`` is relative to ``data/raw``.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def gather_dataset_files(root: Path) -> List[Path]:
    """Recursively collect all regular files under ``root``."""
    return [p for p in root.rglob("*") if p.is_file()]

def build_manifest(raw_root: Path, files: List[Path]) -> Dict:
    """
    Build a checksum manifest dictionary.
    The ``files`` list contains absolute Path objects; keys in the manifest
    are paths relative to ``raw_root`` (i.e. ``data/raw``).
    """
    manifest: Dict[str, Dict] = {"files": {}}
    for f in files:
        rel_path = f.relative_to(raw_root).as_posix()
        manifest["files"][rel_path] = compute_sha256(f)
    return manifest

def main() -> None:
    """
    Verify dataset presence and integrity.

    - Checks for existence of ``data/raw/ds003123/``.
    - Checks for ``stimuli/`` sub‑directory.
    - Requires at least one ``sub‑*`` participant directory containing at
      least one file.
    - Creates or verifies ``checksums.json`` containing SHA‑256 hashes for
      **all** files under ``stimuli/`` and under each participant folder.
    """
    raw_root: Path = paths.data("raw")
    dataset_dir: Path = raw_root / "ds003123"
    checksum_path: Path = raw_root / "checksums.json"

    # --------------------------------------------------------------
    # 1️⃣  Basic existence checks
    # --------------------------------------------------------------
    if not dataset_dir.is_dir():
        # Unified error message as required by the specification.
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    stimuli_dir = dataset_dir / "stimuli"
    if not stimuli_dir.is_dir():
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # --------------------------------------------------------------
    # 2️⃣  Verify participant directories
    # --------------------------------------------------------------
    sub_dirs = sorted(dataset_dir.glob("sub-*"))
    if not sub_dirs:
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # At least one file inside any participant folder
    participant_files: List[Path] = []
    for sub in sub_dirs:
        participant_files.extend(gather_dataset_files(sub))

    if not participant_files:
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # --------------------------------------------------------------
    # 3️⃣  Gather all files that must be hashed
    # --------------------------------------------------------------
    # Files under stimuli/ plus all participant files
    files_to_hash = gather_dataset_files(stimuli_dir) + participant_files

    # --------------------------------------------------------------
    # 4️⃣  Load existing manifest or create a new one
    # --------------------------------------------------------------
    if checksum_path.is_file():
        logger.info(f"Loading existing checksum manifest from {checksum_path}")
        with checksum_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        logger.info("Checksum manifest not found – creating a new one.")
        manifest = build_manifest(raw_root, files_to_hash)
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {checksum_path}")

    # --------------------------------------------------------------
    # 5️⃣  Verify each entry in the manifest
    # --------------------------------------------------------------
    for rel_path_str, expected_hash in manifest.get("files", {}).items():
        rel_path = Path(rel_path_str)
        absolute_path = raw_root / rel_path
        if not absolute_path.is_file():
            raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")
        actual_hash = compute_sha256(absolute_path)
        if actual_hash != expected_hash:
            raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    # --------------------------------------------------------------
    # 6️⃣  Ensure every required physical file is represented
    # --------------------------------------------------------------
    actual_paths = {p.relative_to(raw_root).as_posix() for p in files_to_hash}
    missing_in_manifest = actual_paths - set(manifest.get("files", {}).keys())
    if missing_in_manifest:
        raise RuntimeError("DATA_MISSING_001: ds003123 incomplete")

    logger.info("Dataset verification succeeded.")
    print("Dataset verification succeeded")

if __name__ == "__main__":
    main()