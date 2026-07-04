"""
Download module for fetching the RAVDESS dataset.

This module handles the programmatic acquisition of the RAVDESS dataset
from the verified HuggingFace URL (as established in T011a) and caches it
in the project's data/raw directory.
"""
import os
import sys
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

# Import project configuration
from config import (
    get_env_config,
    ensure_directories,
    set_all_seeds,
    RAVDESS_DEFAULT_URL,
    RAVDESS_DATASET_NAME
)

# Attempt to import HuggingFace datasets
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

def fetch_ravdess_dataset(
    output_dir: Optional[Path] = None,
    dataset_name: Optional[str] = None,
    trust_remote_code: bool = True
) -> Dict[str, Any]:
    """
    Fetches the RAVDESS dataset from HuggingFace and caches it locally.
    
    Args:
        output_dir: Base directory for caching. Defaults to project's data/raw.
        dataset_name: The HuggingFace dataset identifier. Defaults to config value.
        trust_remote_code: Whether to trust remote code during loading.
        
    Returns:
        A dictionary containing metadata about the download operation.
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or accessed.
        ConnectionError: If network access fails.
    """
    # Resolve paths and config
    config = get_env_config()
    if output_dir is None:
        base_data_dir = Path(config.get('data_dir', 'data'))
        output_dir = base_data_dir / 'raw'
    else:
        output_dir = Path(output_dir)
        
    if dataset_name is None:
        dataset_name = RAVDESS_DATASET_NAME
        
    # Ensure directory exists
    ensure_directories([output_dir])
    
    print(f"Initializing download for dataset: {dataset_name}")
    print(f"Target directory: {output_dir}")
    
    try:
        # Load the dataset
        # Note: RAVDESS on HuggingFace is often a wrapper around the original files.
        # We load it to ensure connectivity and metadata availability.
        # We use streaming=False to force download for local caching if needed,
        # though HuggingFace usually caches automatically in ~/.cache/huggingface.
        # Here we explicitly copy to our data/raw if the dataset structure allows,
        # or we just verify the load and record the cache location.
        
        # Attempt to load with streaming first to check availability, then full load
        # to ensure files are present if the dataset card suggests it.
        dataset = load_dataset(
            dataset_name,
            trust_remote_code=trust_remote_code,
            cache_dir=str(output_dir / '.hf_cache') # Use a subfolder for HF cache to keep data/raw clean
        )
        
        # Verify dataset structure
        if not dataset:
            raise FileNotFoundError(f"Dataset {dataset_name} loaded but returned empty.")
            
        # Record metadata
        download_info = {
            "dataset_name": dataset_name,
            "downloaded_at": str(Path().cwd()),
            "output_base": str(output_dir),
            "cache_location": str(output_dir / '.hf_cache'),
            "splits": list(dataset.keys()) if hasattr(dataset, 'keys') else ['default'],
            "status": "success",
            "message": "Dataset loaded and cached successfully via HuggingFace."
        }
        
        # Save metadata log
        log_path = output_dir / 'ravdess_download_log.json'
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(download_info, f, indent=2)
            
        print(f"Success: RAVDESS dataset '{dataset_name}' is available.")
        print(f"Log saved to: {log_path}")
        
        return download_info
        
    except Exception as e:
        error_info = {
            "dataset_name": dataset_name,
            "status": "failed",
            "error_type": type(e).__name__,
            "message": str(e)
        }
        print(f"ERROR: Failed to fetch dataset {dataset_name}: {e}")
        # Save error log
        error_log_path = output_dir / 'ravdess_download_error.json'
        with open(error_log_path, 'w', encoding='utf-8') as f:
            json.dump(error_info, f, indent=2)
        raise

def main():
    """Entry point for the download script."""
    print("--- RAVDESS Dataset Downloader ---")
    set_all_seeds() # Ensure deterministic behavior if any randomness is involved in loading
    
    try:
        result = fetch_ravdess_dataset()
        if result['status'] == 'success':
            print("Download and caching complete.")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Download process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
