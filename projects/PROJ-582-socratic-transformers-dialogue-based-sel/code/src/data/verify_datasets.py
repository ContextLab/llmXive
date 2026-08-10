"""
Dataset Verification and Checksum Management for Socratic Transformers Project.

This module handles the recording and validation of checksums for the GSM8K
and MATH datasets to ensure data integrity before processing.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, List, Any

from datasets import load_dataset
from src.utils.config import get_config


# Constants for dataset identifiers
DATASET_IDS = {
    "gsm8k": "openai/gsm8k",
    "math": "hendrycks/math"
}

# Splits to verify for each dataset
DATASET_SPLITS = {
    "gsm8k": ["train", "test"],
    "math": ["train", "test"]
}

# Checksum algorithm
HASH_ALGORITHM = "sha256"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the file hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the existing manifest file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary containing the manifest data.
    """
    if not manifest_path.exists():
        return {}

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest_path: Path, manifest_data: Dict[str, Any]) -> None:
    """
    Save the manifest data to a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.
        manifest_data: Dictionary to save.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)


def verify_dataset(
    dataset_id: str,
    manifest_path: Path,
    update_mode: bool = False
) -> bool:
    """
    Verify a dataset's integrity against the manifest or record its checksum.

    Args:
        dataset_id: The dataset identifier (e.g., 'gsm8k', 'math').
        manifest_path: Path to the manifest file.
        update_mode: If True, record/update checksums. If False, validate against existing.

    Returns:
        True if verification passed or update successful, False otherwise.
    """
    if dataset_id not in DATASET_IDS:
        raise ValueError(f"Unknown dataset_id: {dataset_id}. "
                         f"Available: {list(DATASET_IDS.keys())}")

    source_name = DATASET_IDS[dataset_id]
    splits = DATASET_SPLITS.get(dataset_id, ["train"])
    
    manifest = load_manifest(manifest_path)
    dataset_entry = manifest.get(dataset_id, {})
    current_checksums = dataset_entry.get("checksums", {})

    print(f"Processing dataset: {dataset_id} (source: {source_name})")
    
    # Load dataset
    try:
        dataset = load_dataset(source_name, split=splits)
    except Exception as e:
        print(f"Error loading dataset {source_name}: {e}")
        return False

    # We need to compute a representative hash. Since HuggingFace datasets
    # are loaded into memory/arrow cache, we hash the string representation
    # of the raw data rows for verification purposes in this context.
    # For a production pipeline, one would hash the cached arrow files directly.
    # Here we simulate the integrity check by hashing the JSON representation
    # of the first N rows of each split to ensure data consistency.
    
    new_checksums = {}
    
    # Ensure we have a deterministic sample if the dataset is huge
    # For verification, we hash the entire dataset if small, or a fixed sample
    # to ensure reproducibility without loading everything into a single hash string
    
    for split in splits:
        split_data = dataset[split]
        # Create a deterministic string representation for hashing
        # We iterate through the split and create a hash of the content
        hasher = hashlib.sha256()
        
        # Sample size for hashing to avoid memory issues with huge datasets
        # but maintain integrity check logic
        sample_size = 10000 
        count = 0
        
        for row in split_data:
            if count >= sample_size:
                break
            # Create a deterministic string key for the row
            # Sort keys to ensure consistency
            row_str = json.dumps(dict(row), sort_keys=True)
            hasher.update(row_str.encode('utf-8'))
            count += 1
        
        split_hash = hasher.hexdigest()
        new_checksums[split] = split_hash
        print(f"  - Split '{split}': {count} rows hashed, checksum: {split_hash[:16]}...")

    if update_mode:
        # Update manifest
        manifest[dataset_id] = {
            "source": source_name,
            "checksums": new_checksums,
            "verified_at": "now" # In a real system, use datetime.now().isoformat()
        }
        save_manifest(manifest_path, manifest)
        print(f"Manifest updated for {dataset_id}.")
        return True
    else:
        # Validate against existing
        if not current_checksums:
            print(f"Warning: No existing checksums for {dataset_id} in manifest.")
            return False

        all_match = True
        for split in splits:
            if split not in current_checksums:
                print(f"Mismatch: Split '{split}' missing in manifest for {dataset_id}.")
                all_match = False
                continue
            
            expected = current_checksums[split]
            actual = new_checksums.get(split)
            
            if expected != actual:
                print(f"Mismatch: Split '{split}' for {dataset_id}.")
                print(f"  Expected: {expected}")
                print(f"  Actual:   {actual}")
                all_match = False
            else:
                print(f"OK: Split '{split}' matches manifest.")
        
        return all_match


def main() -> int:
    """
    Main entry point for dataset verification.
    
    Usage:
        python src/data/verify_datasets.py --update  # Record checksums
        python src/data/verify_datasets.py           # Verify checksums
    
    Returns:
        0 on success, 1 on failure.
    """
    config = get_config()
    project_root = Path(config.project_root)
    state_dir = project_root / "state"
    manifest_path = state_dir / "dataset_manifest.json"

    # Check for --update flag
    update_mode = "--update" in sys.argv

    if update_mode:
        print("Running in UPDATE mode: Recording checksums to manifest.")
    else:
        print("Running in VERIFY mode: Validating checksums against manifest.")

    success = True
    
    for dataset_id in DATASET_IDS:
        try:
            result = verify_dataset(dataset_id, manifest_path, update_mode=update_mode)
            if not result:
                success = False
        except Exception as e:
            print(f"Error processing {dataset_id}: {e}")
            success = False

    if success:
        print("\nAll datasets verified successfully." if not update_mode else "\nManifest updated successfully.")
        return 0
    else:
        print("\nVerification failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())