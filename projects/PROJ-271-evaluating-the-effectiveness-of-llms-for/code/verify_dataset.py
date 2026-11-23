"""
verify_dataset.py

This script verifies that the required HuggingFace dataset is reachable,
downloads a small test shard, computes its SHA‑256 checksum, and records the
checksum in ``data/checksums.txt``. If any step fails, the script aborts
with an exception so that the overall pipeline stops.
"""

import hashlib
import json
import logging
import os
from pathlib import Path

from datasets import load_dataset
from config import setup_logging, get_data_path, get_path

# Configure logger
logger = setup_logging(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The verified dataset identifier (as per the project plan)
DEFAULT_DATASET_ID = "code-search-net/python"
# Number of examples to download for the test shard
TEST_SHARD_SIZE = 10

# Helper to support both the original single‑argument API and the
# multi‑argument usage expected by the unit tests.
def _resolve_data_path(*parts: str) -> Path:
    """
    Resolve a data path using ``get_data_path`` if it supports the given
    signature; otherwise fall back to ``get_path`` with the parts joined.
    """
    try:
        # Attempt to call the original function with the provided parts.
        return get_data_path(*parts)  # type: ignore[arg-type]
    except TypeError:
        # The real ``get_data_path`` accepts a single filename; join the
        # parts manually and use ``get_path`` which works with a single
        # relative path string.
        combined = os.path.join(*parts)
        return get_path(combined)

# Output files
CHECKSUMS_FILE = _resolve_data_path("checksums.txt")
TEST_SHARD_FILE = _resolve_data_path("raw", "test_shard.jsonl")

def download_test_shard(dataset_id: str = DEFAULT_DATASET_ID,
                       shard_size: int = TEST_SHARD_SIZE) -> Path:
    """
    Streams a small number of examples from the dataset and writes them to a
    JSON‑Lines file.

    Returns:
        Path to the written JSON‑Lines file.
    """
    logger.info(
        f"Downloading a test shard ({shard_size} examples) from dataset '{dataset_id}'"
    )
    # Use streaming mode to avoid downloading the full dataset
    ds = load_dataset(dataset_id, split="train", streaming=True)

    # Ensure the target directory exists
    output_path = Path(TEST_SHARD_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the first ``shard_size`` examples to a file
    with output_path.open("w", encoding="utf-8") as f:
        for i, item in enumerate(ds):
            if i >= shard_size:
                break
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + "\n")

    logger.info(f"Test shard written to {output_path}")
    return output_path

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA‑256 checksum of the given file.

    Returns:
        Hexadecimal digest string.
    """
    logger.info(f"Computing SHA‑256 checksum for {file_path}")
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    logger.info(f"Checksum: {checksum}")
    return checksum

def write_checksum_record(dataset_id: str, checksum: str, output_path: Path) -> None:
    """
    Writes a single line record to ``checksums.txt`` in the format:

        <dataset_id>  <checksum>

    The file is created (or overwritten) each time the script runs.
    """
    logger.info(f"Recording checksum in {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"{dataset_id}  {checksum}\\n")
    logger.info("Checksum record written successfully")

def main() -> None:
    """
    Entry point: verify dataset, download shard, compute checksum, write record.
    """
    try:
        shard_path = download_test_shard()
        checksum = compute_sha256(shard_path)
        write_checksum_record(DEFAULT_DATASET_ID, checksum, CHECKSUMS_FILE)
        logger.info("Dataset verification completed successfully")
    except Exception as e:
        logger.error(f"Dataset verification failed: {e}")
        # Re‑raise to ensure the pipeline aborts
        raise

if __name__ == "__main__":
    main()
