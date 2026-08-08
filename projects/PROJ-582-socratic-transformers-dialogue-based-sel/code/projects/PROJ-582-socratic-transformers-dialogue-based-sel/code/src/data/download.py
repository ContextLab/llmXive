import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset
from src.utils.config import get_config, SocraticConfig


def ensure_data_dirs() -> Path:
    """Ensure the data/raw directory exists."""
    config = get_config()
    data_dir = config.data_dir / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksums(manifest_path: Path, data_dir: Path) -> bool:
    """Verify that downloaded files match the expected checksums in the manifest."""
    if not manifest_path.exists():
        # If no manifest exists, we cannot verify, but we proceed (first run)
        return True

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    all_valid = True
    for dataset_name, info in manifest.items():
        expected_hash = info.get("sha256")
        file_name = info.get("file_name")
        if not file_name:
            continue

        file_path = data_dir / file_name
        if not file_path.exists():
            print(f"Warning: {file_name} not found for {dataset_name}.")
            all_valid = False
            continue

        actual_hash = compute_file_hash(file_path)
        if actual_hash != expected_hash:
            print(f"Checksum mismatch for {file_name}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            print(f"Checksum verified for {file_name}")

    return all_valid


def download_dataset(
    dataset_name: str,
    config_name: Optional[str] = None,
    split: str = "train",
    trust_remote_code: bool = True,
    cache_dir: Optional[str] = None,
) -> Path:
    """
    Download a dataset using HuggingFace datasets.
    Returns the path to the downloaded data directory or a processed file.
    """
    data_dir = ensure_data_dirs()
    manifest_path = data_dir.parent.parent / "state" / "download_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing manifest
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    # Construct dataset identifier
    ds_id = f"{dataset_name}"
    if config_name:
        ds_id = f"{dataset_name}/{config_name}"

    print(f"Loading dataset: {ds_id}")
    dataset = load_dataset(
        ds_id,
        split=split,
        trust_remote_code=trust_remote_code,
        cache_dir=cache_dir,
    )

    # Save dataset to parquet for persistence and checksumming
    output_file_name = f"{dataset_name.replace('/', '_')}_{split}.parquet"
    output_path = data_dir / output_file_name

    # If already exists, verify checksum
    if output_path.exists():
        if verify_checksums(manifest_path, data_dir):
            print(f"Dataset {output_file_name} already exists and verified.")
            return output_path

    # Save to parquet
    dataset.to_parquet(str(output_path))

    # Compute hash
    file_hash = compute_file_hash(output_path)

    # Update manifest
    manifest[dataset_name] = {
        "sha256": file_hash,
        "file_name": output_file_name,
        "source": ds_id,
        "split": split,
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Dataset saved to {output_path} with checksum {file_hash}")
    return output_path


def download_all_datasets() -> List[Path]:
    """
    Download all required datasets (GSM8K and MATH) as per project requirements.
    Returns a list of paths to the downloaded files.
    """
    paths = []

    # GSM8K
    try:
        gsm8k_path = download_dataset("gsm8k", config_name="main", split="train")
        paths.append(gsm8k_path)
    except Exception as e:
        print(f"Failed to download GSM8K: {e}")
        # Fail loudly as per constraints

    # MATH
    try:
        # MATH dataset often requires specific handling or config
        math_path = download_dataset("hendrycks/math", split="train")
        paths.append(math_path)
    except Exception as e:
        print(f"Failed to download MATH: {e}")
        # Fail loudly as per constraints

    return paths


def main():
    """Main entry point for dataset download."""
    print("Starting dataset download process...")
    paths = download_all_datasets()
    print(f"Downloaded {len(paths)} datasets successfully.")
    for p in paths:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
