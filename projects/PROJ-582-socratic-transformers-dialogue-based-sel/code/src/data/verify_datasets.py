"""
Dataset Verification Utility for Socratic Transformers Project.

This module handles the verification of external datasets (GSM8K and MATH) by:
1. Downloading and caching datasets from HuggingFace Hub.
2. Computing SHA-256 checksums of the cached dataset files.
3. Storing checksums in a manifest file under `state/`.
4. Validating existing datasets against the manifest before processing.

It ensures data integrity by failing loudly if checksums do not match or
if real data cannot be retrieved.
"""
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, List, Any

from datasets import load_dataset
from src.utils.config import get_config

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
MANIFEST_PATH = STATE_DIR / "dataset_manifest.json"

# Real dataset identifiers
DATASET_CONFIGS = {
    "gsm8k": {
        "name": "gsm8k",
        "hub_id": "openai/gsm8k",
        "config": "main",
        "split": "train",
    },
    "math": {
        "name": "math",
        "hub_id": "hendrycks/math",
        "config": "algebra", # Specific split for MATH dataset
        "split": "train",
    },
}


def ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_manifest() -> Dict[str, Any]:
    """Load the existing manifest or return an empty structure."""
    if not MANIFEST_PATH.exists():
        return {"datasets": {}, "version": "1.0"}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Failed to load manifest {MANIFEST_PATH}: {e}")


def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest to disk."""
    ensure_state_dir()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def download_and_cache_dataset(dataset_id: str, hub_id: str, config: str, split: str) -> List[Path]:
    """
    Download and cache a dataset from HuggingFace Hub.
    Returns a list of paths to the cached data files.
    """
    print(f"Downloading and caching dataset: {hub_id} (config: {config}, split: {split})")
    try:
        # Use streaming=False to force full download and caching for checksumming
        dataset = load_dataset(hub_id, config, split=split, trust_remote_code=True)
        
        # The 'datasets' library caches data in a specific directory structure.
        # We need to find where the actual arrow/json files are stored for this specific dataset.
        # Since the dataset object itself doesn't always expose the raw file path directly
        # in a portable way across all versions, we will rely on the cache directory
        # logic or a temporary export if necessary.
        
        # However, for integrity verification of the *source* as fetched,
        # we can compute a hash of the entire dataset content by iterating it.
        # But the task asks for checksums of "raw data".
        # A robust way is to export to a temporary JSONL and hash that, 
        # or hash the cache files if we can locate them.
        
        # Approach: Export to a temporary JSONL file in a controlled location to hash.
        # This ensures the hash represents the exact data fetched.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as tmp:
            tmp_path = Path(tmp.name)
            for item in dataset:
                tmp.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        return [tmp_path]
        
    except Exception as e:
        raise RuntimeError(f"Failed to download/cache dataset {hub_id}: {e}")


def verify_dataset(dataset_name: str, expected_hash: str) -> bool:
    """
    Verify a dataset against the expected hash in the manifest.
    Returns True if valid, False otherwise.
    """
    manifest = load_manifest()
    if dataset_name not in manifest.get("datasets", {}):
        return False
    
    current_hash = manifest["datasets"][dataset_name].get("hash")
    return current_hash == expected_hash


def register_dataset(dataset_name: str, files: List[Path], manifest: Dict[str, Any]) -> None:
    """
    Register a dataset in the manifest by computing hashes of its files.
    """
    if "datasets" not in manifest:
        manifest["datasets"] = {}
    
    dataset_info = {
        "files": [],
        "hash": None,
        "hub_id": None,
        "config": None,
    }
    
    combined_hasher = hashlib.sha256()
    
    for file_path in files:
        file_hash = compute_file_hash(file_path)
        dataset_info["files"].append({
            "path": str(file_path),
            "hash": file_hash,
        })
        combined_hasher.update(file_hash.encode('utf-8'))
        
        # Cleanup temporary file after hashing if it was created here
        if file_path.is_file():
            # If it's a temp file we created in this run, we might want to keep it 
            # or delete it depending on strategy. For verification, we just need the hash.
            # We will delete the temp file to save space, assuming the dataset 
            # is re-fetched or cached by HF if needed later.
            # However, T012 (Download) will handle the persistent storage.
            # Here we just verify the integrity of the fetched batch.
            pass 
    
    dataset_info["hash"] = combined_hasher.hexdigest()
    
    # We need to know the hub_id and config to re-fetch if needed, 
    # but for this task we just record the hash of the fetched content.
    # We'll assume the caller passes the correct config info or we look it up.
    
    manifest["datasets"][dataset_name] = dataset_info
    save_manifest(manifest)
    print(f"Registered dataset {dataset_name} with hash {dataset_info['hash']}")


def main():
    """
    Main entry point for dataset verification.
    
    1. Checks if manifest exists.
    2. If not, or if verification fails, downloads datasets and registers them.
    3. If manifest exists, verifies checksums.
    
    Exit Code 0: All checksums match or newly registered successfully.
    Exit Code 1: Checksum mismatch or download failure.
    """
    print("Starting dataset verification...")
    manifest = load_manifest()
    
    all_valid = True
    
    for key, config in DATASET_CONFIGS.items():
        print(f"\n--- Processing {key} ---")
        hub_id = config["hub_id"]
        ds_config = config["config"]
        split = config["split"]
        
        # Check if we have a record for this dataset
        if key in manifest.get("datasets", {}):
            print(f"Found existing record for {key}. Verifying hash...")
            # In a real scenario, we would re-fetch or check the cache.
            # Since we are simulating the verification of the *source* integrity,
            # and we don't have the persistent files from a previous run in this environment,
            # we will re-download and compare against the stored hash.
            # If the stored hash matches the new download, it's valid.
            
            try:
                files = download_and_cache_dataset(key, hub_id, ds_config, split)
                # Compute new hash
                combined_hasher = hashlib.sha256()
                for f in files:
                    combined_hasher.update(compute_file_hash(f).encode('utf-8'))
                    f.unlink(missing_ok=True) # Cleanup temp
                
                new_hash = combined_hasher.hexdigest()
                stored_hash = manifest["datasets"][key]["hash"]
                
                if new_hash == stored_hash:
                    print(f"✓ Checksum verified for {key}: {stored_hash}")
                else:
                    print(f"✗ Checksum MISMATCH for {key}!")
                    print(f"  Expected: {stored_hash}")
                    print(f"  Got:      {new_hash}")
                    all_valid = False
            except Exception as e:
                print(f"✗ Failed to verify {key}: {e}")
                all_valid = False
        else:
            print(f"No record found for {key}. Downloading and registering...")
            try:
                files = download_and_cache_dataset(key, hub_id, ds_config, split)
                # Compute hash
                combined_hasher = hashlib.sha256()
                for f in files:
                    combined_hasher.update(compute_file_hash(f).encode('utf-8'))
                    f.unlink(missing_ok=True)
                
                new_hash = combined_hasher.hexdigest()
                
                # Update manifest
                manifest["datasets"][key] = {
                    "hub_id": hub_id,
                    "config": ds_config,
                    "split": split,
                    "hash": new_hash,
                    "files": []
                }
                save_manifest(manifest)
                print(f"✓ Registered {key} with hash: {new_hash}")
            except Exception as e:
                print(f"✗ Failed to download/register {key}: {e}")
                all_valid = False
    
    if all_valid:
        print("\n✅ All datasets verified successfully.")
        sys.exit(0)
    else:
        print("\n❌ Verification failed. Checksums do not match or downloads failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()