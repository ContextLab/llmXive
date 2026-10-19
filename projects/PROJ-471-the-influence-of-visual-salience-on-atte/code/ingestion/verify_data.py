"""
Verify that the Moral Foundations Eye‑Tracking dataset (OpenNeuro ds003123) is
present under ``data/raw/ds003123/`` and generate a SHA‑256 checksum manifest
at ``data/raw/checksums.json``.

The script aborts loudly with a ``RuntimeError`` containing the code
``DATA_MISSING_001`` if the dataset directory is missing, if any expected
sub-directory (stimuli/ or sub-*) is absent, or if any checksum does not match.

The manifest format is:
{
    "files": [
        {"path": "<relative/path>", "sha256": "<hash>"},
        ...
    ]
}
where ``path`` is relative to ``data/raw``.
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
    The ``path`` entries are stored relative to ``raw_root`` (data/raw).
    """
    entries = []
    for f in files:
        rel_path = f.relative_to(raw_root)
        entries.append({"path": str(rel_path), "sha256": compute_sha256(f)})
    return {"files": entries}

def main() -> None:
    """
    Verify dataset presence and integrity.

    - Checks for existence of data/raw/ds003123/.
    - Checks for stimuli/ and at least one sub-*/ directory.
    - If checksums.json exists, verifies all listed files and their hashes.
    - If checksums.json is missing, creates it from current files.
    - Ensures every physical file is represented in the manifest.
    """
    raw_root: Path = paths.data("raw")
    dataset_dir: Path = raw_root / "ds003123"
    checksum_path: Path = raw_root / "checksums.json"

    # 1. Basic existence check
    if not dataset_dir.is_dir():
        raise RuntimeError(
            "DATA_MISSING_001: ds003123 not found at data/raw/ds003123/"
        )

    # 2. Check for expected sub-directories
    stimuli_dir = dataset_dir / "stimuli"
    if not stimuli_dir.is_dir():
        raise RuntimeError(
            "DATA_MISSING_001: ds003123 not found at data/raw/ds003123/ (missing stimuli/)"
        )

    # Check for at least one participant directory (sub-*)
    sub_dirs = list(dataset_dir.glob("sub-*"))
    if not sub_dirs:
        raise RuntimeError(
            "DATA_MISSING_001: ds003123 not found at data/raw/ds003123/ (missing participant sub- directories)"
        )

    # 3. Gather current files
    dataset_files = gather_dataset_files(dataset_dir)

    # 4. Load or create the checksum manifest
    if checksum_path.is_file():
        logger.info(f"Loading existing checksum manifest from {checksum_path}")
        with checksum_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        logger.info("Checksum manifest not found – creating a new one.")
        manifest = build_manifest(raw_root, dataset_files)
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {checksum_path}")

    # 5. Verify each entry in the manifest
    listed_paths = set()
    for entry in manifest.get("files", []):
        rel_path = Path(entry["path"])
        listed_paths.add(rel_path)
        absolute_path = raw_root / rel_path
        if not absolute_path.is_file():
            raise RuntimeError(
                f"DATA_MISSING_001: Expected file missing – {rel_path}"
            )
        expected_hash = entry["sha256"]
        actual_hash = compute_sha256(absolute_path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"DATA_MISSING_001: Checksum mismatch for {rel_path}"
            )

    # 6. Ensure every physical file is represented in the manifest
    actual_paths = {p.relative_to(raw_root) for p in dataset_files}
    missing_in_manifest = actual_paths - listed_paths
    if missing_in_manifest:
        missing_str = ", ".join(str(p) for p in sorted(missing_in_manifest))
        raise RuntimeError(
            f"DATA_MISSING_001: Files missing from checksum manifest – {missing_str}"
        )

    logger.info("Dataset verification succeeded.")
    print("Dataset verification succeeded")

if __name__ == "__main__":
    main()
