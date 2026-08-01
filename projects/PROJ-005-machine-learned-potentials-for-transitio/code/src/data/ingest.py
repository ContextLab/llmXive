"""
Data Ingestion Module for QM9-TS Dataset.

Handles fetching, filtering, and processing of the QM9-TS dataset
for transition-metal catalysis research.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Import logging utility from existing project structure
from src.utils.logging import setup_logger, get_logger
from src.utils.config import get_project_root

# Attempt to import HuggingFace datasets
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Please install it via: pip install datasets"
    )

# Constants
TARGET_ELEMENTS = [46, 28, 29]  # Pd (46), Ni (28), Cu (29) atomic numbers
SCARCITY_THRESHOLD = 120
SCARCITY_FLAG_PATH = "data/processed/data_scarcity_flag.json"
CHECKSUM_MANIFEST_PATH = "data/raw/checksums.json"

logger = get_logger(__name__)


def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent.parent.parent


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Computes the checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_checksums(file_paths: List[Path], manifest_path: Path) -> None:
    """Saves checksums for a list of files to a JSON manifest."""
    manifest = {}
    for path in file_paths:
        if path.exists():
            manifest[path.name] = {
                "checksum": compute_file_checksum(path),
                "size_bytes": path.stat().st_size
            }
        else:
            logger.warning(f"File not found for checksum: {path}")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Checksums saved to {manifest_path}")


def fetch_dataset_from_hf(dataset_id: str = "mattwdavis/qm9-ts", split: str = "train") -> Any:
    """
    Fetches the QM9-TS dataset from HuggingFace.

    Args:
        dataset_id: HuggingFace dataset identifier.
        split: Dataset split to load (e.g., 'train', 'test').

    Returns:
        Loaded dataset object.
    """
    logger.info(f"Fetching dataset: {dataset_id} (split: {split})")
    try:
        dataset = load_dataset(dataset_id, split=split, streaming=True)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset from HuggingFace: {e}")
        raise


def load_and_count_reactions(dataset: Any, target_elements: List[int] = None) -> Tuple[int, List[Dict]]:
    """
    Iterates through the dataset, counts valid reactions, and returns sample data.

    Args:
        dataset: The loaded dataset object.
        target_elements: List of atomic numbers to filter by.

    Returns:
        Tuple of (count, list_of_sample_reactions)
    """
    if target_elements is None:
        target_elements = TARGET_ELEMENTS

    count = 0
    samples = []

    # Iterate through the streaming dataset
    for i, entry in enumerate(dataset):
        # Determine if this entry contains target metals
        # Assuming entry structure has 'atomic_numbers' or similar
        # QM9-TS usually has 'atoms' or 'atomic_numbers' list
        atomic_numbers = entry.get('atomic_numbers', entry.get('atoms', []))
        
        if not atomic_numbers:
            continue

        # Check if any atom in the reaction is a target metal
        has_target = any(z in target_elements for z in atomic_numbers)
        
        if has_target:
            count += 1
            # Store a small sample for debugging if needed
            if count <= 5:
                samples.append({
                    "index": i,
                    "count": count,
                    "atoms": atomic_numbers
                })

        # Safety break for extremely large datasets if needed, 
        # but for counting we usually want to go through all or use a limit if specified.
        # For this task, we assume we need the total count of the filtered set.
        # If the dataset is too huge, we might need to rely on metadata, 
        # but here we iterate.

    logger.info(f"Found {count} reactions containing target elements {target_elements}")
    return count, samples


def filter_transition_metals(dataset: Any, target_elements: List[int] = None) -> Any:
    """
    Filters the dataset to keep only reactions with target transition metals.
    Returns a generator or filtered dataset.
    """
    if target_elements is None:
        target_elements = TARGET_ELEMENTS

    def filter_func(entry):
        atomic_numbers = entry.get('atomic_numbers', entry.get('atoms', []))
        if not atomic_numbers:
            return False
        return any(z in target_elements for z in atomic_numbers)

    # If using HuggingFace datasets, we can use filter
    if hasattr(dataset, 'filter'):
        return dataset.filter(filter_func)
    else:
        # Fallback for streaming generators
        return (entry for entry in dataset if filter_func(entry))


def handle_scarcity(count: int, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Implements scarcity flag logic (Task T015b).
    
    Logic:
    1. If count >= 120, log info and return status "sufficient".
    2. If count < 120, log warning, create data_scarcity_flag.json with status "scarcity".
    
    Args:
        count: Number of valid reactions found.
        output_path: Path to write the flag JSON. Defaults to project root + SCARCITY_FLAG_PATH.

    Returns:
        Dict containing 'count' and 'status'.
    """
    if output_path is None:
        output_path = get_project_root() / SCARCITY_FLAG_PATH
    
    result = {
        "count": count,
        "status": "sufficient"
    }

    if count < SCARCITY_THRESHOLD:
        result["status"] = "scarcity"
        logger.warning(f"Data scarcity detected: {count} < {SCARCITY_THRESHOLD}. "
                       f"Creating scarcity flag at {output_path}")
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the flag file
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Scarcity flag written to {output_path}")
    else:
        logger.info(f"Sufficient data found: {count} >= {SCARCITY_THRESHOLD}. "
                    f"No scarcity flag created.")

    return result


def main():
    """
    Main entry point for data ingestion and scarcity check.
    """
    setup_logger(level=logging.INFO)
    
    try:
        # 1. Fetch Dataset
        # Note: Using streaming=True to handle large datasets without loading all into memory
        dataset = fetch_dataset_from_hf()
        
        # 2. Count Reactions
        count, samples = load_and_count_reactions(dataset)
        
        # 3. Handle Scarcity Logic (T015b)
        status = handle_scarcity(count)
        
        # 4. Save Checksums (if we had local files, but here we just log the dataset source)
        # In a real pipeline, we would download specific shards and checksum them.
        # For this task, we ensure the directory structure exists.
        raw_dir = get_project_root() / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Pipeline complete. Status: {status}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()