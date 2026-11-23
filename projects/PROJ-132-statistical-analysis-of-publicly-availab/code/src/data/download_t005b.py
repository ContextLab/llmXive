"""
Task T005b: Download Verified eBird Sample.

Streams the verified eBird sample (vvud/eb-data) via datasets.load_dataset,
writes raw files to data/raw/ebird_sample/, and computes SHA-256 checksums.
"""
import os
import sys
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Import logging setup from existing config module
from src.config import setup_logging

# Import load_dataset from datasets
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install it via 'pip install datasets'.")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_dataset(output_dir: Path, dataset_name: str = "vvud/eb-data", split: str = "train") -> List[Path]:
    """
    Stream the verified eBird sample and write raw files to output_dir.

    Args:
        output_dir: Directory to save raw files.
        dataset_name: HuggingFace dataset name.
        split: Dataset split to load.

    Returns:
        List of paths to downloaded files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    logging.info(f"Loading dataset '{dataset_name}' (split='{split}') with streaming=True...")
    try:
        # Stream the dataset
        dataset = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as e:
        logging.error(f"Failed to load dataset '{dataset_name}': {e}")
        raise RuntimeError(f"Dataset '{dataset_name}' not available or failed to load: {e}")

    # Convert to pandas for easier handling if needed, or iterate directly
    # Since streaming yields dicts, we'll batch them and write to parquet/json
    # For simplicity and robustness, we'll write to JSONL format per batch
    batch_size = 10000
    batch_data = []
    file_counter = 0
    file_path = output_dir / f"ebird_sample_{file_counter}.jsonl"

    with open(file_path, "w", encoding="utf-8") as f:
        for i, record in enumerate(dataset):
            batch_data.append(record)
            if len(batch_data) >= batch_size:
                for rec in batch_data:
                    f.write(json.dumps(rec) + "\n")
                batch_data = []
                file_counter += 1
                file_path = output_dir / f"ebird_sample_{file_counter}.jsonl"
                f = open(file_path, "w", encoding="utf-8")  # Reopen for next batch

    # Write remaining records
    if batch_data:
        for rec in batch_data:
            f.write(json.dumps(rec) + "\n")
        f.close()
        file_counter += 1

    # Collect all file paths
    downloaded_files = list(output_dir.glob("ebird_sample_*.jsonl"))
    logging.info(f"Downloaded {len(downloaded_files)} shard files.")
    return downloaded_files


def verify_checksums(output_dir: Path, checksums_file: Path) -> bool:
    """
    Compute and store SHA-256 checksums for all downloaded files.

    Args:
        output_dir: Directory containing downloaded files.
        checksums_file: Path to write checksums.

    Returns:
        True if all checksums computed successfully.
    """
    checksums = {}
    files = list(output_dir.glob("ebird_sample_*.jsonl"))
    if not files:
        logging.error("No downloaded files found to checksum.")
        return False

    for file_path in files:
        checksum = compute_sha256(file_path)
        checksums[file_path.name] = checksum
        logging.info(f"Checksum for {file_path.name}: {checksum}")

    with open(checksums_file, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

    logging.info(f"Checksums written to {checksums_file}")
    return True


def archive_data(source_dir: Path, archive_dir: Path) -> None:
    """
    Copy raw data to archive directory.

    Args:
        source_dir: Source directory with raw files.
        archive_dir: Destination archive directory.
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    for file_path in source_dir.glob("*"):
        if file_path.is_file():
            shutil.copy2(file_path, archive_dir / file_path.name)
    logging.info(f"Archived data from {source_dir} to {archive_dir}")


def write_success_report(output_dir: Path, report_file: Path, checksums_file: Path) -> None:
    """
    Write a success report with metadata.

    Args:
        output_dir: Directory where files were saved.
        report_file: Path to write the report.
        checksums_file: Path to checksums file.
    """
    report = {
        "task_id": "T005b",
        "status": "success",
        "dataset": "vvud/eb-data",
        "output_directory": str(output_dir),
        "checksums_file": str(checksums_file),
        "files": [f.name for f in output_dir.glob("ebird_sample_*.jsonl")]
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logging.info(f"Success report written to {report_file}")


def run_download_pipeline() -> None:
    """
    Main pipeline for T005b: Download Verified eBird Sample.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    data_raw_dir = project_root / "data" / "raw" / "ebird_sample"
    data_archive_dir = project_root / "data" / "raw" / "archive"
    checksums_file = data_raw_dir / "checksums.sha256"
    success_report = data_raw_dir / "download_success.json"

    # Setup logging
    setup_logging()

    try:
        # Step 1: Download dataset
        downloaded_files = download_dataset(data_raw_dir)
        if not downloaded_files:
            raise RuntimeError("No files were downloaded.")

        # Step 2: Verify and write checksums
        if not verify_checksums(data_raw_dir, checksums_file):
            raise RuntimeError("Checksum verification failed.")

        # Step 3: Archive data
        archive_data(data_raw_dir, data_archive_dir)

        # Step 4: Write success report
        write_success_report(data_raw_dir, success_report, checksums_file)

        logging.info("T005b completed successfully.")

    except Exception as e:
        logging.error(f"T005b failed: {e}")
        raise


def main():
    """Entry point for script execution."""
    run_download_pipeline()


if __name__ == "__main__":
    main()
