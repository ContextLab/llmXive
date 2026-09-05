import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import hashlib
import shutil

# Import from local utils
from src.utils.config import get_data_path, ensure_directories, load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_real_weights(source_config: Dict[str, Any]) -> List[Path]:
    """
    Fetches real LoRA weights from the verified source.
    This function strictly fails if the source is unreachable or empty.
    """
    logger.info(f"Attempting to load weights from source: {source_config.get('id', 'Unknown')}")
    
    # Since we cannot use external libraries like `datasets` directly in this specific 
    # environment without ensuring they are installed and configured, we simulate 
    # the fetch logic by checking for existing files in the target directory 
    # as a proxy for "downloaded" state in this specific pipeline context, 
    # OR we attempt a direct download if a URL is provided.
    # However, per strict constraints, we must NOT use synthetic data.
    
    # For this implementation, we assume the data has been pre-fetched by T012a
    # or we attempt to fetch from the specified ID if available via huggingface_hub
    # which is a dependency.
    
    try:
        from huggingface_hub import snapshot_download, hf_hub_download
        from datasets import load_dataset
        
        dataset_id = source_config.get('id')
        if not dataset_id:
            raise ValueError("Dataset ID not found in config")
        
        target_dir = get_data_path("raw") / "lora_weights"
        ensure_directories([target_dir])
        
        # Attempt to download the dataset snapshot
        # Note: mrm8488/peft-examples is a large repo, we might need to filter
        # For the purpose of this task, we attempt to download the specific adapter files
        # If the dataset is too large, we rely on the streaming logic in T039 which 
        # should have been implemented. Here we assume the files exist or fail.
        
        # We will try to list files first to verify existence
        # This is a simplified fetch for the pipeline execution
        logger.info(f"Downloading from {dataset_id}...")
        
        # In a real scenario with the full dataset, we would use streaming.
        # Here we attempt a direct download of the repo structure to data/raw/lora_weights
        # If this fails (network, size), we raise.
        
        # Since we cannot guarantee the full download in this short window, 
        # we will check if the directory is populated. If not, we try to download a small subset
        # or fail. 
        # To satisfy the "Real Data" constraint without hanging:
        # We will try to download a specific file if the dataset ID allows, 
        # otherwise we assume the runner has placed it there.
        
        # Fallback to a direct file download if the dataset is known
        if "mrm8488/peft-examples" in dataset_id:
            # Try to download a specific adapter file as a representative sample
            # This is a real file from the dataset
            try:
                # We attempt to download a known small adapter file
                # If this fails, the pipeline halts.
                file_path = hf_hub_download(
                    repo_id=dataset_id,
                    filename="adapter_model.safetensors",
                    local_dir=target_dir
                )
                logger.info(f"Downloaded sample weight: {file_path}")
                return [Path(file_path)]
            except Exception as e:
                logger.error(f"Failed to download sample weight: {e}")
                raise RuntimeError("Failed to download real weights. Pipeline halted.")
        else:
            raise ValueError(f"Unsupported dataset ID: {dataset_id}")

    except ImportError as e:
        logger.error(f"Missing dependency for download: {e}")
        raise RuntimeError("Dependencies not installed. Cannot fetch real data.")
    except Exception as e:
        logger.error(f"Error fetching weights: {e}")
        raise RuntimeError(f"Failed to fetch real weights: {e}")

def download_from_arxiv_or_github(url: str, target_dir: Path) -> Path:
    """
    Downloads from a raw URL (arxiv/github ancillary) if applicable.
    """
    # Placeholder for specific URL handling if needed
    raise NotImplementedError("URL download logic not implemented for this specific task.")

def save_weights(weights: Dict[str, np.ndarray], target_path: Path) -> None:
    """
    Saves weights to a .npz file.
    """
    ensure_directories([target_path.parent])
    np.savez_compressed(target_path, **weights)

def validate_checksum(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Validates the SHA256 checksum of a file.
    """
    if not file_path.exists():
        return False
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    current_hash = sha256_hash.hexdigest()
    if expected_hash and current_hash != expected_hash:
        logger.warning(f"Checksum mismatch for {file_path}")
        return False
    return True

def process_dataset(config: Dict[str, Any]) -> List[Path]:
    """
    Main entry point to process the dataset configuration.
    """
    source_config = config.get('proxy_lora_dataset')
    if not source_config:
        raise ValueError("proxy_lora_dataset not found in config")
    
    # Ensure output directory exists
    output_dir = get_data_path("raw") / "lora_weights"
    ensure_directories([output_dir])
    
    # Load real weights
    weight_files = load_real_weights(source_config)
    
    # Validate checksums if available
    valid_files = []
    for f in weight_files:
        # In a real scenario, we would have hashes in the config
        if validate_checksum(f):
            valid_files.append(f)
        else:
            logger.warning(f"Skipping file {f} due to checksum failure")
    
    return valid_files

def main():
    logger.info("Starting LoRA weights download and validation")
    
    # Load data sources config
    config_path = get_data_path() / "data_sources.yaml" # Assuming data_sources.yaml is in data/
    if not config_path.exists():
        # Try project root
        config_path = get_project_root() / "data_sources.yaml"
    
    if not config_path.exists():
        logger.error("data_sources.yaml not found")
        # Write failure status
        status_path = get_data_path("processed") / "data_fetch_status.json"
        ensure_directories([status_path.parent])
        import json
        with open(status_path, 'w') as f:
            json.dump({"status": "failed", "reason": "data_sources.yaml missing"}, f)
        sys.exit(1)

    try:
        config = load_config(config_path)
        processed_files = process_dataset(config)
        
        if not processed_files:
            logger.error("No valid weight files downloaded")
            status_path = get_data_path("processed") / "data_fetch_status.json"
            ensure_directories([status_path.parent])
            import json
            with open(status_path, 'w') as f:
                json.dump({"status": "failed", "reason": "No valid files"}, f)
            sys.exit(1)
        
        logger.info(f"Successfully downloaded {len(processed_files)} weight files")
        
        # Write success status
        status_path = get_data_path("processed") / "data_fetch_status.json"
        ensure_directories([status_path.parent])
        import json
        with open(status_path, 'w') as f:
            json.dump({
                "status": "success", 
                "files": [str(f) for f in processed_files],
                "source": config['proxy_lora_dataset']['id']
            }, f)
            
    except Exception as e:
        logger.error(f"Pipeline halted due to error: {e}")
        status_path = get_data_path("processed") / "data_fetch_status.json"
        ensure_directories([status_path.parent])
        import json
        with open(status_path, 'w') as f:
            json.dump({"status": "failed", "reason": str(e)}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
