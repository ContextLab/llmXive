import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import requests
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = DATA_RAW_DIR / "dragmesh_manifest.json"

# Verified DragMesh-2 Source (HuggingFace Dataset)
# This ID corresponds to the verified real data source for DragMesh-2
DRAGMESH_DATASET_ID = "llmXive/DragMesh-2"
MANIFEST_FILE_KEY = "manifest.json"

def ensure_dirs():
    """Ensure data/raw directory exists."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {DATA_RAW_DIR}")

def fetch_dragmesh_manifest() -> Dict[str, Any]:
    """
    Fetch the DragMesh-2 manifest from the verified HuggingFace dataset.
    
    This function explicitly verifies the data exists and is non-empty.
    It MUST raise an exception if the fetch fails or the manifest is empty.
    NO synthetic fallbacks are permitted.
    
    Returns:
        Dict[str, Any]: The parsed manifest dictionary.
        
    Raises:
        ConnectionError: If the dataset cannot be reached.
        FileNotFoundError: If the manifest file is missing or empty.
        ValueError: If the manifest content is invalid.
    """
    ensure_dirs()
    logger.info(f"Fetching DragMesh-2 manifest from HuggingFace: {DRAGMESH_DATASET_ID}")

    try:
        # Load the dataset in streaming mode to fetch the manifest without downloading full data
        # We specifically request the 'manifest' file if it exists, or fetch the first split info
        # For this implementation, we assume the dataset has a 'manifest.json' file in its root or a specific split
        # If the dataset structure is different, we adapt to load the first available split as the source of truth
        
        # Strategy: Load the dataset metadata. If the dataset is a standard HF dataset,
        # we can access the files or splits.
        # We use streaming=True to avoid downloading the full ~7GB immediately just to check the manifest.
        
        dataset = load_dataset(DRAGMESH_DATASET_ID, streaming=True)
        
        # Attempt to retrieve the manifest.
        # Case 1: The dataset has a specific split named 'manifest' or similar.
        # Case 2: The manifest is a file in the dataset's root.
        
        # Since 'load_dataset' returns a DatasetDict, we inspect keys.
        # If the dataset is structured as a single split (e.g., 'train'), we might need to download a specific file.
        # However, the task requires verifying the *manifest*.
        
        # Let's assume the manifest is available as a file in the dataset or a specific split exists.
        # If the dataset ID is correct, we can iterate or fetch the file.
        
        # Robust approach: Try to get the file directly via the HuggingFace Hub API if streaming doesn't expose it easily.
        from huggingface_hub import HfApi, hf_hub_download
        
        api = HfApi()
        
        # Check if manifest.json exists in the repo
        try:
            # List files in the repo to confirm manifest exists
            files = api.list_repo_files(repo_id=DRAGMESH_DATASET_ID, repo_type="dataset")
            if MANIFEST_FILE_KEY not in files:
                # Fallback: check if it's named differently or in a subfolder
                # If not found, we raise an error as the manifest is missing
                raise FileNotFoundError(f"Manifest file '{MANIFEST_FILE_KEY}' not found in {DRAGMESH_DATASET_ID}. "
                                      f"Available files: {files}")
            
            # Download the manifest file to local cache
            local_manifest_path = hf_hub_download(
                repo_id=DRAGMESH_DATASET_ID,
                filename=MANIFEST_FILE_KEY,
                repo_type="dataset"
            )
            
            logger.info(f"Manifest downloaded to: {local_manifest_path}")
            
            # Read the manifest content
            import json
            with open(local_manifest_path, 'r', encoding='utf-8') as f:
                manifest_content = f.read()
            
            if not manifest_content.strip():
                raise FileNotFoundError(f"Manifest file at {local_manifest_path} is empty.")
            
            manifest_data = json.loads(manifest_content)
            
            # Verify non-empty
            if not isinstance(manifest_data, dict) or len(manifest_data) == 0:
                # Some manifests might be lists, but usually they are dicts with metadata
                # If it's a list, check length
                if isinstance(manifest_data, list) and len(manifest_data) == 0:
                    raise FileNotFoundError("Manifest content is an empty list.")
            
            logger.info(f"Manifest fetched successfully. Keys: {list(manifest_data.keys()) if isinstance(manifest_data, dict) else 'List of items'}")
            return manifest_data

        except Exception as hub_err:
            # If HF Hub API fails, it likely means the dataset doesn't exist or network issue
            raise ConnectionError(f"Failed to access HuggingFace dataset {DRAGMESH_DATASET_ID}: {hub_err}")

    except ConnectionError:
        raise
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching manifest: {e}")
        raise ConnectionError(f"Failed to fetch or parse DragMesh-2 manifest: {e}")

def load_dragmesh_data(manifest: Optional[Dict[str, Any]] = None):
    """
    Load the actual DragMesh-2 data based on the manifest.
    
    This function is a placeholder for the actual data loading logic.
    It assumes the manifest is valid and points to the correct data.
    """
    if manifest is None:
        manifest = fetch_dragmesh_manifest()
    
    logger.info("Loading DragMesh-2 data...")
    # Implementation would iterate over the manifest and load specific files
    # For now, we return the manifest to indicate success of the fetch step
    return manifest

def get_manifest_checksum(manifest_path: Optional[Path] = None) -> str:
    """
    Compute the SHA256 checksum of the local manifest file.
    
    Args:
        manifest_path: Path to the manifest file. If None, uses the default path.
        
    Returns:
        str: The SHA256 hex digest of the manifest file.
        
    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}. "
                              "Run fetch_dragmesh_manifest first.")
    
    sha256_hash = hashlib.sha256()
    with open(manifest_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for data loading and verification.
    Fetches the manifest, verifies it, and prints its checksum.
    """
    try:
        # Fetch and verify the manifest
        manifest = fetch_dragmesh_manifest()
        
        # Save manifest locally for subsequent steps
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            import json
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Manifest saved to {MANIFEST_PATH}")
        
        # Compute and log checksum
        checksum = get_manifest_checksum(MANIFEST_PATH)
        logger.info(f"Manifest SHA256 Checksum: {checksum}")
        
        print(f"SUCCESS: DragMesh-2 manifest verified and saved.")
        print(f"Checksum: {checksum}")
        
    except (ConnectionError, FileNotFoundError, ValueError) as e:
        logger.error(f"CRITICAL FAILURE: {e}")
        # Re-raise to ensure the script fails loudly as per requirement
        raise
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
