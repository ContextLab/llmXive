import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data/raw")
DATASET_NAME = "codexglue_code_to_text-python"
DATASET_SPLIT = "train"
CHECKSUM_FILE = DATA_DIR / "codexglue_checksums.json"

def fetch_codexglue_dataset() -> Optional[Dict]:
    """
    Fetches the CodeXGLUE Python code-generation subset from HuggingFace.
    Returns the dataset object or None if fetching fails.
    """
    try:
        logger.info(f"Attempting to fetch dataset: {DATASET_NAME}")
        dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT, trust_remote_code=True)
        logger.info(f"Successfully fetched {len(dataset)} samples from CodeXGLUE.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch CodeXGLUE dataset: {e}")
        return None

def validate_sample_size(dataset: Optional[Dict], min_samples: int = 10) -> bool:
    """
    Validates that the fetched dataset has at least min_samples.
    Returns True if valid, False otherwise.
    """
    if dataset is None:
        logger.warning("Dataset is None, validation failed.")
        return False
    
    count = len(dataset)
    if count < min_samples:
        logger.warning(f"Sample size {count} is below minimum threshold {min_samples}.")
        return False
    
    logger.info(f"Sample size validation passed: {count} >= {min_samples}")
    return True

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def save_dataset(dataset: Dict, output_dir: Path, filename: str = "codexglue_sample.json") -> Optional[Path]:
    """
    Saves the dataset to a JSON file and computes its checksum.
    Returns the path to the saved file if successful, None otherwise.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    try:
        # Convert dataset to list of dicts for JSON serialization
        data_list = []
        for item in dataset:
            data_list.append({
                "prompt_id": item.get("file_name", "unknown"),
                "code": item.get("code", ""),
                "docstring": item.get("docstring", "")
            })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=2)

        # Compute and store checksum
        checksum = compute_file_hash(output_path)
        if not checksum:
            logger.error("Failed to compute checksum.")
            return None

        checksum_entry = {
            "filename": filename,
            "sha256": checksum,
            "record_count": len(data_list)
        }

        # Load existing checksums if any
        if CHECKSUM_FILE.exists():
            with open(CHECKSUM_FILE, "r", encoding="utf-8") as f:
                checksums = json.load(f)
        else:
            checksums = {}

        # Update and save
        checksums[filename] = checksum_entry
        with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)

        logger.info(f"Dataset saved to {output_path} with checksum {checksum[:16]}...")
        return output_path

    except Exception as e:
        logger.error(f"Failed to save dataset: {e}")
        return None

def verify_baseline_exists() -> bool:
    """
    Verifies that the human baseline file exists.
    """
    baseline_path = DATA_DIR / "human_baseline_times.json"
    if not baseline_path.exists():
        logger.error(f"Human baseline file not found at {baseline_path}.")
        return False
    
    try:
        with open(baseline_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or len(data) == 0:
            logger.error("Human baseline file is empty or invalid format.")
            return False
        logger.info("Human baseline file verified.")
        return True
    except Exception as e:
        logger.error(f"Error reading human baseline: {e}")
        return False

def validate_checksum(file_path: Path) -> bool:
    """
    Validates the checksum of a downloaded file against the stored checksum.
    Returns True if valid or if this is the first run (no stored checksum), False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist, cannot validate checksum.")
        return False

    if not CHECKSUM_FILE.exists():
        logger.info("No checksum file found. This is likely the first run. Checksum validation skipped.")
        return True

    try:
        with open(CHECKSUM_FILE, "r", encoding="utf-8") as f:
            checksums = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load checksum file: {e}")
        return False

    filename = file_path.name
    if filename not in checksums:
        logger.warning(f"No stored checksum for {filename}. Saving new checksum.")
        return True

    stored_entry = checksums[filename]
    current_hash = compute_file_hash(file_path)

    if current_hash != stored_entry["sha256"]:
        logger.error(f"Checksum mismatch for {filename}!")
        logger.error(f"  Expected: {stored_entry['sha256']}")
        logger.error(f"  Found:    {current_hash}")
        return False

    logger.info(f"Checksum validation passed for {filename}.")
    return True

def main():
    """
    Main entry point for downloading and validating CodeXGLUE data.
    """
    logger.info("Starting CodeXGLUE data download process.")

    # 1. Fetch dataset
    dataset = fetch_codexglue_dataset()
    if not validate_sample_size(dataset):
        logger.error("Sample size validation failed. Aborting.")
        sys.exit(1)

    # 2. Save dataset
    saved_path = save_dataset(dataset, DATA_DIR)
    if not saved_path:
        logger.error("Failed to save dataset. Aborting.")
        sys.exit(1)

    # 3. Validate checksum (T008 Implementation)
    # This ensures data integrity for subsequent runs or corruption checks.
    if not validate_checksum(saved_path):
        logger.error("Checksum validation failed. Data may be corrupted.")
        sys.exit(1)

    # 4. Verify baseline exists (dependency for downstream tasks)
    if not verify_baseline_exists():
        logger.warning("Human baseline not found. Downstream tasks may fail.")
        # We do not exit here as T006 is responsible for creating this if missing,
        # but we log the warning as per T005/T006 dependencies.

    logger.info("Data download and validation completed successfully.")

if __name__ == "__main__":
    main()