"""
Compute SHA-256 checksums for ALL downloaded datasets in data/raw/
and write results to data/checksums.csv (FR-010).
"""
import os
import sys
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.logging_config import setup_pipeline_logger

logger = setup_pipeline_logger("checksum_datasets")

RAW_DIR = project_root / "data" / "raw"
CHECKSUMS_FILE = project_root / "data" / "checksums.csv"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_raw_dataset_files() -> List[Path]:
    """Collect dataset files in the raw directory."""
    if not RAW_DIR.exists():
        logger.error(f"Raw directory does not exist: {RAW_DIR}")
        sys.exit(1)
    files = []
    for ext in ["*.csv", "*.arff", "*.txt", "*.parquet", "*.json"]:
        files.extend(RAW_DIR.glob(ext))
    # Exclude any non‑data files that may be present
    return [f for f in files if not f.name.startswith("log")]

def write_checksums_csv(checksums: List[Dict[str, Any]]) -> None:
    """Write checksum records to the canonical CSV file."""
    headers = ["dataset_id", "checksum"]
    with open(CHECKSUMS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(checksums)
    logger.info(f"Wrote {len(checksums)} checksum rows to {CHECKSUMS_FILE}")

def main():
    logger.info("Starting checksum computation for all raw datasets.")
    dataset_files = get_raw_dataset_files()
    if not dataset_files:
        logger.warning("No dataset files found in raw directory; creating empty checksums file.")
        write_checksums_csv([])
        sys.exit(0)

    checksums: List[Dict[str, Any]] = []
    for file_path in dataset_files:
        dataset_id = file_path.stem.replace("openml_", "").replace("uci_", "")
        try:
            sha = compute_sha256(file_path)
            checksums.append({"dataset_id": dataset_id, "checksum": sha})
            logger.info(f"Checksummed {dataset_id}: {sha[:12]}...")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")

    write_checksums_csv(checksums)
    logger.info("Checksum computation completed.")

if __name__ == "__main__":
    main()
