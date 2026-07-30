import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from datasets import load_dataset
from utils.logging import get_logger, DataLoadError

logger = get_logger(__name__)

DATA_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/manifest.json")

def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load the manifest file if it exists."""
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest file."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

def fetch_gsm8k() -> Dict[str, Any]:
    """
    Fetch the GSM8K dataset from HuggingFace and return it as a dictionary.
    This dataset is strictly for EVALUATION.
    """
    logger.info("Fetching GSM8K dataset from HuggingFace...")
    try:
        # GSM8K is a small dataset, loading into memory is fine
        dataset = load_dataset("gsm8k", "main", split="train")
        # Convert to list of dicts for JSON serialization
        data = dataset.to_list()
        logger.info(f"Successfully fetched GSM8K: {len(data)} examples")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch GSM8K: {e}")
        raise DataLoadError(f"Failed to fetch GSM8K dataset: {e}")

def fetch_mmlu() -> Dict[str, Any]:
    """
    Fetch the MMLU dataset from HuggingFace and return it as a dictionary.
    This dataset is strictly for EVALUATION.
    """
    logger.info("Fetching MMLU dataset from HuggingFace...")
    try:
        # MMLU is large, but we load the 'coarse' split or a subset if memory constrained.
        # The task asks for the dataset. We will load the 'test' split of the main dataset.
        # MMLU on HF is often 'cais/mmlu'.
        dataset = load_dataset("cais/mmlu", "all", split="test")
        data = dataset.to_list()
        logger.info(f"Successfully fetched MMLU: {len(data)} examples")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch MMLU: {e}")
        raise DataLoadError(f"Failed to fetch MMLU dataset: {e}")

def save_dataset_and_manifest(
    dataset_name: str,
    data: List[Dict[str, Any]],
    dataset_type: str = "evaluation"
) -> None:
    """
    Save the dataset to JSON and update the manifest with the checksum.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / f"{dataset_name}.json"

    logger.info(f"Saving {dataset_name} to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(data, f)

    checksum = compute_checksum(output_path)
    size_bytes = output_path.stat().st_size
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

    manifest = load_manifest()
    manifest[dataset_name] = {
        "type": dataset_type,
        "checksum": checksum,
        "size_bytes": size_bytes,
        "created_at": timestamp
    }
    save_manifest(manifest)
    logger.info(f"Saved {dataset_name} with checksum {checksum}")

def main():
    """
    Main entry point to fetch GSM8K and MMLU evaluation datasets.
    """
    logger.info("Starting data loading for evaluation datasets (T004b)...")

    # Fetch and save GSM8K
    gsm8k_data = fetch_gsm8k()
    save_dataset_and_manifest("gsm8k", gsm8k_data)

    # Fetch and save MMLU
    mmlu_data = fetch_mmlu()
    save_dataset_and_manifest("mmlu", mmlu_data)

    logger.info("Evaluation datasets loaded and saved successfully.")

if __name__ == "__main__":
    main()
