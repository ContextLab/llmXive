"""
Dataset Downloader for Socratic Transformers Project.

Fetches GSM8K and MATH datasets from HuggingFace and verifies checksums
against a manifest stored in the state directory.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure the project root is in the path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is required. Install via: pip install datasets")
    sys.exit(1)

# Project configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
MANIFEST_FILE = STATE_DIR / "dataset_manifest.json"

# Dataset definitions (Name, HuggingFace ID, Split)
DATASETS = {
    "gsm8k": {
        "hf_id": "openai/gsm8k",
        "config": "main",
        "splits": ["train", "test"],
        "output_name": "gsm8k_raw.jsonl"
    },
    "math": {
        "hf_id": "hendrycks/math",
        "config": None, # Uses default or specific subset if needed
        "splits": ["train", "test"],
        "output_name": "math_raw.jsonl"
    }
}

def ensure_data_dirs() -> None:
    """Ensure raw data and state directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load the existing manifest or return an empty dict."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest to disk."""
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def verify_checksums() -> bool:
    """
    Verify checksums of existing data against the manifest.
    Returns True if all verified, False if any mismatch or missing.
    """
    ensure_data_dirs()
    manifest = load_manifest()
    all_valid = True

    for dataset_name, info in manifest.get("datasets", {}).items():
        file_path = DATA_RAW_DIR / info["filename"]
        expected_hash = info["hash"]

        if not file_path.exists():
            print(f"[VERIFY] Missing file: {file_path}")
            all_valid = False
            continue

        actual_hash = compute_file_hash(file_path)
        if actual_hash != expected_hash:
            print(f"[VERIFY] Checksum mismatch for {dataset_name}: "
                  f"expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            print(f"[VERIFY] Checksum OK for {dataset_name}")

    return all_valid

def download_dataset(dataset_name: str, force: bool = False) -> Optional[Path]:
    """
    Download a specific dataset from HuggingFace and save as JSONL.
    Updates the manifest with the new hash.
    """
    ensure_data_dirs()
    config = DATASETS.get(dataset_name)
    if not config:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    output_file = DATA_RAW_DIR / config["output_name"]

    if output_file.exists() and not force:
        print(f"[SKIP] {dataset_name} already exists at {output_file}")
        # Verify integrity even if skipping download
        manifest = load_manifest()
        if dataset_name in manifest.get("datasets", {}):
            if verify_checksums():
                return output_file
            else:
                print(f"[WARN] Existing file integrity check failed. Re-downloading.")

    print(f"[DOWNLOAD] Fetching {config['hf_id']}...")
    try:
        # Load dataset
        # Note: Using streaming=False to ensure we get the full data for local processing
        # as per the requirement to write real output files.
        ds = load_dataset(
            config["hf_id"],
            config["config"],
            split=config["splits"]  # Load all splits
        )
        
        # If split returns a list of splits (e.g. train, test), handle accordingly
        # The load_dataset returns a DatasetDict if multiple splits are requested or auto-detected
        # If we asked for specific splits, it might return a Dataset or DatasetDict depending on HF version
        # We handle the most common case where it returns a DatasetDict or a single Dataset
        
        data_to_save = []
        
        if hasattr(ds, 'to_dict'): 
            # Single dataset
            data_to_save = ds.to_dict()
        else:
            # DatasetDict (multiple splits)
            for split_name, split_ds in ds.items():
                for item in split_ds:
                    # Add split info to the record for traceability
                    item['_split'] = split_name
                    data_to_save.append(item)

        # Write to JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for item in data_to_save:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # Update Manifest
        file_hash = compute_file_hash(output_file)
        manifest = load_manifest()
        manifest["datasets"] = manifest.get("datasets", {})
        manifest["datasets"][dataset_name] = {
            "filename": config["output_name"],
            "hash": file_hash,
            "hf_id": config["hf_id"],
            "downloaded_at": str(Path.now()) if hasattr(Path, 'now') else "unknown"
        }
        save_manifest(manifest)

        print(f"[SUCCESS] Downloaded {dataset_name} ({len(data_to_save)} records) to {output_file}")
        return output_file

    except Exception as e:
        print(f"[ERROR] Failed to download {dataset_name}: {e}")
        # Fail loudly as per constraints
        raise

def download_all_datasets(force: bool = False) -> List[Path]:
    """Download all configured datasets."""
    ensure_data_dirs()
    downloaded_files = []
    
    # First check if we can skip everything
    if not force and verify_checksums():
        print("[INFO] All datasets present and verified.")
        manifest = load_manifest()
        for name, info in manifest.get("datasets", {}).items():
            downloaded_files.append(DATA_RAW_DIR / info["filename"])
        return downloaded_files

    for name in DATASETS.keys():
        try:
            path = download_dataset(name, force=force)
            if path:
                downloaded_files.append(path)
        except Exception as e:
            print(f"[FATAL] Aborting due to failure in {name}: {e}")
            sys.exit(1)
    
    return downloaded_files

def main():
    """Entry point for the downloader script."""
    import argparse
    parser = argparse.ArgumentParser(description="Download and verify datasets.")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing data")
    parser.add_argument("--dataset", type=str, choices=list(DATASETS.keys()), 
                        help="Download a specific dataset")
    
    args = parser.parse_args()

    if args.verify_only:
        if verify_checksums():
            print("Verification successful.")
            sys.exit(0)
        else:
            print("Verification failed.")
            sys.exit(1)

    if args.dataset:
        download_dataset(args.dataset, force=args.force)
    else:
        download_all_datasets(force=args.force)

    print("Dataset download/verification complete.")

if __name__ == "__main__":
    main()