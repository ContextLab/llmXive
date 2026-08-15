import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import hashlib
import time

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_data_path, ensure_directories, set_seed
from huggingface_hub import HfApi, hf_hub_download, list_repo_files
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data source configuration
DATASET_CONFIG = {
    'alfworld': {
        'hf_dataset': 'latent-skills/alfworld-weights',
        'hf_path': 'weights/alfworld',
        'output_filename': 'alfworld_weights.npz',
        'arxiv_url': 'https://arxiv.org/e-print/2405.12345', # Placeholder, will update if real URL found
        'gh_repo': 'https://github.com/latent-skills/weights' # Placeholder
    },
    'searchqa': {
        'hf_dataset': 'latent-skills/searchqa-weights',
        'hf_path': 'weights/searchqa',
        'output_filename': 'searchqa_weights.npz',
        'arxiv_url': 'https://arxiv.org/e-print/2405.12345', # Placeholder
        'gh_repo': 'https://github.com/latent-skills/weights' # Placeholder
    }
}

def load_real_weights(source_type: str, dataset_name: str, output_path: Path) -> bool:
    """
    Attempts to download real weights from HuggingFace, then arXiv, then GitHub.
    Returns True if successful, False otherwise.
    """
    config = DATASET_CONFIG[dataset_name]
    
    # Strategy 1: HuggingFace Dataset
    logger.info(f"Attempting to download {dataset_name} weights from HuggingFace...")
    try:
        api = HfApi()
        repo_files = list_repo_files(config['hf_dataset'])
        
        # Find npz files in the specified path
        target_files = [f for f in repo_files if f.startswith(config['hf_path']) and f.endswith('.npz')]
        
        if not target_files:
            logger.warning(f"No .npz files found in {config['hf_path']} for {dataset_name}")
            raise FileNotFoundError(f"No weights found in HF dataset for {dataset_name}")
        
        logger.info(f"Found {len(target_files)} weight files in HuggingFace dataset")
        
        # Download and merge all npz files
        merged_data = {}
        for file_path in target_files:
            logger.info(f"Downloading {file_path}...")
            local_path = hf_hub_download(
                repo_id=config['hf_dataset'],
                filename=file_path,
                repo_type="dataset"
            )
            
            # Load and merge
            data = np.load(local_path, allow_pickle=True)
            for key in data.files:
                merged_data[key] = data[key]
        
        # Save merged data
        np.savez(output_path, **merged_data)
        logger.info(f"Successfully downloaded and merged {dataset_name} weights to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"HF download failed: {e}")
        # Fallback to arXiv
        pass

    # Strategy 2: arXiv Supplementary (if available)
    logger.info(f"Attempting to download {dataset_name} weights from arXiv...")
    try:
        # Note: arXiv supplementary URLs are often not directly accessible programmatically
        # This is a placeholder for where we would implement arXiv download logic
        # For now, we'll log and move to GitHub
        logger.warning("arXiv supplementary download not implemented for this dataset")
    except Exception as e:
        logger.error(f"arXiv download failed: {e}")

    # Strategy 3: GitHub Repository
    logger.info(f"Attempting to download {dataset_name} weights from GitHub...")
    try:
        # Placeholder for GitHub clone/download logic
        logger.warning("GitHub download not implemented for this dataset")
    except Exception as e:
        logger.error(f"GitHub download failed: {e}")

    logger.error(f"All download strategies failed for {dataset_name}")
    return False

def validate_checksum(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Validates the checksum of a downloaded file.
    """
    if not file_path.exists():
        return False
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual_hash = sha256_hash.hexdigest()
    logger.info(f"File {file_path} SHA256: {actual_hash}")
    
    if expected_hash:
        if actual_hash.lower() == expected_hash.lower():
            logger.info("Checksum validation passed")
            return True
        else:
            logger.error(f"Checksum mismatch! Expected {expected_hash}, got {actual_hash}")
            return False
    
    logger.warning("No expected hash provided, skipping validation")
    return True

def process_dataset(dataset_name: str, output_dir: Path) -> Tuple[bool, str]:
    """
    Process a single dataset: download, validate, and save.
    """
    config = DATASET_CONFIG[dataset_name]
    output_path = output_dir / config['output_filename']
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing dataset: {dataset_name}")
    
    success = load_real_weights(config['hf_dataset'], dataset_name, output_path)
    
    if not success:
        return False, f"Failed to download {dataset_name} weights"
    
    # Validate checksum if available
    # Note: We don't have checksums in data_sources.yaml for these specific files yet
    # so we skip validation for now
    if not validate_checksum(output_path, None):
        return False, f"Checksum validation failed for {dataset_name}"
    
    return True, f"Successfully processed {dataset_name}"

def main():
    """
    Main entry point for downloading LoRA weights.
    """
    set_seed(42)
    ensure_directories()
    
    data_dir = get_data_path() / 'raw'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting LoRA weights download and validation")
    
    datasets = ['alfworld', 'searchqa']
    results = {}
    
    for dataset in datasets:
        logger.info(f"--- Processing {dataset} ---")
        success, message = process_dataset(dataset, data_dir)
        results[dataset] = {
            'success': success,
            'message': message,
            'source': 'HuggingFace' if success else 'FAILED'
        }
        logger.info(f"{dataset}: {message}")
    
    # Log summary
    logger.info("--- Download Summary ---")
    all_success = True
    for dataset, result in results.items():
        status = "✓" if result['success'] else "✗"
        logger.info(f"{dataset}: {status} ({result['source']})")
        if not result['success']:
            all_success = False
    
    if not all_success:
        logger.error("One or more datasets failed to download. Halting pipeline.")
        sys.exit(1)
    
    logger.info("All weights downloaded successfully.")

if __name__ == "__main__":
    main()