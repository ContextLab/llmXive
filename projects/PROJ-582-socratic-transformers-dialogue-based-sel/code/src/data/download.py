"""
Dataset Downloader for Socratic Transformers Project.

Fetches GSM8K and MATH datasets from HuggingFace Datasets.
Implements checksum verification against a manifest in the state/ directory.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from datasets import load_dataset
from src.utils.config import get_config, SocraticConfig

# Constants for dataset identification
DATASET_CONFIGS = {
    "gsm8k": {
        "name": "gsm8k",
        "config": "main",
        "splits": ["train", "test"],
        "output_file": "gsm8k_full.jsonl"
    },
    "math": {
        "name": "hendrycks/math",
        "config": "all",
        "splits": ["train", "test"],
        "output_file": "math_full.jsonl"
    }
}

def ensure_data_dirs(config: SocraticConfig) -> None:
    """Ensure the required data directories exist."""
    dirs = [
        config.data_raw_dir,
        config.data_processed_dir,
        config.data_results_dir,
        config.state_dir
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _load_manifest(state_dir: Path) -> Dict[str, str]:
    """Load the checksum manifest if it exists."""
    manifest_path = state_dir / "dataset_checksums.json"
    if not manifest_path.exists():
        return {}
    with open(manifest_path, "r") as f:
        return json.load(f)

def _save_manifest(state_dir: Path, checksums: Dict[str, str]) -> None:
    """Save the checksum manifest."""
    manifest_path = state_dir / "dataset_checksums.json"
    with open(manifest_path, "w") as f:
        json.dump(checksums, f, indent=2)

def _verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify the file checksum matches the expected hash."""
    if not expected_hash:
        return False
    actual_hash = _compute_file_hash(file_path)
    return actual_hash == expected_hash

def download_dataset(
    dataset_key: str,
    config_obj: SocraticConfig,
    force_redownload: bool = False
) -> Path:
    """
    Download a specific dataset from HuggingFace and save it as JSONL.

    Args:
        dataset_key: Key in DATASET_CONFIGS (e.g., 'gsm8k', 'math')
        config_obj: Project configuration object
        force_redownload: If True, skip existing files and re-download

    Returns:
        Path to the downloaded file

    Raises:
        ValueError: If dataset_key is invalid
        RuntimeError: If checksum verification fails after download
    """
    if dataset_key not in DATASET_CONFIGS:
        raise ValueError(f"Unknown dataset key: {dataset_key}. Valid keys: {list(DATASET_CONFIGS.keys())}")

    dataset_info = DATASET_CONFIGS[dataset_key]
    dataset_name = dataset_info["name"]
    dataset_config = dataset_info["config"]
    splits = dataset_info["splits"]
    output_filename = dataset_info["output_file"]

    output_path = config_obj.data_raw_dir / output_filename
    manifest = _load_manifest(config_obj.state_dir)
    expected_hash = manifest.get(output_filename, "")

    # Check if file exists and is valid
    if not force_redownload and output_path.exists():
        if expected_hash:
            if _verify_checksum(output_path, expected_hash):
                print(f"Dataset {dataset_name} already downloaded and verified: {output_path}")
                return output_path
            else:
                print(f"Checksum mismatch for {output_filename}. Redownloading...")
        else:
            print(f"Dataset {dataset_name} exists but no checksum in manifest. Redownloading to ensure integrity.")

    print(f"Downloading dataset: {dataset_name} (config: {dataset_config})...")
    try:
        # Load dataset from HuggingFace
        ds = load_dataset(dataset_name, dataset_config)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {dataset_name}: {e}")

    # Combine splits into a single JSONL file
    all_records = []
    for split in splits:
        if split not in ds:
            print(f"Warning: Split '{split}' not found in {dataset_name}. Skipping.")
            continue
        split_data = ds[split]
        # Convert to list of dicts
        for i, item in enumerate(split_data):
            # Add metadata about origin
            item["_source_dataset"] = dataset_name
            item["_source_split"] = split
            item["_source_index"] = i
            all_records.append(item)

    print(f"Writing {len(all_records)} records to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Compute and save checksum
    actual_hash = _compute_file_hash(output_path)
    manifest[output_filename] = actual_hash
    _save_manifest(config_obj.state_dir, manifest)

    print(f"Download complete. Saved to {output_path} (SHA256: {actual_hash})")
    return output_path

def download_all_datasets(config: Optional[SocraticConfig] = None, force_redownload: bool = False) -> List[Path]:
    """
    Download all configured datasets.

    Args:
        config: Project configuration. If None, loads default.
        force_redownload: If True, re-download all datasets.

    Returns:
        List of paths to downloaded files.
    """
    if config is None:
        config = get_config()

    ensure_data_dirs(config)

    downloaded_paths = []
    for key in DATASET_CONFIGS:
        try:
            path = download_dataset(key, config, force_redownload)
            downloaded_paths.append(path)
        except Exception as e:
            print(f"Error downloading {key}: {e}", file=sys.stderr)
            # Continue with other datasets rather than failing completely
            continue

    return downloaded_paths

def main():
    """CLI entry point for dataset download."""
    import argparse

    parser = argparse.ArgumentParser(description="Download datasets for Socratic Transformers project")
    parser.add_argument(
        "--dataset",
        choices=["gsm8k", "math", "all"],
        default="all",
        help="Which dataset to download"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files exist"
    )

    args = parser.parse_args()
    config = get_config()

    if args.dataset == "all":
        paths = download_all_datasets(config, force_redownload=args.force)
    else:
        path = download_dataset(args.dataset, config, force_redownload=args.force)
        paths = [path]

    if paths:
        print(f"\nSuccessfully downloaded {len(paths)} dataset(s):")
        for p in paths:
            print(f"  - {p}")
    else:
        print("\nNo datasets were downloaded.")
        sys.exit(1)

if __name__ == "__main__":
    main()
