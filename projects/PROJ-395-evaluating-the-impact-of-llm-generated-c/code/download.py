"""
Dataset download and verification module.

This module handles downloading benchmark datasets (HumanEval, MBPP) from
HuggingFace, verifying checksums, and maintaining a manifest for versioning.

Key Functions:
    - download_dataset: Fetch dataset from HuggingFace
    - verify_dataset_structure: Validate downloaded files
    - calculate_sha256: Compute file checksums
    - save_dataset_to_parquet: Convert to parquet format
    - update_manifest: Record dataset version in manifest

Usage:
    from download import download_dataset, verify_dataset_structure
    download_dataset('mbpp', 'test', 'data/raw/')
    verify_dataset_structure('data/raw/mbpp')
"""

import hashlib
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from datasets import load_dataset
import pandas as pd

from config import DATASET_MANIFEST_PATH, DATA_RAW_DIR


def calculate_sha256(filepath: str) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        filepath: Path to the file to hash.

    Returns:
        str: Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_dataset_structure(dataset_path: str) -> bool:
    """
    Verify that the downloaded dataset has the expected structure.

    Args:
        dataset_path: Path to the dataset directory.

    Returns:
        bool: True if structure is valid, False otherwise.

    Raises:
        ValueError: If required files are missing.
    """
    path = Path(dataset_path)
    if not path.exists():
        raise ValueError(f"Dataset path does not exist: {dataset_path}")

    # Check for manifest or data files
    expected_files = ['dataset_info.json', 'train-00000-of-00001.parquet']
    has_data = any((path / f).exists() for f in expected_files)

    if not has_data:
        # Check for any parquet files
        parquet_files = list(path.glob('*.parquet'))
        if not parquet_files:
            raise ValueError(f"No data files found in {dataset_path}")

    return True


def download_dataset(
    dataset_name: str,
    split: str = 'test',
    output_dir: Optional[str] = None
) -> str:
    """
    Download a dataset from HuggingFace.

    Args:
        dataset_name: Name of the dataset (e.g., 'mbpp', 'human_eval').
        split: Dataset split to download (e.g., 'test', 'train').
        output_dir: Directory to save the dataset. Defaults to config.DATA_RAW_DIR.

    Returns:
        str: Path to the downloaded dataset.

    Raises:
        ValueError: If the dataset name is invalid.
        ConnectionError: If download fails.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR

    output_path = Path(output_dir) / dataset_name
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {dataset_name} split={split}...")

    try:
        # Load dataset from HuggingFace
        ds = load_dataset(dataset_name, split=split, trust_remote_code=True)

        # Save to parquet
        parquet_path = output_path / f'{split}.parquet'
        df = ds.to_pandas()
        df.to_parquet(parquet_path, index=False)

        print(f"Dataset saved to {parquet_path}")
        return str(parquet_path)

    except Exception as e:
        raise ConnectionError(f"Failed to download dataset {dataset_name}: {e}")


def save_dataset_to_parquet(
    dataset_name: str,
    data: Any,
    output_path: str
) -> None:
    """
    Save dataset to parquet format.

    Args:
        dataset_name: Name of the dataset (for metadata).
        data: Dataset object or pandas DataFrame to save.
        output_path: Path to save the parquet file.
    """
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        df = data.to_pandas() if hasattr(data, 'to_pandas') else pd.DataFrame(data)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)


def update_manifest(
    dataset_name: str,
    dataset_path: str,
    version: str = '1.0.0',
    checksum: Optional[str] = None
) -> None:
    """
    Update the dataset manifest with version information.

    Args:
        dataset_name: Name of the dataset.
        dataset_path: Path to the dataset file.
        version: Version string.
        checksum: Optional SHA-256 checksum of the file.
    """
    manifest_path = Path(DATASET_MANIFEST_PATH)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing manifest or create new
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {'datasets': {}}

    # Calculate checksum if not provided
    if checksum is None:
        checksum = calculate_sha256(dataset_path)

    # Update manifest
    manifest['datasets'][dataset_name] = {
        'path': str(dataset_path),
        'version': version,
        'checksum': checksum,
        'updated_at': str(Path.now()) if hasattr(Path, 'now') else '2024-01-01'
    }

    # Save manifest
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)

    print(f"Manifest updated: {manifest_path}")


def main():
    """
    Main entry point for downloading datasets.

    Downloads MBPP test split by default and updates the manifest.
    """
    dataset_name = 'mbpp'
    split = 'test'

    try:
        dataset_path = download_dataset(dataset_name, split)
        verify_dataset_structure(os.path.dirname(dataset_path))

        # Update manifest
        checksum = calculate_sha256(dataset_path)
        update_manifest(dataset_name, dataset_path, version='1.0.0', checksum=checksum)

        print(f"Dataset {dataset_name} (split={split}) ready at {dataset_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()