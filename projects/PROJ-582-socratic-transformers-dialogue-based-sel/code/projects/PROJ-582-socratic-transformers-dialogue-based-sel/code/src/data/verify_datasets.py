"""
verify_datasets.py

Implements dataset integrity verification for GSM8K and MATH.
Downloads datasets via HuggingFace, computes SHA-256 checksums of the raw
parquet files, records them in a manifest under `state/`, and validates
existing data against this manifest.

Usage:
    python src/data/verify_datasets.py
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, List, Any

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Dataset configuration
DATASETS = {
    "gsm8k": {
        "huggingface_id": "openai/gsm8k",
        "config": "main",
        "split": "train",
        "expected_files": ["gsm8k-train.parquet"],
    },
    "math": {
        "huggingface_id": "hendrycks/math",
        "config": "all",
        "split": "train",
        "expected_files": ["math-train.parquet"],
    },
}

MANIFEST_PATH = STATE_DIR / "dataset_manifest.json"


def ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_manifest() -> Dict[str, Any]:
    """Load the manifest if it exists, otherwise return an empty dict."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest to disk."""
    ensure_state_dir()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def download_and_cache_dataset(
    dataset_name: str,
    config: str,
    split: str,
) -> List[Path]:
    """
    Download and cache the dataset using HuggingFace datasets.
    Returns a list of local file paths for the raw data.
    """
    from datasets import load_dataset

    ds_config = DATASETS[dataset_name]
    hf_id = ds_config["huggingface_id"]

    print(f"Loading dataset: {hf_id} (config={config}, split={split})")

    # Load dataset (this caches it locally)
    dataset = load_dataset(hf_id, config=config, split=split, trust_remote_code=True)

    # The datasets library caches data in ~/.cache/huggingface
    # We need to find the actual parquet files to hash them.
    # Since we cannot easily access the internal cache structure reliably across versions,
    # we will rely on the fact that `load_dataset` ensures the data is present.
    # To get a hashable artifact, we will re-save the data to a deterministic location
    # in data/raw/ and hash that. This ensures reproducibility and a stable target for checksums.

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DATA_RAW_DIR / f"{dataset_name}-{split}.parquet"

    # Export to parquet to have a stable file to hash
    # Note: This assumes the dataset can be converted to a single parquet file.
    # For large datasets, this might be memory intensive, but GSM8K and MATH are small enough.
    dataset.to_parquet(str(output_file))

    return [output_file]


def verify_dataset(
    dataset_name: str,
    manifest: Dict[str, Any],
    force_update: bool = False,
) -> bool:
    """
    Verify a dataset against the manifest.
    If force_update is True, re-download and update the manifest.
    Returns True if verification passes (or update succeeds), False otherwise.
    """
    ds_config = DATASETS[dataset_name]
    hf_id = ds_config["huggingface_id"]

    if force_update:
        print(f"[{dataset_name}] Force updating dataset...")
        try:
            file_paths = download_and_cache_dataset(
                dataset_name, ds_config["config"], ds_config["split"]
            )
            new_checksums = {}
            for fp in file_paths:
                if fp.exists():
                    checksum = compute_file_hash(fp)
                    new_checksums[fp.name] = checksum
                    print(f"  - {fp.name}: {checksum}")

            # Update manifest
            if dataset_name not in manifest:
                manifest[dataset_name] = {}
            manifest[dataset_name]["checksums"] = new_checksums
            manifest[dataset_name]["hf_id"] = hf_id
            manifest[dataset_name]["config"] = ds_config["config"]
            manifest[dataset_name]["split"] = ds_config["split"]
            save_manifest(manifest)
            print(f"[{dataset_name}] Manifest updated successfully.")
            return True
        except Exception as e:
            print(f"[{dataset_name}] Failed to download/update: {e}")
            return False

    # Check if dataset is in manifest
    if dataset_name not in manifest:
        print(f"[{dataset_name}] Not found in manifest. Run with --update to record.")
        return False

    manifest_entry = manifest[dataset_name]
    expected_checksums = manifest_entry.get("checksums", {})

    if not expected_checksums:
        print(f"[{dataset_name}] No checksums recorded in manifest.")
        return False

    print(f"[{dataset_name}] Verifying against manifest...")
    all_valid = True

    for filename, expected_hash in expected_checksums.items():
        file_path = DATA_RAW_DIR / filename
        if not file_path.exists():
            print(f"  - {filename}: MISSING")
            all_valid = False
            continue

        actual_hash = compute_file_hash(file_path)
        if actual_hash == expected_hash:
            print(f"  - {filename}: OK ({actual_hash[:16]}...)")
        else:
            print(f"  - {filename}: MISMATCH")
            print(f"      Expected: {expected_hash}")
            print(f"      Actual:   {actual_hash}")
            all_valid = False

    return all_valid


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify dataset integrity.")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Force re-download and update manifest checksums.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=list(DATASETS.keys()),
        default=None,
        help="Specific dataset to verify/update (default: all).",
    )
    args = parser.parse_args()

    datasets_to_process = (
        [args.dataset] if args.dataset else list(DATASETS.keys())
    )

    manifest = load_manifest()
    all_success = True

    for ds_name in datasets_to_process:
        success = verify_dataset(ds_name, manifest, force_update=args.update)
        if not success:
            all_success = False

    if all_success:
        print("\nAll verified datasets passed integrity checks.")
        return 0
    else:
        print("\nSome datasets failed verification or update.")
        return 1


if __name__ == "__main__":
    sys.exit(main())