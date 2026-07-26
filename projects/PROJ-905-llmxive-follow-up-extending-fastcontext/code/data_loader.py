"""
Data Loader for SWE-bench Lite.

This module handles downloading and verifying the SWE-bench Lite dataset
from HuggingFace datasets.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add the code directory to the path to allow relative imports if running as script
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_path, ensure_directories

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )


def compute_file_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verifies the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.
        expected_hash: Expected SHA-256 hash.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_file_sha256(file_path)
    return actual_hash == expected_hash


def download_dataset(
    dataset_name: str = "princeton-nlp/SWE-bench_Lite",
    split: str = "test",
    revision: str = "main",
    cache_dir: Optional[Path] = None
) -> Any:
    """
    Downloads and loads the SWE-bench Lite dataset.

    This function ensures the dataset is downloaded (or loaded from cache)
    and returns the dataset object for the specified split.

    Args:
        dataset_name: The HuggingFace dataset identifier.
        split: The dataset split to load (default: 'test').
        revision: The git revision to load (default: 'main').
        cache_dir: Optional cache directory for the dataset.

    Returns:
        The loaded dataset object (Dataset or DatasetDict).

    Raises:
        FileNotFoundError: If the dataset cannot be downloaded or loaded.
        ValueError: If the dataset structure is unexpected.
    """
    try:
        # Load the dataset from HuggingFace
        # The datasets library handles caching automatically
        dataset = load_dataset(
            dataset_name,
            split=split,
            revision=revision,
            cache_dir=str(cache_dir) if cache_dir else None
        )
        
        # Verify that the dataset contains expected fields
        if len(dataset) == 0:
            raise ValueError(f"Dataset '{dataset_name}' split '{split}' is empty.")
        
        # Check for key fields expected in SWE-bench Lite
        expected_fields = ["repo", "instance_id", "problem_statement"]
        sample_row = dataset[0]
        missing_fields = [f for f in expected_fields if f not in sample_row]
        
        if missing_fields:
            raise ValueError(
                f"Dataset '{dataset_name}' is missing expected fields: {missing_fields}"
            )
        
        return dataset
        
    except Exception as e:
        raise FileNotFoundError(
            f"Failed to download or load dataset '{dataset_name}' split '{split}'. "
            f"Ensure internet connectivity and valid HuggingFace credentials. "
            f"Error: {e}"
        )


def main():
    """
    Main entry point for the data loader script.
    Downloads the dataset and prints basic statistics.
    """
    print("Starting dataset download for SWE-bench Lite...")
    
    try:
        dataset = download_dataset()
        
        print(f"Successfully loaded dataset: {dataset}")
        print(f"Number of examples: {len(dataset)}")
        print(f"Columns: {dataset.column_names}")
        
        # Show a sample row
        if len(dataset) > 0:
            sample = dataset[0]
            print("\nSample row:")
            for key, value in sample.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
        
        print("Task T007 completed.")
        
    except Exception as e:
        print(f"Error during download: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
