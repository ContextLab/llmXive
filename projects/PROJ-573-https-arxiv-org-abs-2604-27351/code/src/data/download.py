import hashlib
import os
import time
import logging
import shutil
from pathlib import Path
from typing import Tuple, Optional, Any, Dict, List
import tempfile
import requests
from datasets import load_dataset
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_data_dirs(base_dir: Optional[Path] = None) -> Path:
    """Ensure data directories exist."""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent / "data"
    
    data_dir = Path(base_dir)
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Data directories ensured at {data_dir}")
    return data_dir

def compute_dataset_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_dataset_integrity(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """Verify dataset integrity via checksum if expected is provided."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    actual_checksum = compute_dataset_checksum(file_path)
    logger.info(f"Computed checksum for {file_path}: {actual_checksum}")
    
    if expected_checksum and actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch for {file_path}")
        logger.error(f"Expected: {expected_checksum}, Got: {actual_checksum}")
        return False
    
    return True

def download_dataset(
    url: str,
    output_dir: Optional[Path] = None,
    max_retries: int = 3,
    timeout: int = 300
) -> Tuple[str, str]:
    """
    Download a dataset with retry logic.
    
    Supports:
    - HuggingFace datasets (via datasets.load_dataset)
    - Direct URLs (via requests)
    
    Args:
        url: Dataset identifier (e.g., 'UCI_HAR') or direct URL
        output_dir: Directory to save the dataset
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for each attempt
        
    Returns:
        Tuple of (path_to_dataset, checksum)
        
    Raises:
        RuntimeError: If download fails after all retries
        ValueError: If URL format is unrecognized
    """
    if output_dir is None:
        output_dir = ensure_data_dirs() / "raw"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries} for {url}")
            
            # Check if it's a HuggingFace dataset identifier
            if not url.startswith(('http://', 'https://', 'ftp://')):
                # Try HuggingFace datasets
                logger.info(f"Loading dataset '{url}' from HuggingFace...")
                dataset = load_dataset(url)
                
                # Save dataset to disk
                dataset_name = url.replace('/', '_').replace('-', '_')
                dataset_path = output_dir / dataset_name
                
                # Save dataset in parquet format (efficient and standard)
                if 'train' in dataset:
                    train_path = dataset_path / "train.parquet"
                    dataset['train'].to_parquet(str(train_path))
                    logger.info(f"Saved train split to {train_path}")
                
                if 'test' in dataset:
                    test_path = dataset_path / "test.parquet"
                    dataset['test'].to_parquet(str(test_path))
                    logger.info(f"Saved test split to {test_path}")
                
                # Compute checksum of the directory (aggregate of files)
                checksum = compute_directory_checksum(dataset_path)
                logger.info(f"Dataset '{url}' downloaded successfully. Checksum: {checksum}")
                return str(dataset_path), checksum
            
            else:
                # Direct URL download
                filename = url.split('/')[-1] or "dataset"
                local_path = output_dir / filename
                
                logger.info(f"Downloading from URL: {url}")
                response = requests.get(url, stream=True, timeout=timeout)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                checksum = compute_dataset_checksum(local_path)
                logger.info(f"Downloaded {local_path}. Checksum: {checksum}")
                return str(local_path), checksum
                
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed for {url}")
    
    raise RuntimeError(f"Failed to download dataset {url} after {max_retries} attempts. Last error: {str(last_exception)}")

def compute_directory_checksum(dir_path: Path) -> str:
    """Compute a combined checksum for all files in a directory."""
    combined_hash = hashlib.sha256()
    
    # Sort files for deterministic ordering
    files = sorted(dir_path.rglob("*"))
    
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash
            relative_path = file_path.relative_to(dir_path)
            combined_hash.update(relative_path.as_posix().encode())
            
            # Include file content in hash
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    combined_hash.update(chunk)
    
    return combined_hash.hexdigest()

def main():
    """Main entry point for dataset download verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and verify datasets")
    parser.add_argument(
        "--dataset",
        type=str,
        default="UCI_HAR",
        help="Dataset identifier (e.g., 'UCI_HAR', 'DROP')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/raw)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds"
    )
    
    args = parser.parse_args()
    
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        path, checksum = download_dataset(
            url=args.dataset,
            output_dir=output_dir,
            max_retries=args.max_retries,
            timeout=args.timeout
        )
        
        print(f"SUCCESS: Dataset downloaded to {path}")
        print(f"Checksum: {checksum}")
        
        # Update research.md if needed (optional)
        # This would be handled by a separate research update task
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
