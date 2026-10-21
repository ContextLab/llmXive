"""
Simple checksum generator for the checkpointing task.

It scans ``data/raw`` for any parquet/CSV/ARFF files, computes a SHA‑256
checksum for each file, and writes ``data/checksums.csv`` with two columns:
``dataset_id`` (derived from the filename) and ``checksum``.
"""
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict

def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hash of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_raw_dataset_files() -> List[Path]:
    """Collect all supported raw dataset files."""
    raw_dir = Path("data") / "raw"
    if not raw_dir.is_dir():
        return []
    return [
        p
        for p in raw_dir.iterdir()
        if p.suffix.lower() in {".parquet", ".csv", ".arff"}
    ]

def get_dataset_id_from_filename(file_path: Path) -> str:
    """
    Derive a dataset identifier from the filename.

    Expected patterns:
    - ``openml_<id>.parquet`` → ``<id>``
    - ``uci_<name>.csv``      → ``<name>``
    If the pattern is not recognised, the stem of the file is returned.
    """
    stem = file_path.stem
    parts = stem.split("_")
    return parts[-1] if len(parts) > 1 else stem

def write_checksums_csv(checksums: List[Dict[str, str]]) -> None:
    """Write ``data/checksums.csv`` with a header."""
    csv_path = Path("data") / "checksums.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset_id", "checksum"])
        writer.writeheader()
        for row in checksums:
            writer.writerow(row)

def main() -> None:
    """Compute checksums for all raw files and persist them."""
    logger = logging.getLogger("checksum")
    logger.setLevel(logging.INFO)

    files = get_raw_dataset_files()
    if not files:
        logger.warning("No raw dataset files found – nothing to checksum.")
        return

    checksums: List[Dict[str, str]] = []
    for fp in files:
        ds_id = get_dataset_id_from_filename(fp)
        cs = compute_sha256(fp)
        checksums.append({"dataset_id": ds_id, "checksum": cs})
        logger.info(f"Checksum for {fp.name}: {cs}")

    write_checksums_csv(checksums)
    logger.info("All checksums have been written to data/checksums.csv")

if __name__ == "__main__":
    main()
