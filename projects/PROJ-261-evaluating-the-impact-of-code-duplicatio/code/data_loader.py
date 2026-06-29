import logging
import time
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

def handle_rate_limit(retry_count: int = 3, base_delay: float = 1.0):
    """
    Handle HuggingFace rate limiting with exponential backoff.
    
    Args:
        retry_count: Maximum number of retries
        base_delay: Base delay in seconds
    
    Returns:
        Decorator function for rate limit handling
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retry_count):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited, waiting {delay:.2f}s (attempt {attempt + 1}/{retry_count})")
                        time.sleep(delay)
                    else:
                        raise
            raise Exception(f"Failed after {retry_count} retries due to rate limiting")
        return wrapper
    return decorator

def handle_network_error(retry_count: int = 3, timeout: float = 30.0):
    """
    Handle network interruptions with retry logic.
    
    Args:
        retry_count: Maximum number of retries
        timeout: Request timeout in seconds
    
    Returns:
        Decorator function for network error handling
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retry_count):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "network" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                        delay = 2 ** attempt
                        logger.warning(f"Network error, retrying in {delay}s (attempt {attempt + 1}/{retry_count})")
                        time.sleep(delay)
                    else:
                        raise
            raise Exception(f"Failed after {retry_count} retries due to network errors")
        return wrapper
    return decorator

def load_raw_data(data_path: str | Path, streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    Load raw data with streaming support and error handling.
    
    Args:
        data_path: Path to data file or dataset identifier
        streaming: Whether to use streaming mode
    
    Yields:
        Dictionary of data records
    """
    data_path = Path(data_path)
    
    try:
        if streaming and data_path.exists():
            # Stream from CSV file
            df = pd.read_csv(data_path, chunksize=1000)
            for chunk in df:
                for _, row in chunk.iterrows():
                    yield row.to_dict()
        elif data_path.exists():
            # Load entire file
            df = pd.read_csv(data_path)
            for _, row in df.iterrows():
                yield row.to_dict()
        else:
            logger.warning(f"Data path not found: {data_path}")
            # Return empty generator
            return
            
    except Exception as e:
        logger.error(f"Failed to load raw data from {data_path}: {e}")
        raise

def stream_dataset(dataset_name: str = "codeparrot/github-code", 
                  config: str = "python",
                  split: str = "train",
                  streaming: bool = True,
                  max_samples: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Stream dataset from HuggingFace with error handling.
    
    Args:
        dataset_name: HuggingFace dataset name
        config: Dataset configuration
        split: Dataset split
        streaming: Whether to use streaming mode
        max_samples: Maximum number of samples to yield
    
    Yields:
        Dataset records
    """
    try:
        from datasets import load_dataset
        
        dataset = load_dataset(
            dataset_name,
            config,
            split=split,
            streaming=streaming
        )
        
        sample_count = 0
        for record in dataset:
            yield record
            sample_count += 1
            if max_samples and sample_count >= max_samples:
                break
                
    except ImportError as e:
        logger.error(f"datasets library not available: {e}")
        # Return empty generator
        return
    except Exception as e:
        logger.error(f"Failed to stream dataset: {e}")
        raise

def save_raw_data_to_csv(data: List[Dict[str, Any]], output_path: str | Path):
    """
    Save raw data to CSV file with error handling.
    
    Args:
        data: List of data dictionaries
        output_path: Path to save CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(data)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save data to {output_path}: {e}")
        raise

def download_and_save_sample(dataset_name: str = "codeparrot/github-code",
                             output_path: str | Path = "data/raw/github-code-sample.csv",
                             max_samples: int = 100,
                             streaming: bool = True):
    """
    Download and save a sample of the dataset.
    
    Args:
        dataset_name: HuggingFace dataset name
        output_path: Path to save CSV file
        max_samples: Maximum number of samples to download
        streaming: Whether to use streaming mode
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading sample from {dataset_name} (max {max_samples} samples)")
    
    try:
        data = []
        for record in stream_dataset(dataset_name, max_samples=max_samples, streaming=streaming):
            data.append(record)
        
        if data:
            save_raw_data_to_csv(data, output_path)
        else:
            logger.warning("No data downloaded, creating empty file")
            output_path.touch()
            
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        # Create empty file to indicate attempted download
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        raise

def main():
    """Main entry point for data loader."""
    logging.basicConfig(level=logging.INFO)
    
    # Test download
    output_path = Path("data/raw/github-code-sample.csv")
    try:
        download_and_save_sample(max_samples=10, streaming=True)
        print(f"Downloaded data to {output_path}")
    except Exception as e:
        print(f"Download failed: {e}")

if __name__ == "__main__":
    main()
