"""
Data loader module for downloading and streaming code datasets.

This module handles downloading code datasets from HuggingFace,
with streaming support, error handling, and checksum computation.
"""
import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
import pandas as pd
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def handle_rate_limit(retry_count: int = 3, base_delay: float = 1.0) -> bool:
    """Handle rate limiting with exponential backoff."""
    for attempt in range(retry_count):
        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
        logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1})")
        time.sleep(delay)
    return False

def handle_network_error(retry_count: int = 3) -> bool:
    """Handle network errors with retry logic."""
    for attempt in range(retry_count):
        delay = 2 ** attempt
        logger.warning(f"Network error, retrying in {delay}s (attempt {attempt + 1})")
        time.sleep(delay)
    return False

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Compute checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def stream_dataset(
    dataset_name: str = "codeparrot/github-code-clean",
    split: str = "train",
    streaming: bool = True,
    max_samples: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace
        split: Dataset split to load
        streaming: Whether to use streaming mode
        max_samples: Maximum number of samples to yield
        
    Yields:
        Dictionary containing dataset samples
    """
    try:
        from datasets import load_dataset
        
        logger.info(f"Loading dataset: {dataset_name}")
        
        # Use streaming mode for large datasets
        if streaming:
            dataset = load_dataset(dataset_name, split=split, streaming=True)
        else:
            dataset = load_dataset(dataset_name, split=split)
        
        sample_count = 0
        for sample in dataset:
            yield sample
            sample_count += 1
            if max_samples and sample_count >= max_samples:
                break
                
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        raise

def save_raw_data_to_csv(
    samples: List[Dict[str, Any]],
    output_path: Path,
    columns: Optional[List[str]] = None
) -> None:
    """
    Save raw data samples to CSV file.
    
    Args:
        samples: List of dictionaries containing data samples
        output_path: Path to output CSV file
        columns: Optional list of columns to include
    """
    if not samples:
        logger.warning("No samples to save")
        return
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine columns from first sample if not provided
    if columns is None:
        columns = list(samples[0].keys())
    
    # Filter to only include existing columns
    valid_columns = [col for col in columns if col in samples[0]]
    
    # Create DataFrame and save
    df = pd.DataFrame(samples)
    df = df[valid_columns]
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(samples)} samples to {output_path}")

def download_and_save_sample(
    output_path: Path,
    max_samples: int = 1000,
    dataset_name: str = "codeparrot/github-code-clean"
) -> Tuple[bool, str]:
    """
    Download dataset and save sample to CSV.
    
    Args:
        output_path: Path to save the CSV file
        max_samples: Maximum number of samples to download
        dataset_name: Name of the HuggingFace dataset
        
    Returns:
        Tuple of (success, message)
    """
    output_path = Path(output_path)
    
    try:
        logger.info(f"Downloading dataset: {dataset_name}")
        logger.info(f"Max samples: {max_samples}")
        
        samples = []
        for sample in stream_dataset(
            dataset_name=dataset_name,
            streaming=True,
            max_samples=max_samples
        ):
            samples.append(sample)
            
        if not samples:
            return False, "No samples downloaded"
            
        save_raw_data_to_csv(samples, output_path)
        
        # Compute checksum
        checksum = compute_file_checksum(output_path)
        logger.info(f"File checksum: {checksum}")
        
        return True, f"Successfully downloaded {len(samples)} samples"
        
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def load_raw_data(
    input_path: Path,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load raw data from CSV file.
    
    Args:
        input_path: Path to input CSV file
        columns: Optional list of columns to load
        
    Returns:
        DataFrame containing the data
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if columns:
        df = df[[col for col in columns if col in df.columns]]
        
    return df

def main():
    """Main entry point for data loading."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and save code dataset")
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/github-code-sample.csv",
        help="Output path for CSV file"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=1000,
        help="Maximum number of samples to download"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="codeparrot/github-code-clean",
        help="HuggingFace dataset name"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    success, message = download_and_save_sample(
        output_path=output_path,
        max_samples=args.max_samples,
        dataset_name=args.dataset
    )
    
    if success:
        logger.info(message)
    else:
        logger.error(message)
        exit(1)

if __name__ == "__main__":
    main()
