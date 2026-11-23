"""
Verify HuggingFace dataset availability and checksum.
Implements T074.
"""
import os
import sys
import json
import logging
import hashlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/hf_verification.log')
    ]
)
logger = logging.getLogger(__name__)

def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_dataset_availability(dataset_name: str, expected_hash: str = None):
    """
    Verify a dataset is available on HuggingFace Hub and optionally check checksum.
    
    Args:
        dataset_name: HuggingFace dataset identifier (e.g., 'username/dataset-name')
        expected_hash: Optional expected SHA256 hash of the downloaded file
    
    Returns:
        Path to the downloaded file if successful, None otherwise
    """
    try:
        from huggingface_hub import hf_hub_download, HfApi
    except ImportError:
        logger.error("huggingface_hub not installed. Run: pip install huggingface_hub")
        raise RuntimeError("Missing dependency: huggingface_hub")

    try:
        # Attempt to download the file (assumes first file in repo for simplicity)
        # In a real scenario, you might specify a filename
        api = HfApi()
        files = api.list_repo_files(dataset_name)
        
        if not files:
            logger.error(f"No files found in dataset {dataset_name}")
            return None
        
        # Download the first file (or a specific one if known)
        # For this verification, we'll download the first file
        filename = files[0]
        logger.info(f"Downloading {filename} from {dataset_name}...")
        
        local_path = hf_hub_download(
            repo_id=dataset_name,
            filename=filename,
            local_dir="data/raw/hf_verify"
        )
        
        logger.info(f"Downloaded to: {local_path}")
        
        # Verify hash if provided
        if expected_hash:
            actual_hash = compute_file_hash(local_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch! Expected: {expected_hash}, Got: {actual_hash}")
                return None
            logger.info("Hash verification passed.")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Failed to verify dataset {dataset_name}: {str(e)}")
        return None

def main():
    """Main entry point for verification."""
    import argparse
    parser = argparse.ArgumentParser(description="Verify HuggingFace dataset availability")
    parser.add_argument('--dataset', type=str, help="Dataset name (e.g., username/dataset)")
    parser.add_argument('--hash', type=str, help="Expected SHA256 hash")
    args = parser.parse_args()

    if not args.dataset:
        logger.warning("No dataset specified. Usage: python verify_hf_dataset.py --dataset username/dataset")
        return 1

    result = verify_dataset_availability(args.dataset, args.hash)
    
    if result:
        logger.info(f"Verification successful: {result}")
        return 0
    else:
        logger.error("Verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
