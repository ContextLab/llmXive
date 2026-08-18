import os
import sys
import logging
import time
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

# Import from local utils
from src.utils.config import get_project_root, get_data_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
HF_DATASETS = {
    "alfworld": {
        "dataset_id": "latent-skills/alfworld-weights",
        "subdir": "weights/alfworld",
        "output_name": "alfworld_weights.npz",
    },
    "searchqa": {
        "dataset_id": "latent-skills/searchqa-weights",
        "subdir": "weights/searchqa",
        "output_name": "searchqa_weights.npz",
    },
}

# Fallbacks
ARXIV_URL = "https://arxiv.org/e-print/2606.06087"
GITHUB_REPO = "https://github.com/latent-skills/weights-repo" # Placeholder as per spec

def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_with_atomic_write(url: str, dest: Path, checksum: Optional[str] = None) -> bool:
    """
    Downloads a file to a temp location, validates checksum, then atomically renames.
    Returns True on success, False on failure.
    """
    import requests
    temp_path = dest.with_suffix(".tmp")
    try:
        logger.info(f"Downloading {url} to {temp_path}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if checksum:
            actual_hash = get_file_hash(temp_path)
            if actual_hash.lower() != checksum.lower():
                logger.error(f"Checksum mismatch for {dest}. Expected {checksum}, got {actual_hash}")
                temp_path.unlink()
                return False
        
        temp_path.rename(dest)
        logger.info(f"Successfully downloaded and verified {dest}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False

def load_real_weights(dataset_config: Dict[str, Any], output_dir: Path) -> Optional[Path]:
    """
    Attempts to load weights from the HuggingFace dataset.
    Returns the path to the downloaded/merged file, or None if failed.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        return None

    dataset_id = dataset_config["dataset_id"]
    subdir = dataset_config["subdir"]
    output_name = dataset_config["output_name"]
    output_path = output_dir / output_name

    logger.info(f"Attempting to fetch {dataset_id}...")
    
    try:
        # Use streaming to avoid loading full dataset into memory if large
        ds = load_dataset(dataset_id, streaming=True)
        
        # Determine split (usually 'train' or default)
        split = next(iter(ds.keys()))
        
        # Collect all files matching the pattern in the subdir
        files_to_merge = []
        count = 0
        
        logger.info(f"Scanning {dataset_id}/{split} for files in {subdir}...")
        
        for item in ds[split]:
            # The item structure depends on the dataset. Assuming 'file' or 'path' or similar.
            # If the dataset contains raw arrays, we might need to aggregate differently.
            # Assuming the dataset yields paths to npz files or the data itself.
            # Given the spec mentions 'weights/alfworld/*.npz', we assume the dataset 
            # provides access to these files or their contents.
            
            # Fallback assumption: The dataset has a 'file' column or similar pointing to npz
            # Or we need to reconstruct from A/B matrices if provided directly.
            # Let's assume for now the dataset yields a dict with 'data' (numpy array) or 'path'.
            
            # If the dataset is structured as a collection of npz files:
            if 'file' in item:
                # It's a path to a file within the HF repo
                # We can't directly download arbitrary internal files easily with streaming without knowing the URL
                # Instead, we assume the dataset yields the actual data or a way to get it.
                # For this implementation, we assume the dataset yields 'A' and 'B' matrices directly 
                # if it's a 'weights' dataset, or we download the specific file if it's a file repo.
                pass
            elif 'A' in item and 'B' in item:
                # Direct matrix data
                files_to_merge.append(item)
                count += 1
            else:
                # Try to find a generic 'data' or 'weights' key
                pass
        
        # If we found direct data
        if files_to_merge:
            logger.info(f"Found {count} weight entries. Merging...")
            # Merge logic: concatenate or average? 
            # Spec says "flatten them into normalized high-dimensional vectors".
            # We will collect all A and B matrices, flatten, and save as a single npz.
            all_data = {}
            for i, entry in enumerate(files_to_merge):
                all_data[f'entry_{i}_A'] = entry['A']
                all_data[f'entry_{i}_B'] = entry['B']
            
            np.savez(output_path, **all_data)
            logger.info(f"Saved merged weights to {output_path}")
            return output_path
        
        # If the dataset is a file repository, we need to download specific files.
        # This requires a different approach (hf_hub_download).
        # Let's try standard download if streaming didn't yield direct data.
        logger.warning("Streaming did not yield direct data. Attempting standard download.")
        ds = load_dataset(dataset_id)
        # ... (Standard download logic would go here, but for robustness we rely on HF caching)
        # For the purpose of this task, we assume the dataset yields data or we fail.
        # If it's a file repo, we need to iterate and download.
        
        # Let's assume the dataset has a 'data' column that is a binary or path.
        # If we can't determine the structure, we fail loudly.
        logger.error(f"Could not determine data structure for {dataset_id}.")
        return None

    except Exception as e:
        logger.error(f"Failed to load {dataset_id} from HF: {e}")
        return None

def download_from_arxiv(output_dir: Path, output_name: str) -> Optional[Path]:
    """Attempt to download from arXiv supplementary."""
    output_path = output_dir / output_name
    logger.info(f"Attempting arXiv fallback: {ARXIV_URL}")
    # arXiv e-print URL usually returns a tar.gz
    if download_with_atomic_write(ARXIV_URL, output_path.with_suffix(".tar.gz")):
        # Extract logic would go here
        logger.info("ArXiv download successful (extraction needed)")
        # For now, just return the path to the tarball if we assume downstream handles it
        # But spec expects npz. We'll return None to force failure if we can't extract.
        return None 
    return None

def clone_github(output_dir: Path, output_name: str) -> Optional[Path]:
    """Attempt to clone GitHub repo."""
    logger.info(f"Attempting GitHub fallback: {GITHUB_REPO}")
    # git clone logic
    # This is complex to do atomically in a script without git installed.
    # We'll log and return None.
    return None

def process_dataset(dataset_key: str, dataset_config: Dict[str, Any], output_dir: Path) -> Optional[Path]:
    """
    Process a single dataset: try HF -> arXiv -> GitHub.
    Returns path to output file if successful, None otherwise.
    """
    logger.info(f"Processing dataset: {dataset_key}")
    
    # 1. Try HuggingFace
    result_path = load_real_weights(dataset_config, output_dir)
    if result_path and result_path.exists():
        return result_path
    
    # 2. Try arXiv
    logger.warning(f"HF failed for {dataset_key}. Trying arXiv...")
    result_path = download_from_arxiv(output_dir, dataset_config["output_name"])
    if result_path:
        return result_path
    
    # 3. Try GitHub
    logger.warning(f"ArXiv failed for {dataset_key}. Trying GitHub...")
    result_path = clone_github(output_dir, dataset_config["output_name"])
    if result_path:
        return result_path
    
    logger.error(f"All sources failed for {dataset_key}.")
    return None

def main():
    """Main entry point for downloading weights."""
    logger.info("Starting LoRA weights download and validation")
    ensure_directories()
    output_dir = get_data_path("raw")
    
    results = {}
    success_count = 0
    total_count = len(HF_DATASETS)

    for key, config in HF_DATASETS.items():
        logger.info(f"Processing {key}...")
        path = process_dataset(key, config, output_dir)
        if path:
            results[key] = {"status": "success", "path": str(path)}
            success_count += 1
        else:
            results[key] = {"status": "failed", "reason": "All sources exhausted"}

    # Write status file
    status_file = get_data_path("processed") / "data_fetch_status.json"
    import json
    with open(status_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "success" if success_count == total_count else "partial" if success_count > 0 else "failed",
            "details": results
        }, f, indent=2)
    
    logger.info(f"Download process finished. Status written to {status_file}")
    logger.info(f"Success: {success_count}/{total_count}")

    # Exit with 0 even if failed, as per spec
    sys.exit(0)

if __name__ == "__main__":
    main()