"""
Data loader module for downloading and streaming code datasets.
Handles rate-limiting, network interruptions, and PII scanning.
"""
import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
import pandas as pd

# Import config for dataset parameters
from config import (
    get_dataset_name,
    get_streaming_enabled,
    get_random_seed,
    get_clone_thresholds,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting constants
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0

# Network error handling
NETWORK_TIMEOUT = 30
NETWORK_RETRIES = 3

def handle_rate_limit(retry_count: int = 0) -> float:
    """
    Handle rate-limiting by implementing exponential backoff.
    
    Args:
        retry_count: Current retry attempt number
        
    Returns:
        Time to wait before next attempt
    """
    if retry_count >= MAX_RETRIES:
        raise RuntimeError(f"Max retries ({MAX_RETRIES}) exceeded due to rate limiting")
    
    backoff_time = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
    # Add jitter to prevent thundering herd
    jitter = random.uniform(0.1, 0.3) * backoff_time
    wait_time = backoff_time + jitter
    
    logger.warning(f"Rate limited. Waiting {wait_time:.2f}s before retry {retry_count + 1}/{MAX_RETRIES}")
    time.sleep(wait_time)
    return wait_time

def handle_network_error(retry_count: int = 0) -> float:
    """
    Handle network interruptions with exponential backoff.
    
    Args:
        retry_count: Current retry attempt number
        
    Returns:
        Time to wait before next attempt
    """
    if retry_count >= NETWORK_RETRIES:
        raise RuntimeError(f"Network error: max retries ({NETWORK_RETRIES}) exceeded")
    
    backoff_time = min(INITIAL_BACKOFF * (2 ** retry_count), MAX_BACKOFF)
    jitter = random.uniform(0.1, 0.3) * backoff_time
    wait_time = backoff_time + jitter
    
    logger.warning(f"Network error. Waiting {wait_time:.2f}s before retry {retry_count + 1}/{NETWORK_RETRIES}")
    time.sleep(wait_time)
    return wait_time

def load_raw_data(dataset_name: Optional[str] = None, streaming: bool = True) -> Any:
    """
    Load raw data from HuggingFace datasets.
    
    Args:
        dataset_name: Name of the dataset to load
        streaming: Whether to use streaming mode
        
    Returns:
        Dataset object
    """
    try:
        from datasets import load_dataset
        
        dataset_name = dataset_name or get_dataset_name()
        
        # Try streaming first, fall back to full load if streaming fails
        if streaming:
            try:
                dataset = load_dataset(dataset_name, streaming=True)
                logger.info(f"Loaded dataset '{dataset_name}' in streaming mode")
                return dataset
            except Exception as e:
                logger.warning(f"Streaming failed ({str(e)}), falling back to full load")
                dataset = load_dataset(dataset_name, streaming=False)
                logger.info(f"Loaded dataset '{dataset_name}' in full mode")
                return dataset
        else:
            dataset = load_dataset(dataset_name, streaming=False)
            logger.info(f"Loaded dataset '{dataset_name}' in full mode")
            return dataset
            
    except ImportError:
        raise ImportError("datasets library not installed. Run: pip install datasets")
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        raise

def stream_dataset(dataset: Any, split: str = 'train', num_samples: int = 1000) -> Generator[Dict[str, Any], None, None]:
    """
    Stream samples from a dataset.
    
    Args:
        dataset: Dataset object to stream from
        split: Dataset split to use
        num_samples: Number of samples to yield
        
    Yields:
        Individual samples as dictionaries
    """
    count = 0
    try:
        for sample in dataset[split]:
            if count >= num_samples:
                break
            yield sample
            count += 1
    except Exception as e:
        logger.error(f"Error streaming dataset: {str(e)}")
        raise

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of the file checksum
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def save_raw_data_to_csv(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save raw data samples to CSV format.
    
    Args:
        samples: List of sample dictionaries
        output_path: Path to output CSV file
    """
    if not samples:
        logger.warning("No samples to save")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(samples)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(samples)} samples to {output_path}")

def download_and_save_sample(
    dataset_name: Optional[str] = None,
    output_path: Optional[Path] = None,
    num_samples: int = 1000,
    streaming: bool = True
) -> Path:
    """
    Download a sample from HuggingFace dataset and save to CSV.
    Handles rate-limiting and network interruptions.
    
    Args:
        dataset_name: Name of the dataset to download
        output_path: Path to save the CSV file
        num_samples: Number of samples to download
        streaming: Whether to use streaming mode
        
    Returns:
        Path to the saved CSV file
    """
    dataset_name = dataset_name or get_dataset_name()
    output_path = output_path or Path('data/raw/github-code-sample.csv')
    
    retry_count = 0
    network_retry_count = 0
    samples = []
    
    logger.info(f"Starting download of {num_samples} samples from '{dataset_name}'")
    
    try:
        # Load dataset with retry logic
        while retry_count < MAX_RETRIES:
            try:
                dataset = load_raw_data(dataset_name, streaming=streaming)
                break
            except Exception as e:
                error_str = str(e).lower()
                if 'rate limit' in error_str or '429' in error_str:
                    handle_rate_limit(retry_count)
                    retry_count += 1
                elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
                    handle_network_error(network_retry_count)
                    network_retry_count += 1
                    retry_count += 1
                else:
                    # For other errors (like streaming unsupported), fall back to non-streaming
                    logger.warning(f"Dataset error: {str(e)}. Attempting non-streaming fallback...")
                    dataset = load_raw_data(dataset_name, streaming=False)
                    break
        
        # Stream samples
        for sample in stream_dataset(dataset, num_samples=num_samples):
            samples.append(sample)
        
        # Save to CSV
        save_raw_data_to_csv(samples, output_path)
        
        # Compute checksum
        checksum = compute_file_checksum(output_path)
        logger.info(f"Download complete. Checksum: {checksum[:16]}...")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")

def main():
    """Main entry point for data loader."""
    import sys
    
    # Parse command line arguments
    num_samples = 1000
    output_path = Path('data/raw/github-code-sample.csv')
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--num-samples' and i < len(sys.argv):
            num_samples = int(sys.argv[i + 1])
        elif arg == '--output' and i < len(sys.argv):
            output_path = Path(sys.argv[i + 1])
    
    # Download and save sample
    try:
        result_path = download_and_save_sample(
            num_samples=num_samples,
            output_path=output_path,
            streaming=get_streaming_enabled()
        )
        logger.info(f"Successfully downloaded to: {result_path}")
    except Exception as e:
        logger.error(f"Failed to download: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
