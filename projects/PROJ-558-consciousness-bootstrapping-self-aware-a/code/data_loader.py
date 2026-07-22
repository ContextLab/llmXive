import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datasets import load_dataset

from utils.logging import get_logger, DataLoadError

logger = get_logger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "manifest.json"

def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load existing manifest or return empty structure."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save manifest to disk."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def fetch_arxiv_pile_truncated() -> Path:
    """
    Fetch the 'arxiv' subset of The Pile dataset.
    Note: This function is already implemented in T004.
    It is included here for API completeness if needed by external callers.
    """
    logger.info("Fetching Pile arxiv subset (implementation from T004)...")
    # Placeholder for T004 implementation logic if called directly
    # In a real scenario, this would be fully implemented in T004.
    raise NotImplementedError("This function is handled by T004 implementation.")

def fetch_gsm8k() -> Path:
    """
    Fetch the GSM8K dataset via HuggingFace datasets API.
    Saves to data/raw/gsm8k.json.
    Returns the path to the saved file.
    """
    logger.info("Fetching GSM8K dataset...")
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
    except Exception as e:
        raise DataLoadError(f"Failed to load GSM8K dataset from HuggingFace: {e}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / "gsm8k.json"

    # Convert to list of dicts and save as JSON
    data_list = dataset.to_list()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=2)

    logger.info(f"GSM8K dataset saved to {output_path}")
    return output_path

def fetch_mmlu() -> Path:
    """
    Fetch the MMLU dataset via HuggingFace datasets API.
    Saves to data/raw/mmlu.json.
    Returns the path to the saved file.
    """
    logger.info("Fetching MMLU dataset...")
    try:
        # MMLU is a large dataset; we fetch the 'auxiliary_train' or 'test' split.
        # The task requires evaluation data, so we fetch the 'test' split if available,
        # or 'validation' if test is hidden (some HF datasets hide test).
        # Standard mmlu dataset on HF usually has 'test', 'validation', 'train', 'auxiliary_train'.
        # We will fetch 'test' for evaluation.
        dataset = load_dataset("cais/mmlu", split="test")
    except Exception as e:
        raise DataLoadError(f"Failed to load MMLU dataset from HuggingFace: {e}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / "mmlu.json"

    # Convert to list of dicts and save as JSON
    data_list = dataset.to_list()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=2)

    logger.info(f"MMLU dataset saved to {output_path}")
    return output_path

def save_dataset_and_manifest(dataset_name: str, file_path: Path, data_type: str) -> None:
    """
    Update the manifest with the new dataset information.
    """
    manifest = load_manifest()
    checksum = compute_checksum(file_path)
    size_bytes = file_path.stat().st_size
    timestamp = data_path_str(file_path) # Helper to get timestamp or just use current time
    from datetime import datetime
    created_at = datetime.now().isoformat()

    manifest[dataset_name] = {
        "type": data_type,
        "checksum": checksum,
        "size_bytes": size_bytes,
        "created_at": created_at
    }
    save_manifest(manifest)
    logger.info(f"Manifest updated for {dataset_name}")

def data_path_str(path: Path) -> str:
    # Helper to ensure path string is handled if needed, though not strictly used in logic above
    return str(path)

def main():
    """
    Main entry point to fetch evaluation datasets (GSM8K and MMLU) and update manifest.
    """
    logger.info("Starting data loader for evaluation datasets (T004b)...")
    
    try:
        # Fetch GSM8K
        gsm8k_path = fetch_gsm8k()
        save_dataset_and_manifest("gsm8k.json", gsm8k_path, "evaluation")

        # Fetch MMLU
        mmlu_path = fetch_mmlu()
        save_dataset_and_manifest("mmlu.json", mmlu_path, "evaluation")

        logger.info("Successfully fetched and saved GSM8K and MMLU datasets.")
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during data loading: {e}")
        raise

if __name__ == "__main__":
    main()
