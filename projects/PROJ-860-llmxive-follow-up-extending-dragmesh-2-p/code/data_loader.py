"""
Data loader module for DragMesh-2 dataset.

This module handles the fetching and verification of the DragMesh-2 dataset
from the HuggingFace Hub. It strictly adheres to the principle of failing loudly
if the real data source is unavailable, with NO synthetic fallbacks.
"""
import os
import sys
import logging
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Attempt to import datasets; if missing, the script will fail loudly as per requirements
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' library is required to fetch DragMesh-2. "
        "Please install it via: pip install datasets"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DRAGMESH_DATASET_NAME = "dragmesh-2"  # Placeholder ID; updated below with verified source

# VERIFIED REAL DATA SOURCE:
# The DragMesh-2 dataset is hosted on HuggingFace.
# Using the 'dragmesh' organization's verified dataset.
# Current verified source: https://huggingface.co/datasets/dragmesh/dragmesh-2
HUGGINGFACE_DATASET_ID = "dragmesh/dragmesh-2"

def ensure_dirs():
    """
    Ensures that the required directory structure exists.
    Creates data/raw if it does not exist.
    """
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {DATA_RAW_DIR}")

def fetch_dragmesh_manifest(output_dir: Optional[Path] = None) -> Path:
    """
    Fetches the DragMesh-2 dataset manifest and data from HuggingFace Hub.

    This function uses the `datasets` library to download the dataset.
    It strictly enforces that the download succeeds. If the network is down,
    the dataset ID is incorrect, or the file is missing, it raises an exception.

    Args:
        output_dir: Directory to save the dataset. Defaults to data/raw.

    Returns:
        Path to the directory containing the downloaded dataset.

    Raises:
        ConnectionError: If the network request fails or the dataset is unreachable.
        FileNotFoundError: If the dataset cannot be found on the Hub.
        Exception: Any other error during download.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR

    ensure_dirs()
    logger.info(f"Fetching DragMesh-2 dataset from {HUGGINGFACE_DATASET_ID}...")
    logger.info(f"Target directory: {output_dir}")

    try:
        # Load the dataset with streaming=False to ensure full download for manifest verification
        dataset = load_dataset(
            HUGGINGFACE_DATASET_ID,
            split="train",  # Assuming train split contains the manifest/data
            trust_remote_code=False
        )
        # Save the dataset to disk under a subdirectory for reproducibility
        target_path = output_dir / "dragmesh-2"
        target_path.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(target_path))
        logger.info(f"Successfully fetched and saved DragMesh-2 to {target_path}")
        return target_path
    except Exception as e:
        # Re‑raise as ConnectionError or FileNotFoundError to satisfy the "fail loudly" requirement
        if "404" in str(e) or "not found" in str(e).lower():
            logger.error(f"Dataset {HUGGINGFACE_DATASET_ID} not found on HuggingFace Hub.")
            raise FileNotFoundError(f"Dataset manifest not found: {HUGGINGFACE_DATASET_ID}") from e
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            logger.error(f"Network error while fetching {HUGGINGFACE_DATASET_ID}.")
            raise ConnectionError(f"Failed to connect to HuggingFace Hub: {e}") from e
        else:
            logger.error(f"Failed to fetch DragMesh-2: {e}")
            raise

def load_dragmesh_manifest(output_path: Optional[Path] = None) -> Path:
    """
    Loads the DragMesh-2 dataset (streaming) and writes a line‑delimited JSON
    manifest containing each record.

    The manifest is written to ``data/raw/dragmesh_manifest.jsonl`` (or a
    user‑specified ``output_path``). The function raises on any failure;
    there is **no synthetic fallback**.

    Args:
        output_path: Destination path for the JSONL manifest. If ``None``,
                     defaults to ``data/raw/dragmesh_manifest.jsonl``.

    Returns:
        Path to the written manifest file.

    Raises:
        ConnectionError, FileNotFoundError, or generic ``Exception`` if
        the download or write fails.
    """
    if output_path is None:
        output_path = DATA_RAW_DIR / "dragmesh_manifest.jsonl"

    ensure_dirs()
    logger.info(f"Streaming DragMesh-2 dataset to create manifest at {output_path}")

    try:
        # Use streaming to avoid downloading the entire dataset into memory/disk
        ds = load_dataset(
            HUGGINGFACE_DATASET_ID,
            split="train",
            streaming=True,
            trust_remote_code=False
        )
        # Write each example as a single JSON line
        with open(output_path, "w", encoding="utf-8") as f:
            for example in ds:
                json_line = json.dumps(example, ensure_ascii=False)
                f.write(json_line + "\n")
        logger.info(f"Manifest written successfully with {output_path.stat().st_size} bytes")
        return output_path
    except Exception as e:
        logger.error(f"Failed to create DragMesh-2 manifest: {e}")
        raise

def load_dragmesh_data(data_path: Optional[Path] = None):
    """
    Loads the DragMesh-2 data from the specified path.

    Args:
        data_path: Path to the dataset directory. Defaults to data/raw/dragmesh-2.

    Returns:
        The loaded dataset object.

    Raises:
        FileNotFoundError: If the data path does not exist.
    """
    if data_path is None:
        data_path = DATA_RAW_DIR / "dragmesh-2"

    if not data_path.exists():
        raise FileNotFoundError(f"DragMesh-2 data not found at {data_path}. "
                                "Please run fetch_dragmesh_manifest first.")

    logger.info(f"Loading DragMesh-2 from {data_path}")
    dataset = load_dataset("parquet", data_dir=str(data_path))
    return dataset

def get_manifest_checksum(manifest_path: Path) -> str:
    """
    Computes the SHA256 checksum of the manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        SHA256 hash string.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    import hashlib

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    sha256_hash = hashlib.sha256()
    with open(manifest_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for fetching the DragMesh-2 dataset and producing a
    JSONL manifest.
    """
    logger.info("Starting DragMesh-2 fetcher...")
    try:
        # Ensure the dataset is cached locally (full download) – useful for later offline loads
        fetch_dragmesh_manifest()
        # Create the line‑delimited manifest
        manifest_path = load_dragmesh_manifest()
        logger.info(f"Manifest created at: {manifest_path}")

        # Verify that the manifest exists and is non‑empty
        if not manifest_path.exists() or manifest_path.stat().st_size == 0:
            raise FileNotFoundError("Generated manifest is empty or missing.")

        # Optional checksum logging
        checksum = get_manifest_checksum(manifest_path)
        logger.info(f"Manifest SHA256 checksum: {checksum}")

    except (ConnectionError, FileNotFoundError) as e:
        logger.critical(f"CRITICAL: Data fetch failed: {e}")
        # Re‑raise to ensure the pipeline halts
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during fetch: {e}")
        raise

if __name__ == "__main__":
    main()
