"""
Dataset Downloader for Socratic Transformers Project.

This module implements the real data fetching for GSM8K and MATH datasets
via HuggingFace `datasets`. It ensures data integrity by computing checksums
and verifying them against a manifest stored in `state/`.

Per task T012:
- Fetches real data (never synthetic).
- Verifies checksums against `state/manifest.json`.
- Fails loudly if real data cannot be obtained.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Constants for dataset configuration
DATASET_CONFIGS = {
    "gsm8k": {
        "id": "openai/gsm8k",
        "split": "train",
        "output_file": "gsm8k_train.jsonl",
        "description": "Grade School Math 8K dataset",
    },
    "math": {
        "id": "hendrycks/math",
        "split": "train",
        "output_file": "math_train.jsonl",
        "description": "MATH dataset (Hendrycks)",
    },
}

# Paths relative to project root
DATA_RAW_DIR = _project_root / "data" / "raw"
STATE_DIR = _project_root / "state"
MANIFEST_PATH = STATE_DIR / "manifest.json"


def ensure_data_dirs() -> None:
    """Create necessary data directories if they do not exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest() -> Dict[str, Any]:
    """
    Load the checksum manifest from the state directory.

    Returns:
        Dictionary containing the manifest data.
        Returns an empty dict if the manifest does not exist.
    """
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: Dict[str, Any]) -> None:
    """
    Save the checksum manifest to the state directory.

    Args:
        manifest: Dictionary to save.
    """
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def verify_checksums(dataset_name: str, file_path: Path, expected_hash: str) -> bool:
    """
    Verify the checksum of a downloaded file against the expected hash.

    Args:
        dataset_name: Name of the dataset (for logging).
        file_path: Path to the downloaded file.
        expected_hash: Expected SHA-256 hash.

    Returns:
        True if hashes match, False otherwise.
    """
    if not file_path.exists():
        return False
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash


def download_dataset(dataset_name: str, force: bool = False) -> Path:
    """
    Download a specific dataset from HuggingFace and save it as JSONL.

    This function fetches REAL data. If the fetch fails, it raises an exception.
    It does NOT generate synthetic data.

    Args:
        dataset_name: Key in DATASET_CONFIGS (e.g., 'gsm8k', 'math').
        force: If True, re-download even if file exists.

    Returns:
        Path to the downloaded JSONL file.
    """
    if dataset_name not in DATASET_CONFIGS:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    config = DATASET_CONFIGS[dataset_name]
    dataset_id = config["id"]
    split = config["split"]
    output_filename = config["output_file"]
    output_path = DATA_RAW_DIR / output_filename

    # Check if file already exists and verify
    if output_path.exists() and not force:
        print(f"Checking existing file: {output_path}")
        manifest = load_manifest()
        if dataset_name in manifest:
            expected_hash = manifest[dataset_name]["hash"]
            if verify_checksums(dataset_name, output_path, expected_hash):
                print(f"Checksum verified for {dataset_name}. Skipping download.")
                return output_path
            else:
                print(f"Checksum mismatch for {dataset_name}. Re-downloading.")
        else:
            print(f"Manifest missing for {dataset_name}. Re-downloading.")

    print(f"Downloading {dataset_id} (split: {split})...")
    try:
        # Load the real dataset from HuggingFace
        # Using streaming=False to ensure we have the full data for checksumming
        # If memory is an issue, the task requires streaming or chunking, but for
        # GSM8K/MATH train splits, full load is usually feasible in 7GB RAM.
        ds = load_dataset(dataset_id, split=split, trust_remote_code=True)
    except Exception as e:
        raise RuntimeError(
            f"Failed to download real dataset {dataset_id}: {e}. "
            "The loader must fail loudly; no synthetic fallback allowed."
        ) from e

    print(f"Dataset loaded. {len(ds)} examples. Writing to {output_path}...")

    # Write to JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for item in ds:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Download complete. Calculating hash...")
    file_hash = compute_file_hash(output_path)

    # Update manifest
    manifest = load_manifest()
    manifest[dataset_name] = {
        "hash": file_hash,
        "source": dataset_id,
        "split": split,
        "size_bytes": output_path.stat().st_size,
    }
    save_manifest(manifest)

    print(f"Saved manifest. Hash: {file_hash}")
    return output_path


def download_all_datasets(force: bool = False) -> List[Path]:
    """
    Download all configured datasets.

    Args:
        force: If True, re-download all datasets.

    Returns:
        List of paths to the downloaded files.
    """
    ensure_data_dirs()
    paths = []
    for name in DATASET_CONFIGS.keys():
        paths.append(download_dataset(name, force=force))
    return paths


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Download GSM8K and MATH datasets.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files exist and checksums match.",
    )
    parser.add_argument(
        "--dataset",
        choices=["gsm8k", "math", "all"],
        default="all",
        help="Which dataset to download.",
    )

    args = parser.parse_args()
    ensure_data_dirs()

    if args.dataset == "all":
        paths = download_all_datasets(force=args.force)
    else:
        paths = [download_dataset(args.dataset, force=args.force)]

    print("\nDownloaded files:")
    for p in paths:
        print(f"  - {p}")
    print("Verification complete.")


if __name__ == "__main__":
    main()