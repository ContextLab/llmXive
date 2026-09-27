"""
Data download module for CodeSearchNet dataset.

This module handles fetching the CodeSearchNet dataset using ir_datasets.
It strictly adheres to the requirement of failing loudly on any fetch failure
and NEVER provides synthetic fallback data.
"""
import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator

import ir_datasets

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "codesearchnet"
SUPPORTED_SUBSETS = ["python", "java", "go", "ruby", "javascript", "php"]
RAW_DATA_DIR = Path("data/raw")
CHECKSUM_FILE = RAW_DATA_DIR / "checksums.json"
STATE_FILE = RAW_DATA_DIR / "state.json"

def ensure_directories() -> None:
    """Create necessary directories for raw data and state files."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DATA_DIR / "python").mkdir(parents=True, exist_ok=True)
    (RAW_DATA_DIR / "java").mkdir(parents=True, exist_ok=True)
    # Create other subset directories if needed
    for subset in SUPPORTED_SUBSETS:
        if subset not in ["python", "java"]:
            (RAW_DATA_DIR / subset).mkdir(parents=True, exist_ok=True)

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """Load the state file tracking downloaded datasets."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"datasets": {}}

def save_state(state: Dict[str, Any]) -> None:
    """Save the state file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_dataset_subset(subset: str) -> Iterator[Dict[str, Any]]:
    """
    Load a specific subset of the CodeSearchNet dataset.
    
    Args:
        subset: The language subset to load (e.g., 'python', 'java').
        
    Returns:
        An iterator over dataset items.
        
    Raises:
        RuntimeError: If the dataset cannot be loaded or the subset is invalid.
        FileNotFoundError: If the dataset is not available locally and cannot be downloaded.
    """
    if subset not in SUPPORTED_SUBSETS:
        raise ValueError(f"Invalid subset '{subset}'. Supported: {SUPPORTED_SUBSETS}")
    
    try:
        logger.info(f"Loading dataset subset: {DATASET_ID}.{subset}")
        # ir_datasets returns an iterable of Dataset objects
        # We need to access the 'train' or 'test' split depending on usage
        # For this implementation, we load the 'train' split as per common usage
        dataset = ir_datasets.load(f"{DATASET_ID}/{subset}")
        
        # Verify we can iterate (this triggers the download if needed)
        # We don't consume it here, just ensure it's accessible
        if not hasattr(dataset, 'docs_iter'):
            # Fallback for newer ir_datasets versions
            if not hasattr(dataset, 'docs'):
                raise RuntimeError(f"Dataset {DATASET_ID}/{subset} does not have expected docs interface")
        
        logger.info(f"Successfully loaded dataset subset: {DATASET_ID}.{subset}")
        return dataset.docs_iter()
        
    except Exception as e:
        # CRITICAL: Do NOT fallback to synthetic data.
        # Raise a clear error so the pipeline fails visibly.
        raise RuntimeError(f"Failed to load dataset subset '{DATASET_ID}.{subset}': {str(e)}") from e

def download_and_save_subset(subset: str, limit: Optional[int] = None) -> Path:
    """
    Download a subset of the dataset and save it to a JSONL file.
    
    Args:
        subset: The language subset to download.
        limit: Optional limit on the number of records to save.
        
    Returns:
        Path to the saved JSONL file.
        
    Raises:
        RuntimeError: If download fails or data cannot be saved.
    """
    ensure_directories()
    
    output_file = RAW_DATA_DIR / subset / f"{subset}_raw.jsonl"
    
    if output_file.exists():
        logger.info(f"Dataset subset {subset} already exists at {output_file}. Skipping download.")
        return output_file
    
    try:
        docs_iter = load_dataset_subset(subset)
        
        logger.info(f"Saving dataset subset {subset} to {output_file}")
        saved_count = 0
        
        with open(output_file, "w", encoding="utf-8") as f:
            for i, doc in enumerate(docs_iter):
                if limit and saved_count >= limit:
                    break
                
                # Convert doc object to dictionary
                doc_dict = {
                    "repo": getattr(doc, 'repo', None),
                    "path": getattr(doc, 'path', None),
                    "language": getattr(doc, 'language', None),
                    "func_name": getattr(doc, 'func_name', None),
                    "func_documentation": getattr(doc, 'func_documentation', None),
                    "func_code": getattr(doc, 'func_code', None),
                }
                
                # Filter out None values for cleaner storage
                doc_dict = {k: v for k, v in doc_dict.items() if v is not None}
                
                f.write(json.dumps(doc_dict) + "\n")
                saved_count += 1
                
                if saved_count % 1000 == 0:
                    logger.info(f"Saved {saved_count} records for {subset}")
        
        logger.info(f"Successfully saved {saved_count} records for {subset} to {output_file}")
        
        # Update state
        state = load_state()
        state["datasets"][subset] = {
            "path": str(output_file),
            "count": saved_count,
            "hash": calculate_file_hash(output_file)
        }
        save_state(state)
        
        return output_file
        
    except Exception as e:
        # Ensure partial file is removed if download fails
        if output_file.exists():
            output_file.unlink()
        raise RuntimeError(f"Failed to download and save subset '{subset}': {str(e)}") from e

def verify_download(subset: str) -> bool:
    """
    Verify the integrity of a downloaded dataset subset.
    
    Args:
        subset: The language subset to verify.
        
    Returns:
        True if verification passes, False otherwise.
    """
    state = load_state()
    if subset not in state.get("datasets", {}):
        logger.warning(f"No state record for subset {subset}")
        return False
    
    record = state["datasets"][subset]
    file_path = Path(record["path"])
    
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist for subset {subset}")
        return False
    
    current_hash = calculate_file_hash(file_path)
    expected_hash = record["hash"]
    
    if current_hash != expected_hash:
        logger.error(f"Hash mismatch for {subset}: expected {expected_hash}, got {current_hash}")
        return False
    
    logger.info(f"Verification passed for subset {subset}")
    return True

def main():
    """Main entry point to download all supported subsets."""
    logger.info("Starting CodeSearchNet dataset download")
    ensure_directories()
    
    # Download Python and Java subsets as primary targets
    # Per task description: "fetch Python/Java subsets"
    subsets_to_download = ["python", "java"]
    
    for subset in subsets_to_download:
        try:
            output_path = download_and_save_subset(subset)
            logger.info(f"Downloaded {subset} to {output_path}")
            
            if not verify_download(subset):
                logger.warning(f"Verification failed for {subset}")
                
        except RuntimeError as e:
            logger.error(f"Critical error downloading {subset}: {e}")
            # Re-raise to ensure the pipeline fails loudly as required
            raise
        
    logger.info("All requested subsets downloaded successfully")

if __name__ == "__main__":
    main()