"""
Task T015b: Download Persona-Chat dataset to data/raw/persona_chat/ with checksums.

This script downloads the Persona-Chat dataset from Hugging Face Hub as a fallback source
for the politeness study, satisfying FR-001's requirement to store datasets locally.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.data_integrity import compute_directory_checksum, generate_manifest
from utils.env_config import get_hf_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "persona_chat"
HF_DATASET_ID = "parlance/persona-chat"
OUTPUT_DIR = "data/raw/persona_chat"
MANIFEST_FILE = "manifest.json"
CHECKSUM_FILE = "checksums.json"

def ensure_directories():
    """Create necessary output directories."""
    output_path = project_root / OUTPUT_DIR
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory: {output_path}")
    return output_path

def load_dataset_with_check():
    """
    Download the Persona-Chat dataset from Hugging Face Hub.
    
    This function:
    1. Checks for HF_TOKEN in environment
    2. Downloads the dataset using the datasets library
    3. Saves it to the output directory in parquet format
    4. Generates checksums and manifest for integrity verification
    
    Returns:
        Path: Path to the downloaded dataset directory
    """
    output_path = ensure_directories()
    
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to download dataset: {HF_DATASET_ID}")
        
        # Attempt to download the dataset
        # Using streaming=False to download full dataset for local storage
        # This satisfies FR-001's requirement to store datasets locally
        dataset = load_dataset(
            HF_DATASET_ID,
            split="train",  # Persona-Chat has a single train split
            trust_remote_code=True
        )
        
        logger.info(f"Successfully loaded {len(dataset)} rows from {HF_DATASET_ID}")
        
        # Save dataset to parquet format
        parquet_path = output_path / "persona_chat.parquet"
        dataset.to_parquet(str(parquet_path))
        logger.info(f"Saved dataset to {parquet_path}")
        
        # Generate checksums for integrity verification
        checksum = compute_directory_checksum(output_path)
        logger.info(f"Computed directory checksum: {checksum}")
        
        # Generate manifest
        manifest = generate_manifest(output_path)
        manifest_path = output_path / MANIFEST_FILE
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Generated manifest at {manifest_path}")
        
        # Save checksums
        checksums = {
            "dataset_name": DATASET_NAME,
            "hf_dataset_id": HF_DATASET_ID,
            "checksum": checksum,
            "file_count": len(manifest.get("files", [])),
            "total_size_bytes": manifest.get("total_size_bytes", 0),
            "downloaded_at": str(Path(__file__).parent.stat().st_mtime)  # Simple timestamp
        }
        checksum_path = output_path / CHECKSUM_FILE
        with open(checksum_path, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Saved checksums to {checksum_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {str(e)}")
        raise RuntimeError(f"Dataset download failed: {str(e)}")

def main():
    """Main entry point for the script."""
    logger.info("Starting Persona-Chat dataset download (T015b)")
    
    try:
        # Verify environment (HF_TOKEN might be needed for authenticated datasets)
        hf_token = get_hf_token()
        if hf_token:
            logger.info("HF_TOKEN found in environment")
        else:
            logger.warning("HF_TOKEN not found - some datasets may require authentication")
        
        # Download and process dataset
        output_path = load_dataset_with_check()
        
        logger.info(f"Persona-Chat dataset successfully downloaded to {output_path}")
        logger.info("Task T015b completed successfully")
        
    except Exception as e:
        logger.error(f"Task T015b failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
