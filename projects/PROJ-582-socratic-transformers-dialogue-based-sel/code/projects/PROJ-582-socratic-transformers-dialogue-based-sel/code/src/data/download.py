"""
Dataset Downloader for Socratic Transformers Project.

This module implements the download of real datasets (GSM8K and MATH) via the
HuggingFace `datasets` library. It adheres to the constraint of using real data
only, failing loudly if the data cannot be fetched, and never falling back to
synthetic generation.

It also includes functionality to compute checksums for verification against
the spec.md manifest (to be implemented in T010).
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project utils as per API surface
from src.utils.config import get_config
from src.utils.logging import get_logger

# Import datasets library
try:
    from datasets import load_dataset, disable_progress_bar
except ImportError:
    # Fallback if not installed, though requirements.txt should handle this
    print("ERROR: 'datasets' library not found. Please install via requirements.txt")
    sys.exit(1)

# Configure logging
logger = get_logger(__name__)

# Disable progress bars for cleaner log output in automated runners
disable_progress_bar()

# Constants for dataset identifiers
DATASET_CONFIGS = {
    "gsm8k": {
        "name": "gsm8k",
        "hf_id": "openai/gsm8k",
        "config": "main",
        "output_file": "gsm8k_train.jsonl",
        "output_subdir": "raw/gsm8k",
        "split": "train",
        "description": "Grade School Math 8K dataset"
    },
    "math": {
        "name": "math",
        "hf_id": "hendrycks/math",
        "config": "all", # We might need to handle subsets, but 'all' is the standard entry
        "output_file": "math_train.jsonl",
        "output_subdir": "raw/math",
        "split": "train", # Standard split for training
        "description": "MATH dataset for competition math"
    }
}

def ensure_data_dirs(base_path: Path) -> None:
    """Ensure the raw data directories exist."""
    for key in DATASET_CONFIGS:
        subdir_path = base_path / DATASET_CONFIGS[key]["output_subdir"]
        subdir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {subdir_path}")

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the expected checksums manifest."""
    if not manifest_path.exists():
        logger.warning(f"Manifest not found at {manifest_path}. Verification will be skipped.")
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_manifest(manifest_path: Path, data: Dict[str, Any]) -> None:
    """Save the checksums manifest."""
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def verify_checksums(downloaded_path: Path, expected_hash: str) -> bool:
    """Verify the downloaded file against the expected hash."""
    actual_hash = compute_file_hash(downloaded_path)
    logger.info(f"Computed hash for {downloaded_path.name}: {actual_hash}")
    if actual_hash == expected_hash:
        logger.info(f"Checksum verification PASSED for {downloaded_path.name}")
        return True
    else:
        logger.error(f"Checksum verification FAILED for {downloaded_path.name}")
        logger.error(f"  Expected: {expected_hash}")
        logger.error(f"  Actual:   {actual_hash}")
        return False

def download_dataset(dataset_key: str, base_path: Path, manifest: Optional[Dict[str, Any]] = None) -> Path:
    """
    Download a specific dataset from HuggingFace and save it as JSONL.

    Args:
        dataset_key: Key in DATASET_CONFIGS (e.g., 'gsm8k', 'math')
        base_path: Base project path (code/)
        manifest: Optional manifest dict for checksum verification

    Returns:
        Path to the downloaded file.

    Raises:
        RuntimeError: If the dataset cannot be fetched or saved.
    """
    config = DATASET_CONFIGS[dataset_key]
    hf_id = config["hf_id"]
    split = config["split"]
    output_subdir = base_path / config["output_subdir"]
    output_file_path = output_subdir / config["output_file"]

    logger.info(f"Starting download for {config['description']} ({hf_id})...")

    try:
        # Load the dataset
        # Note: We use streaming=False to ensure we get the full dataset in memory for processing
        # if it fits, or we handle it in chunks if we change strategy later.
        # For GSM8K and MATH, full load is usually feasible in the context of this project's
        # memory constraints if we process carefully, but we'll attempt a direct load.
        logger.info(f"Loading dataset from HF: {hf_id}, split: {split}")
        dataset = load_dataset(hf_id, split=split, trust_remote_code=True)

        if manifest:
            expected_hash = manifest.get(dataset_key, {}).get("hash")
            if expected_hash:
                logger.info(f"Expected checksum for {dataset_key}: {expected_hash}")

        # Write to JSONL
        logger.info(f"Writing dataset to {output_file_path}...")
        with open(output_file_path, "w", encoding="utf-8") as f:
            for item in dataset:
                # Ensure we serialize safely. Some datasets might have complex types.
                # We convert to string representation if necessary, but standard dicts work.
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + "\n")

        logger.info(f"Successfully downloaded and saved {dataset_key} to {output_file_path}")

        # Verify checksum if manifest is provided
        if manifest:
            expected_hash = manifest.get(dataset_key, {}).get("hash")
            if expected_hash:
                if not verify_checksums(output_file_path, expected_hash):
                    # We do not delete the file here, but we raise an error to stop the pipeline
                    # as per "Fail loudly" constraint.
                    raise RuntimeError(f"Checksum mismatch for {dataset_key}. Aborting.")
            else:
                logger.warning(f"No expected checksum found for {dataset_key} in manifest.")

        return output_file_path

    except Exception as e:
        logger.error(f"Failed to download or process {dataset_key}: {e}")
        # Clean up partial file if it exists
        if output_file_path.exists():
            logger.warning(f"Removing partial file: {output_file_path}")
            output_file_path.unlink()
        raise RuntimeError(f"Data download failed for {dataset_key}. Real data source unreachable.") from e

def download_all_datasets(base_path: Path, manifest_path: Optional[Path] = None) -> List[Path]:
    """
    Download all configured datasets.

    Args:
        base_path: Base project path.
        manifest_path: Path to the checksum manifest file.

    Returns:
        List of paths to downloaded files.
    """
    ensure_data_dirs(base_path)

    manifest = None
    if manifest_path and manifest_path.exists():
        manifest = load_manifest(manifest_path)

    downloaded_files = []
    for key in DATASET_CONFIGS:
        file_path = download_dataset(key, base_path, manifest)
        downloaded_files.append(file_path)

    return downloaded_files

def main():
    """Entry point for the download script."""
    # Determine base path relative to the script location or project root
    # Assuming script is run from code/ directory or similar
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent # code/src/data -> code -> project root
    
    # Adjust path logic if running from different context, but typically:
    # code/ is the root for this project structure
    base_path = current_dir.parent.parent # code/
    
    manifest_path = base_path / "state" / "dataset_checksums.json"
    
    # Ensure state directory exists for manifest
    state_dir = base_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Starting dataset download process...")
        files = download_all_datasets(base_path, manifest_path)
        logger.info(f"Download complete. Files: {[str(f) for f in files]}")
        
        # Update manifest with actual hashes if it didn't exist or for verification
        # (This part is more for T010 to read, but we can compute and save if needed)
        if not manifest_path.exists():
            logger.info("No manifest found. Generating initial manifest with computed hashes...")
            new_manifest = {}
            for key in DATASET_CONFIGS:
                file_path = base_path / DATASET_CONFIGS[key]["output_subdir"] / DATASET_CONFIGS[key]["output_file"]
                if file_path.exists():
                  new_manifest[key] = {
                      "hash": compute_file_hash(file_path),
                      "size_bytes": file_path.stat().st_size
                  }
            save_manifest(manifest_path, new_manifest)
            logger.info(f"Manifest saved to {manifest_path}")

    except RuntimeError as e:
        logger.error(f"Critical error during download: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()