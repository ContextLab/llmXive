"""
Simple verification script used by the quick‑start documentation.

It checks that the OpenNeuro Moral Foundations Eye‑Tracking dataset
(ds003123) is present under ``data/raw/`` and that a checksum manifest
(``data/raw/checksums.json``) exists and matches the files on disk.
If any check fails, a ``RuntimeError`` with the code ``DATA_MISSING_001``
is raised – this matches the behaviour expected by the quick‑start
validation step.
"""
import json
import hashlib
from pathlib import Path

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main() -> None:
    raw_root = paths.data("raw")
    dataset_dir = raw_root / "ds003123"
    checksum_file = raw_root / "checksums.json"

    if not dataset_dir.is_dir():
        raise RuntimeError("DATA_MISSING_001: Dataset directory not found.")

    if not checksum_file.is_file():
        raise RuntimeError("DATA_MISSING_001: checksum manifest not found.")

    # Load manifest
    with checksum_file.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Verify each listed file
    for entry in manifest.get("files", []):
        rel_path = Path(entry["path"])
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

    logger.info("Dataset verification succeeded.")

if __name__ == "__main__":
    main()
