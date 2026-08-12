import os
import sys
import hashlib
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_download(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """Verify the downloaded file exists and optionally matches checksum."""
    if not file_path.exists():
        logger.error(f"Downloaded file not found: {file_path}")
        return False

    if expected_checksum:
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {file_path}")
            logger.error(f"Expected: {expected_checksum}")
            logger.error(f"Actual: {actual_checksum}")
            return False
    return True

def download_from_huggingface(dataset_id: str, output_dir: Path, filename: str) -> Path:
    """Download dataset from HuggingFace Hub."""
    output_path = output_dir / filename
    if output_path.exists():
        logger.info(f"File already exists: {output_path}")
        return output_path

    logger.info(f"Downloading {dataset_id} to {output_path}")
    try:
        from huggingface_hub import hf_hub_download
        hf_hub_download(
            repo_id=dataset_id,
            filename=filename,
            local_dir=output_dir,
            local_dir_use_symlinks=False,
        )
        logger.info(f"Download successful: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

def validate_dataset_structure(file_path: Path) -> bool:
    """Validate that the dataset has the expected structure."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            logger.error("Dataset is not a non-empty list")
            return False

        if 'category' not in data[0]:
            logger.error("Missing 'category' key in dataset")
            return False

        logger.info("Dataset structure validated successfully")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False

def verify_filtered_data_integrity(filtered_path: Path, checksums_file: Path) -> bool:
    """
    Verify the integrity of the filtered dataset by comparing its SHA256 checksum
    against a known-good checksum stored in the state file.

    Args:
        filtered_path: Path to the filtered dataset (data/filtered/...)
        checksums_file: Path to the state file containing known checksums

    Returns:
        bool: True if checksums match or if state file doesn't exist yet (first run),
              False if checksums mismatch.
    """
    if not filtered_path.exists():
        logger.error(f"Filtered dataset not found: {filtered_path}")
        return False

    if not checksums_file.exists():
        logger.warning(f"Checksum state file not found: {checksums_file}. Skipping integrity check (first run?).")
        return True

    try:
        with open(checksums_file, 'r') as f:
            state_data = yaml.safe_load(f)

        known_checksum = state_data.get('filtered_dataset_sha256')

        if known_checksum is None:
            logger.warning("No known checksum found in state file. Skipping integrity check.")
            return True

        actual_checksum = calculate_sha256(filtered_path)

        if actual_checksum != known_checksum:
            logger.error("CRITICAL: Filtered dataset integrity check FAILED!")
            logger.error(f"Expected checksum: {known_checksum}")
            logger.error(f"Actual checksum: {actual_checksum}")
            logger.error("The filtered dataset has changed since the last verified run.")
            return False

        logger.info(f"Filtered dataset integrity verified. Checksum: {actual_checksum}")
        return True

    except Exception as e:
        logger.error(f"Error during integrity verification: {e}")
        return False

def main():
    """Main entry point for download and filter operations."""
    setup_logging()

    parser = argparse.ArgumentParser(description="Download and filter Edit-Compass dataset")
    parser.add_argument("--dataset-id", default="HuggingFaceH4/edit-compass", help="HuggingFace dataset ID")
    parser.add_argument("--output-dir", default="data/raw", help="Output directory for raw data")
    parser.add_argument("--filtered-dir", default="data/filtered", help="Output directory for filtered data")
    parser.add_argument("--categories", nargs="+", default=["World Knowledge Reasoning", "Visual Reasoning"], help="Categories to filter")
    parser.add_argument("--checksums-file", default="state/projects/PROJ-814-checksums.yaml", help="Path to checksums state file")
    parser.add_argument("--verify-only", action="store_true", help="Only verify integrity, do not download/filter")
    args = parser.parse_args()

    raw_dir = Path(args.output_dir)
    filtered_dir = Path(args.filtered_dir)
    checksums_file = Path(args.checksums_file)
    raw_file = raw_dir / "edit-compass.json"

    if args.verify_only:
        filtered_file = filtered_dir / "edit-compass-filtered.json"
        if verify_filtered_data_integrity(filtered_file, checksums_file):
            sys.exit(0)
        else:
            sys.exit(1)

    # Download
    if not raw_file.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
        download_from_huggingface(args.dataset_id, raw_dir, "edit-compass.json")

    # Validate structure
    if not validate_dataset_structure(raw_file):
        logger.error("FATAL: File structure mismatch. Missing 'category' key.")
        sys.exit(1)

    # Filter
    filtered_dir.mkdir(parents=True, exist_ok=True)
    filtered_file = filtered_dir / "edit-compass-filtered.json"

    with open(raw_file, 'r') as f:
        data = json.load(f)

    filtered_data = [item for item in data if item.get('category') in args.categories]

    if len(filtered_data) == 0:
        logger.error("FATAL: Filter returned zero records for target categories.")
        sys.exit(1)

    with open(filtered_file, 'w') as f:
        json.dump(filtered_data, f, indent=2)

    logger.info(f"Filtered dataset saved to {filtered_file} ({len(filtered_data)} records)")

    # Optional: Update checksums file with the new filtered dataset checksum
    if checksums_file.parent.exists():
        actual_checksum = calculate_sha256(filtered_file)
        try:
            if checksums_file.exists():
                with open(checksums_file, 'r') as f:
                    import yaml
                    state_data = yaml.safe_load(f) or {}
            else:
                state_data = {}

            state_data['filtered_dataset_sha256'] = actual_checksum

            with open(checksums_file, 'w') as f:
                import yaml
                yaml.dump(state_data, f)

            logger.info(f"Updated checksums file: {checksums_file}")
        except Exception as e:
            logger.warning(f"Could not update checksums file: {e}")

    sys.exit(0)

if __name__ == "__main__":
    main()
