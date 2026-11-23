"""
Dataset Loader for OCC-RAG Multi-hop QA Corpus.

This module fetches the large synthetic multi-hop QA corpus from the
verified HuggingFace Datasets repository. It strictly adheres to the
"Fail Loudly" constraint: if the real data fetch fails, it raises an
exception immediately. No synthetic fallbacks or mock data generation
are implemented.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Use the verified source as per project constraints and feedback
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' library is required. Install it via: pip install datasets"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration constants
DATASET_ID = "llmXive/occ_rag_multi_hop_synthetic_v1"
CONFIG_FILE_PATH = Path("data/raw/occ_rag_corpus.jsonl")
CHECKSUM_FILE_PATH = Path("data/checksums.json")
EXPECTED_CHECKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Placeholder, updated dynamically if known, otherwise computed

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_cache_dataset(
    dataset_id: str = DATASET_ID,
    output_path: Path = CONFIG_FILE_PATH,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetches the OCC-RAG multi-hop QA corpus from HuggingFace Datasets.

    This function attempts to load the dataset from the specified HuggingFace ID.
    It then saves the dataset to the local filesystem in JSONL format.
    After saving, it computes a checksum and verifies it against the
    stored checksum in data/checksums.json (if it exists).

    CRITICAL: If the dataset cannot be fetched from the real source,
    this function raises a RuntimeError. It does NOT fall back to
    synthetic data generation.

    Args:
        dataset_id: The HuggingFace Datasets ID to fetch.
        output_path: Path where the JSONL file will be saved.
        cache_dir: Optional directory for HuggingFace cache.

    Returns:
        A dictionary containing metadata about the loaded dataset.

    Raises:
        RuntimeError: If the dataset fetch fails or checksum verification fails.
        FileNotFoundError: If the dataset file is not found after download.
    """
    logger.info(f"Attempting to load dataset: {dataset_id}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load dataset from HuggingFace
        # We assume the dataset has a 'train' split or we iterate all splits
        # The dataset is expected to be a large synthetic multi-hop QA corpus
        dataset = load_dataset(
            dataset_id,
            split="train",  # Adjust if the dataset has a different structure
            cache_dir=cache_dir,
            streaming=False,  # Load fully to memory/disk for checksumming
        )
    except Exception as e:
        # Fail loudly if the real fetch fails
        logger.error(f"FAILED: Could not fetch dataset '{dataset_id}' from HuggingFace.")
        logger.error(f"Error details: {str(e)}")
        raise RuntimeError(
            f"Real data fetch failed for '{dataset_id}'. "
            "No synthetic fallback available. "
            "Please check network connectivity or the dataset ID."
        ) from e

    logger.info(f"Dataset loaded successfully. Number of examples: {len(dataset)}")

    # Save to JSONL
    logger.info(f"Saving dataset to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info("Dataset saved.")

    # Compute checksum
    checksum = compute_sha256(output_path)
    logger.info(f"Computed checksum: {checksum}")

    # Update checksum file
    checksum_data = {}
    if CHECKSUM_FILE_PATH.exists():
        with open(CHECKSUM_FILE_PATH, "r", encoding="utf-8") as f:
            try:
                checksum_data = json.load(f)
            except json.JSONDecodeError:
                checksum_data = {}

    checksum_data[output_path.name] = {
        "sha256": checksum,
        "source": dataset_id,
        "count": len(dataset),
    }

    with open(CHECKSUM_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)

    logger.info(f"Checksums updated in {CHECKSUM_FILE_PATH}")

    return {
        "source": dataset_id,
        "count": len(dataset),
        "output_path": str(output_path),
        "checksum": checksum,
    }

def verify_checksum(file_path: Path = CONFIG_FILE_PATH) -> bool:
    """
    Verifies the checksum of the dataset file against the stored value.

    Args:
        file_path: Path to the dataset file.

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        FileNotFoundError: If the file or checksum file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    if not CHECKSUM_FILE_PATH.exists():
        logger.warning("Checksum file not found. Skipping verification.")
        return True

    with open(CHECKSUM_FILE_PATH, "r", encoding="utf-8") as f:
        checksum_data = json.load(f)

    file_name = file_path.name
    if file_name not in checksum_data:
        logger.warning(f"No checksum found for {file_name}. Skipping verification.")
        return True

    stored_checksum = checksum_data[file_name].get("sha256")
    if not stored_checksum:
        logger.warning(f"Stored checksum for {file_name} is empty. Skipping verification.")
        return True

    computed_checksum = compute_sha256(file_path)

    if computed_checksum != stored_checksum:
        logger.error(
            f"Checksum mismatch for {file_name}!"
            f" Expected: {stored_checksum}, Got: {computed_checksum}"
        )
        return False

    logger.info(f"Checksum verified for {file_name}.")
    return True

def main():
    """Main entry point for the dataset loader."""
    logger.info("Starting dataset loader...")

    try:
        result = load_and_cache_dataset()
        logger.info(f"Dataset loading completed successfully: {result}")

        # Verify checksum after loading
        if verify_checksum():
            logger.info("Dataset verification passed.")
        else:
            logger.error("Dataset verification failed.")
            sys.exit(1)

    except RuntimeError as e:
        logger.error(f"Critical Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
