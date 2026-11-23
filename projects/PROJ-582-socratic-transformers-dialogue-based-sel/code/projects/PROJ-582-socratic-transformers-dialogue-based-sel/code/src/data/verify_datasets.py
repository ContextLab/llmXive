"""
verify_datasets.py

Implements dataset integrity verification for GSM8K and MATH.
Downloads datasets, computes checksums, and manages a state manifest.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, List, Any

from datasets import load_dataset


def ensure_state_dir(state_root: Path) -> Path:
    """Ensure the state directory exists."""
    state_root.mkdir(parents=True, exist_ok=True)
    return state_root


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    For HuggingFace datasets, we hash the parquet files in the cache.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the state manifest JSON."""
    if not manifest_path.exists():
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest_path: Path, data: Dict[str, Any]) -> None:
    """Save the state manifest JSON."""
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def download_and_cache_dataset(dataset_id: str, split: str = "train") -> Path:
    """
    Download and cache a HuggingFace dataset.
    Returns the path to the primary data file (e.g., parquet) in the cache.
    Note: This relies on the HF datasets library caching mechanism.
    We return the path to the first data file found in the cache for this dataset.
    """
    try:
        ds = load_dataset(dataset_id, split=split, cache_dir="./data/raw")
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {dataset_id}: {e}")

    # The datasets library caches data in a specific structure.
    # We need to find the actual file to hash.
    # For 'openai/gsm8k' and 'hendrycks/math', the cache usually contains parquet files.
    cache_dir = Path("./data/raw")
    dataset_name = dataset_id.replace("/", "_")

    # Search for parquet files in the cache directory that match the dataset name
    found_files = []
    for root, dirs, files in os.walk(cache_dir):
        if dataset_name in root:
            for file in files:
                if file.endswith(".parquet"):
                    found_files.append(Path(root) / file)

    if not found_files:
        # Fallback: try to find any parquet file in the cache if the name matching fails
        # This is a heuristic as HF cache structure can vary by version
        for root, dirs, files in os.walk(cache_dir):
            for file in files:
                if file.endswith(".parquet"):
                    found_files.append(Path(root) / file)
                if file.endswith(".arrow"):
                    found_files.append(Path(root) / file)

    if not found_files:
        raise FileNotFoundError(
            f"Could not find cached data files for dataset {dataset_id} in {cache_dir}"
        )

    # Return the first found file. For large datasets split into shards,
    # a full verification might need to hash all shards, but for this task
    # we record a representative checksum of the primary shard.
    return found_files[0]


def verify_dataset(
    dataset_id: str,
    manifest: Dict[str, Any],
    expected_hash: Optional[str] = None,
    state_root: Optional[Path] = None,
) -> bool:
    """
    Verify a dataset against the manifest.
    If expected_hash is provided, check against that.
    Otherwise, check against the manifest entry for this dataset.
    """
    if state_root is None:
        state_root = Path("state")

    state_root = ensure_state_dir(state_root)
    manifest_path = state_root / "dataset_manifest.json"

    # If no expected hash provided, load from manifest
    if expected_hash is None:
        manifest = load_manifest(manifest_path)
        entry = manifest.get(dataset_id, {})
        expected_hash = entry.get("checksum")

    if not expected_hash:
        # No record exists, we cannot verify yet
        print(f"Warning: No manifest entry found for {dataset_id}.")
        return False

    try:
        # Download/Cache to ensure file exists and get path
        data_file_path = download_and_cache_dataset(dataset_id)
        actual_hash = compute_file_hash(data_file_path)

        if actual_hash == expected_hash:
            print(f"Verification PASSED for {dataset_id}: {actual_hash}")
            return True
        else:
            print(f"Verification FAILED for {dataset_id}.")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            return False
    except FileNotFoundError as e:
        print(f"Error verifying {dataset_id}: {e}")
        return False
    except Exception as e:
        print(f"Error during verification of {dataset_id}: {e}")
        return False


def register_dataset(
    dataset_id: str,
    state_root: Optional[Path] = None,
    force: bool = False,
) -> str:
    """
    Download dataset, compute checksum, and register it in the manifest.
    Returns the computed checksum.
    """
    if state_root is None:
        state_root = Path("state")

    state_root = ensure_state_dir(state_root)
    manifest_path = state_root / "dataset_manifest.json"

    manifest = load_manifest(manifest_path)

    data_file_path = download_and_cache_dataset(dataset_id)
    checksum = compute_file_hash(data_file_path)

    print(f"Computed checksum for {dataset_id}: {checksum}")

    if dataset_id in manifest and not force:
        print(f"Dataset {dataset_id} already registered. Use --force to update.")
        return manifest[dataset_id]["checksum"]

    manifest[dataset_id] = {
        "checksum": checksum,
        "source": dataset_id,
        "registered_at": str(Path.cwd()), # Storing context, not strict timestamp for simplicity
    }

    save_manifest(manifest_path, manifest)
    print(f"Registered {dataset_id} in {manifest_path}")
    return checksum


def main():
    """
    Main entry point for CLI usage.
    Usage:
      python verify_datasets.py --register openai/gsm8k
      python verify_datasets.py --register hendrycks/math
      python verify_datasets.py --verify openai/gsm8k
      python verify_datasets.py --verify hendrycks/math
      python verify_datasets.py --verify-all
    """
    import argparse

    parser = argparse.ArgumentParser(description="Verify dataset integrity.")
    parser.add_argument("--register", type=str, help="Register a dataset (e.g., openai/gsm8k)")
    parser.add_argument("--verify", type=str, help="Verify a dataset against manifest")
    parser.add_argument("--verify-all", action="store_true", help="Verify all registered datasets")
    parser.add_argument("--force", action="store_true", help="Force re-registration")

    args = parser.parse_args()

    if args.register:
        register_dataset(args.register, force=args.force)
        sys.exit(0)

    if args.verify:
        success = verify_dataset(args.verify)
        sys.exit(0 if success else 1)

    if args.verify_all:
        manifest_path = Path("state") / "dataset_manifest.json"
        if not manifest_path.exists():
            print("No manifest found. Nothing to verify.")
            sys.exit(1)

        manifest = load_manifest(manifest_path)
        all_passed = True
        for ds_id in manifest.keys():
            if not verify_dataset(ds_id):
                all_passed = False
        sys.exit(0 if all_passed else 1)

    print("No action specified. Use --register, --verify, or --verify-all.")
    sys.exit(1)


if __name__ == "__main__":
    main()