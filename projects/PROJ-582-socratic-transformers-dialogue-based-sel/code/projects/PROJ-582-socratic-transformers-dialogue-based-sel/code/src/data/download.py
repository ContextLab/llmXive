"""
Dataset Downloader for Socratic Transformers Project.

This module handles the downloading and verification of the GSM8K and MATH datasets
from HuggingFace, ensuring data integrity via checksums against a manifest.

Dependencies: datasets, hashlib, json, pathlib, typing
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import config to get paths if needed, though we rely on relative paths here
# from src.utils.config import get_config

# Ensure the script can be run from the project root
# If running as a module, adjust sys.path if necessary
if 'projects/PROJ-582-socratic-transformers-dialogue-based-sel/code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datasets import load_dataset


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"


def ensure_data_dirs() -> None:
    """Ensure required directories exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest() -> Dict[str, Any]:
    """Load the checksum manifest from state/manifest.json."""
    manifest_path = STATE_DIR / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}. "
                                "Run T010 (verify_datasets.py) first to create it.")
    with open(manifest_path, "r") as f:
        return json.load(f)


def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the checksum manifest to state/manifest.json."""
    manifest_path = STATE_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def verify_checksums(dataset_name: str, local_path: Path) -> bool:
    """
    Verify the local dataset cache against the manifest.
    Returns True if checksums match, False otherwise.
    """
    manifest = load_manifest()
    if dataset_name not in manifest:
        raise ValueError(f"Dataset {dataset_name} not found in manifest. "
                         "Run T010 to register it.")

    expected_hash = manifest[dataset_name]["hash"]
    # Note: HuggingFace datasets cache structure can be complex.
    # For this task, we assume the manifest stores the hash of the primary
    # data file or the cache directory hash if implemented in T010.
    # We will attempt to compute hash of the first data file found in the cache
    # to match against the manifest logic established in T010.

    # Since T010 is the source of truth for the manifest, we trust its logic.
    # Here we simply check if the file exists and re-compute hash to compare.
    # If T010 stored a specific file path, we would use that.
    # Assuming T010 registered the cache directory hash or a specific split file.
    # To be robust, we check if the local path exists and matches the expected hash.
    
    if not local_path.exists():
        return False

    # We need to match the logic of T010. T010 likely hashed the downloaded file.
    # We will compute the hash of the local_path (if it's a file) or a representative file.
    # For simplicity in this implementation, assuming local_path is the primary artifact.
    actual_hash = compute_file_hash(local_path) if local_path.is_file() else "dir_hash_placeholder"
    
    # If the manifest stores a directory hash, we can't easily recompute it without
    # iterating all files. We assume T010 stored the hash of the main data file.
    # If local_path is a directory (HuggingFace cache), we look for the main data file.
    if local_path.is_dir():
        # Heuristic: look for 'data-00000-of-00001.arrow' or similar
        data_files = list(local_path.glob("*.arrow")) + list(local_path.glob("*.json"))
        if data_files:
            actual_hash = compute_file_hash(data_files[0])
        else:
            # Fallback: hash the directory structure (not recommended for exact match)
            raise ValueError("Could not find primary data file in cache directory.")

    return actual_hash == expected_hash


def download_dataset(dataset_name: str, split: str = "train") -> Path:
    """
    Download and cache a dataset using HuggingFace datasets.
    Returns the path to the cached dataset.
    """
    print(f"Downloading dataset: {dataset_name} (split: {split})")
    
    # Load dataset (this caches it locally in HF default cache or HF_HOME)
    # We use streaming=False to ensure full download for checksum verification
    ds = load_dataset(dataset_name, split=split, trust_remote_code=True)
    
    # HuggingFace datasets doesn't expose the exact cache path easily in all versions.
    # However, we can save the dataset to a specific path for verification purposes
    # or rely on the fact that T010 registered the hash of the cached version.
    # To make verification robust, we will save the dataset to our data/raw directory
    # in a standard format (Parquet or JSON) to have a deterministic file to hash.
    
    output_dir = DATA_RAW_DIR / dataset_name.split("/")[-1]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{split}.parquet"
    
    ds.to_parquet(str(output_file))
    print(f"Dataset saved to: {output_file}")
    
    return output_file


def download_all_datasets() -> None:
    """Download and verify all required datasets (GSM8K, MATH)."""
    ensure_data_dirs()
    
    datasets_config = [
        {"name": "openai/gsm8k", "config": "main", "split": "train"},
        {"name": "hendrycks/math", "config": "all", "split": "train"} # or 'test' depending on spec
    ]
    
    # Note: T010 should have registered these in the manifest.
    # We download, save to a deterministic location, then verify.
    
    for cfg in datasets_config:
        ds_name = cfg["name"]
        split = cfg["split"]
        
        try:
            file_path = download_dataset(ds_name, split)
            
            # Verify checksum
            # We need to map our local file to the manifest key.
            # The manifest key should be the dataset name.
            # T010 must have stored the hash of the file we are about to create
            # OR we must update the manifest if T010 was a dry-run (unlikely).
            # Assuming T010 already downloaded and hashed, we just verify here.
            # But if T010 only registered the EXPECTED hash from a known source,
            # we compare our download against that.
            
            # For this task, we assume the manifest contains the expected hash
            # for the dataset as downloaded by T010.
            # We verify our download matches.
            if verify_checksums(ds_name, file_path):
                print(f"✓ Checksum verified for {ds_name}")
            else:
                print(f"✗ Checksum MISMATCH for {ds_name}")
                # Fail loudly as per constraints
                raise RuntimeError(f"Data integrity check failed for {ds_name}")
                
        except Exception as e:
            print(f"Error processing {ds_name}: {e}")
            raise


def main():
    """Main entry point for the download script."""
    print("Starting dataset download and verification...")
    try:
        download_all_datasets()
        print("All datasets downloaded and verified successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T010 (verify_datasets.py) has been run to create the manifest.")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()