"""
Data loader module for streaming GitHub code corpus.

This module handles downloading and streaming the codeparrot/github-code dataset
using HuggingFace datasets library with streaming mode enabled.
"""
import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
import argparse

# Import datasets library - must be installed per requirements.txt
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install with: pip install datasets")


def setup_logging() -> logging.Logger:
    """Configure logging for the data loader module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def handle_rate_limit(retry_count: int = 3, base_delay: float = 1.0) -> float:
    """
    Handle HuggingFace rate limiting with exponential backoff.
    
    Args:
        retry_count: Number of retries allowed
        base_delay: Base delay in seconds between retries
        
    Returns:
        Delay time for the next retry
    """
    delay = base_delay * (2 ** retry_count) + random.uniform(0, 1)
    return delay


def handle_network_error(retry_count: int = 3) -> bool:
    """
    Handle network errors with retry logic.
    
    Args:
        retry_count: Number of retries allowed
        
    Returns:
        True if should retry, False otherwise
    """
    return retry_count > 0


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of the file checksum
    """
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def stream_dataset(
    dataset_name: str = 'codeparrot/github-code',
    config_name: Optional[str] = None,
    streaming: bool = True,
    split: str = 'train',
    max_samples: Optional[int] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset from HuggingFace Hub.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace Hub
        config_name: Dataset configuration name (optional)
        streaming: Enable streaming mode (must be True for large datasets)
        split: Dataset split to load
        max_samples: Maximum number of samples to yield (None for all)
        
    Yields:
        Dictionary containing dataset samples
        
    Raises:
        ImportError: If datasets library is not installed
        Exception: If dataset loading fails
    """
    logger = setup_logging()
    logger.info(f"Loading dataset: {dataset_name}")
    logger.info(f"Streaming mode enabled: {streaming}")
    
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            # Load dataset with streaming enabled
            load_kwargs = {
                'name': dataset_name,
                'split': split,
                'streaming': streaming
            }
            
            if config_name:
                load_kwargs['config_name'] = config_name
            
            dataset = load_dataset(**load_kwargs)
            logger.info(f"Dataset loaded successfully: {dataset_name}")
            
            # Iterate over samples
            sample_count = 0
            for sample in dataset:
                yield sample
                sample_count += 1
                
                if max_samples and sample_count >= max_samples:
                    logger.info(f"Reached max_samples limit: {max_samples}")
                    break
            
            break  # Success, exit retry loop
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                delay = handle_rate_limit(retry_count)
                logger.warning(
                    f"Error loading dataset (attempt {retry_count}/{max_retries}): {e}"
                )
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to load dataset after {max_retries} attempts: {e}")
                raise


def save_raw_data_to_csv(
    samples: Generator[Dict[str, Any], None, None],
    output_path: Path,
    max_samples: Optional[int] = None,
    sample_columns: Optional[List[str]] = None
) -> Tuple[int, str]:
    """
    Save streamed dataset samples to CSV file.
    
    Args:
        samples: Generator yielding dataset samples
        output_path: Path to output CSV file
        max_samples: Maximum number of samples to save
        sample_columns: Specific columns to include (None for all)
        
    Returns:
        Tuple of (sample_count, checksum)
        
    Raises:
        FileNotFoundError: If output directory doesn't exist
        ValueError: If no samples to save
    """
    logger = setup_logging()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory prepared: {output_path.parent}")
    
    sample_count = 0
    fieldnames = None
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = None
        
        for sample in samples:
            if max_samples and sample_count >= max_samples:
                logger.info(f"Reached max_samples limit: {max_samples}")
                break
            
            # Determine fieldnames from first sample
            if fieldnames is None:
                fieldnames = list(sample.keys())
                if sample_columns:
                    fieldnames = [f for f in fieldnames if f in sample_columns]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                logger.info(f"CSV headers: {fieldnames}")
            
            # Write sample
            if sample_columns:
                filtered_sample = {k: sample.get(k, '') for k in sample_columns}
                writer.writerow(filtered_sample)
            else:
                writer.writerow(sample)
            
            sample_count += 1
            
            if sample_count % 100 == 0:
                logger.info(f"Saved {sample_count} samples...")
    
    if sample_count == 0:
        raise ValueError("No samples were saved to CSV")
    
    # Compute checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Saved {sample_count} samples to {output_path}")
    logger.info(f"File checksum: {checksum}")
    
    return sample_count, checksum


def download_and_save_sample(
    dataset_name: str = 'codeparrot/github-code',
    output_path: Path = None,
    max_samples: int = 100,
    streaming: bool = True
) -> Tuple[int, str]:
    """
    Download a sample from the GitHub code dataset and save to CSV.
    
    This is the main entry point for the data loading pipeline.
    
    Args:
        dataset_name: HuggingFace dataset name
        output_path: Path to output CSV file
        max_samples: Number of samples to download
        streaming: Enable streaming mode (required for large datasets)
        
    Returns:
        Tuple of (sample_count, checksum)
    """
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting data download pipeline")
    logger.info("=" * 60)
    
    # Set default output path if not provided
    if output_path is None:
        output_path = Path('data/raw/github-code-sample.csv')
    
    logger.info(f"Dataset: {dataset_name}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Max samples: {max_samples}")
    logger.info(f"Streaming enabled: {streaming}")
    
    if not streaming:
        logger.warning("Streaming disabled - this may cause memory issues for large datasets")
    
    # Stream and save dataset
    samples = stream_dataset(
        dataset_name=dataset_name,
        streaming=streaming,
        max_samples=max_samples
    )
    
    sample_count, checksum = save_raw_data_to_csv(
        samples=samples,
        output_path=output_path,
        max_samples=max_samples
    )
    
    logger.info("=" * 60)
    logger.info("Data download pipeline completed successfully")
    logger.info(f"Total samples: {sample_count}")
    logger.info(f"Checksum: {checksum}")
    logger.info("=" * 60)
    
    return sample_count, checksum


def load_raw_data(
    input_path: Path = None
) -> List[Dict[str, Any]]:
    """
    Load raw data from CSV file.
    
    Args:
        input_path: Path to input CSV file
        
    Returns:
        List of dictionaries containing the data
    """
    import csv
    
    logger = setup_logging()
    
    if input_path is None:
        input_path = Path('data/raw/github-code-sample.csv')
    
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {input_path}")
    
    logger.info(f"Loading raw data from: {input_path}")
    
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} samples from {input_path}")
    return data


def main():
    """Main entry point for the data loader script."""
    parser = argparse.ArgumentParser(
        description='Stream and save GitHub code dataset samples'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw/github-code-sample.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        default=100,
        help='Maximum number of samples to download'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='codeparrot/github-code',
        help='HuggingFace dataset name'
    )
    parser.add_argument(
        '--streaming',
        type=bool,
        default=True,
        help='Enable streaming mode (default: True)'
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    
    try:
        sample_count, checksum = download_and_save_sample(
            dataset_name=args.dataset,
            output_path=output_path,
            max_samples=args.max_samples,
            streaming=args.streaming
        )
        print(f"Successfully downloaded {sample_count} samples")
        print(f"Output file: {output_path}")
        print(f"Checksum: {checksum}")
        return 0
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Data loading failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
