import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import json
import time
import hashlib

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.config import get_data_path, get_project_root, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATASET_CONFIGS = [
    {
        "name": "alfworld-weights",
        "hf_id": "latent-skills/alfworld-weights",
        "subdir": "weights/alfworld",
        "output_filename": "alfworld_weights.npz",
        "checksum": None  # Add checksum if available in data_sources.yaml
    },
    {
        "name": "searchqa-weights",
        "hf_id": "latent-skills/searchqa-weights",
        "subdir": "weights/searchqa",
        "output_filename": "searchqa_weights.npz",
        "checksum": None
    }
]

def load_real_weights(dataset_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Attempt to load weights from HuggingFace dataset.
    Returns the loaded data dict or None if failed.
    """
    try:
        from datasets import load_dataset
        import tempfile
        import shutil

        logger.info(f"Attempting to load {dataset_config['name']} from HF: {dataset_config['hf_id']}")
        
        # Use streaming to avoid downloading entire dataset if not needed
        # However, for weight files we need to download specific files
        ds = load_dataset(dataset_config['hf_id'], split="train", streaming=False)
        
        # Check if the expected files exist in the dataset
        # This assumes the dataset structure matches the config
        files_to_load = []
        
        # Try to find files in the dataset
        # Note: This is a simplified approach. Real implementation might need
        # to inspect the dataset structure more carefully.
        for item in ds:
            # Assuming the dataset yields dicts with file content or paths
            # This is a placeholder logic - real HF datasets vary
            pass
        
        # Fallback: Try to download specific files if we know the structure
        # For now, we'll simulate the structure check
        # In a real scenario, we'd use huggingface_hub to list files
        
        # Since we can't easily stream specific files from HF datasets without
        # knowing the exact structure, we'll try a direct download approach
        from huggingface_hub import hf_hub_download, list_repo_files
        
        try:
            files = list_repo_files(dataset_config['hf_id'])
            target_files = [f for f in files if f.startswith(dataset_config['subdir']) and f.endswith('.npz')]
            
            if not target_files:
                logger.warning(f"No matching files found in {dataset_config['hf_id']} for {dataset_config['subdir']}")
                return None
            
            # Download all relevant files
            all_data = {}
            for file_path in target_files:
                local_path = hf_hub_download(
                    repo_id=dataset_config['hf_id'],
                    filename=file_path,
                    cache_dir=None
                )
                # Load the npz file
                data = np.load(local_path, allow_pickle=True)
                all_data[file_path] = data
            
            if all_data:
                logger.info(f"Successfully loaded {len(all_data)} files from HF for {dataset_config['name']}")
                return {"data": all_data, "source": "hf"}
                
        except Exception as hf_err:
            logger.warning(f"HF download failed for {dataset_config['name']}: {hf_err}")
            # Continue to fallback
            
    except Exception as e:
        logger.warning(f"Failed to load {dataset_config['name']} from HF: {e}")
    
    return None

def download_from_arxiv_or_github(dataset_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fallback: Attempt to download from arXiv supplementary or GitHub.
    Returns the loaded data dict or None if failed.
    """
    logger.info(f"Attempting fallback for {dataset_config['name']} (arXiv/GitHub)")
    
    # These are placeholder URLs based on the spec
    # In reality, we'd need the exact URLs
    fallback_urls = {
        "alfworld-weights": "https://github.com/latent-skills/alfworld-weights/archive/main.zip",
        "searchqa-weights": "https://github.com/latent-skills/searchqa-weights/archive/main.zip"
    }
    
    url = fallback_urls.get(dataset_config['name'])
    if not url:
        logger.warning(f"No fallback URL configured for {dataset_config['name']}")
        return None
    
    try:
        import requests
        import zipfile
        import io
        
        logger.info(f"Downloading from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Extract the zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Find npz files
            npz_files = [f for f in zip_ref.namelist() if f.endswith('.npz')]
            
            all_data = {}
            for npz_file in npz_files:
                with zip_ref.open(npz_file) as f:
                    data = np.load(f, allow_pickle=True)
                    all_data[npz_file] = data
            
            if all_data:
                logger.info(f"Successfully loaded {len(all_data)} files from fallback for {dataset_config['name']}")
                return {"data": all_data, "source": "fallback"}
                
    except Exception as e:
        logger.warning(f"Fallback download failed for {dataset_config['name']}: {e}")
    
    return None

def save_weights(data_dict: Dict[str, Any], output_path: Path) -> None:
    """
    Save weights to a single npz file.
    Uses atomic write: write to .tmp then rename.
    """
    temp_path = output_path.with_suffix('.npz.tmp')
    
    try:
        # Flatten all data into a single dict for saving
        flattened = {}
        for key, value in data_dict['data'].items():
            # Ensure value is a dict-like object
            if hasattr(value, 'keys'):
                for subkey, subvalue in value.items():
                    flattened[f"{key.replace('/', '_')}_{subkey}"] = subvalue
            else:
                flattened[key] = value
        
        np.savez(temp_path, **flattened)
        
        # Verify the file was written
        if temp_path.exists():
            # Atomic rename
            temp_path.rename(output_path)
            logger.info(f"Successfully saved weights to {output_path}")
        else:
            raise RuntimeError("Temporary file not created")
            
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e

def validate_checksum(file_path: Path, expected_checksum: Optional[str]) -> bool:
    """Validate SHA256 checksum if provided."""
    if not expected_checksum:
        logger.warning(f"No checksum provided for {file_path}, skipping validation")
        return True
    
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    
    actual_checksum = sha256.hexdigest()
    if actual_checksum.lower() != expected_checksum.lower():
        logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        return False
    
    logger.info(f"Checksum validated for {file_path}")
    return True

def process_dataset(dataset_config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Process a single dataset: download, validate, save.
    Returns (success, message).
    """
    logger.info(f"Processing dataset: {dataset_config['name']}")
    
    # Try primary source (HF)
    data = load_real_weights(dataset_config)
    source = "hf"
    
    # Try fallback if primary failed
    if data is None:
        data = download_from_arxiv_or_github(dataset_config)
        source = "fallback"
    
    if data is None:
        return False, f"Failed to download {dataset_config['name']} from all sources"
    
    # Determine output path
    output_path = get_data_path("raw") / dataset_config['output_filename']
    ensure_directories([output_path.parent])
    
    # Save weights
    try:
        save_weights(data, output_path)
        
        # Validate checksum if available
        if dataset_config.get('checksum'):
            if not validate_checksum(output_path, dataset_config['checksum']):
                output_path.unlink()
                return False, f"Checksum validation failed for {dataset_config['name']}"
        
        return True, f"Successfully downloaded and saved {dataset_config['name']} from {source}"
        
    except Exception as e:
        return False, f"Failed to save {dataset_config['name']}: {e}"

def main():
    """Main entry point for weight download."""
    logger.info("Starting LoRA weights download and validation")
    
    raw_dir = get_data_path("raw")
    ensure_directories([raw_dir])
    
    status_results = []
    all_success = True
    
    for config in DATASET_CONFIGS:
        success, message = process_dataset(config)
        status_results.append({
            "dataset": config['name'],
            "success": success,
            "message": message
        })
        if not success:
            all_success = False
            logger.error(message)
        else:
            logger.info(message)
    
    # Write status file
    status_path = get_data_path("processed") / "data_fetch_status.json"
    ensure_directories([status_path.parent])
    
    status_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_success": all_success,
        "details": status_results
    }
    
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Status written to {status_path}")
    
    # Exit with code 0 even if failed (as per spec)
    # The pipeline can check the status file
    if not all_success:
        logger.warning("Some datasets failed to download. Check status file for details.")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
