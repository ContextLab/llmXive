import os
import time
import logging
import shutil
import gc
import sys
import traceback
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

# Try importing huggingface_hub; if missing, we will handle it gracefully in main
try:
    from huggingface_hub import HfApi, hf_hub_download, list_repo_files, login
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False

# Try importing pandas and numpy for dtype optimization
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from config import get_config, require_data_dir
from utils.logging_config import setup_logging, get_logger, log_download_progress
from utils.integrity import compute_sha256, log_checksum

# Constants for chunked loading and memory management
CHUNK_SIZE = 10000  # Rows per batch
TARGET_MEMORY_GB = 6.0  # Target peak RAM to stay under (leaving 1GB buffer)
DTYPE_MAP = {
    'float64': 'float32',
    'int64': 'int32',
    'int32': 'int32',
    'float32': 'float32',
}

class DownloadError(Exception):
    """Custom exception for download failures."""
    pass

@contextmanager
def memory_monitor(threshold_gb: float = TARGET_MEMORY_GB):
    """Context manager to monitor memory usage (best-effort on Linux)."""
    import resource
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert KB to MB
    start_mem_gb = start_mem / 1024
    logger = get_logger(__name__)
    logger.info(f"Memory monitor started. Start usage: {start_mem_gb:.2f} GB. Threshold: {threshold_gb} GB.")
    try:
        yield
    finally:
        current_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        current_mem_gb = current_mem / 1024
        delta = current_mem_gb - start_mem_gb
        logger.info(f"Memory monitor finished. Peak usage: {current_mem_gb:.2f} GB. Delta: {delta:.2f} GB.")
        if current_mem_gb > threshold_gb:
            logger.warning(f"Memory usage ({current_mem_gb:.2f} GB) exceeded threshold ({threshold_gb} GB).")

def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    return delay

def download_with_retry(
    repo_id: str,
    filename: str,
    output_dir: Path,
    max_retries: int = 5,
    token: Optional[str] = None
) -> Path:
    """Download a file from HuggingFace with exponential backoff."""
    if not HF_HUB_AVAILABLE:
        raise DownloadError("huggingface_hub is not installed. Please install it via 'pip install huggingface_hub'.")
    
    if token:
        login(token=token)

    last_exception = None
    for attempt in range(max_retries):
        try:
            logger = get_logger(__name__)
            logger.info(f"Downloading {filename} from {repo_id} (Attempt {attempt + 1}/{max_retries})...")
            local_path = hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=output_dir / "cache")
            # Move from cache to final destination if needed, or just return cache path
            # For this implementation, we assume hf_hub_download returns the path to the file
            logger.info(f"Successfully downloaded to {local_path}")
            return Path(local_path)
        except Exception as e:
            last_exception = e
            delay = exponential_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    raise DownloadError(f"Failed to download {filename} after {max_retries} retries. Last error: {last_exception}")

def fetch_dataset_metadata(repo_id: str) -> Dict[str, Any]:
    """Fetch metadata about a dataset repository."""
    if not HF_HUB_AVAILABLE:
        raise DownloadError("huggingface_hub is not installed.")
    
    try:
        api = HfApi()
        info = api.dataset_info(repo_id=repo_id)
        return {
            'id': info.id,
            'description': info.description,
            'siblings': [s.rfilename for s in info.siblings] if info.siblings else []
        }
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to fetch metadata for {repo_id}: {e}")
        return {}

def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize dataframe dtypes to reduce memory usage (float64 -> float32, etc)."""
    if not PANDAS_AVAILABLE:
        return df
    
    logger = get_logger(__name__)
    original_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    for col in df.columns:
        col_type = df[col].dtype
        if col_type == 'float64':
            df[col] = df[col].astype('float32')
        elif col_type == 'int64':
            # Check if int32 is sufficient
            if df[col].max() <= np.iinfo(np.int32).max and df[col].min() >= np.iinfo(np.int32).min:
                df[col] = df[col].astype('int32')
    
    new_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    reduction = ((original_mem - new_mem) / original_mem) * 100
    logger.info(f"Memory optimization: {original_mem:.2f} MB -> {new_mem:.2f} MB ({reduction:.1f}% reduction)")
    return df

def load_dataframe_chunked(file_path: Path, chunk_size: int = CHUNK_SIZE) -> pd.DataFrame:
    """Load a large CSV/Parquet file in chunks and optimize dtypes."""
    if not PANDAS_AVAILABLE:
        raise DownloadError("pandas is not installed.")
    
    logger = get_logger(__name__)
    logger.info(f"Loading {file_path} in chunks of {chunk_size}...")
    
    chunks = []
    total_rows = 0
    
    try:
        # Determine file type
        suffix = file_path.suffix.lower()
        if suffix == '.parquet':
            # Parquet can be read in chunks with pyarrow, but pandas read_parquet doesn't support chunking directly
            # We'll load in one go but optimize dtypes immediately
            df = pd.read_parquet(file_path)
            df = optimize_dataframe_dtypes(df)
            return df
        elif suffix == '.csv':
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                chunk = optimize_dataframe_dtypes(chunk)
                chunks.append(chunk)
                total_rows += len(chunk)
                if total_rows % 100000 == 0:
                    gc.collect()
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        raise

    if not chunks:
        logger.warning(f"No data loaded from {file_path}")
        return pd.DataFrame()
    
    logger.info(f"Concatenating {len(chunks)} chunks...")
    df = pd.concat(chunks, ignore_index=True)
    gc.collect()
    
    # Final memory check
    final_mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
    logger.info(f"Final loaded size: {final_mem:.2f} MB")
    
    return df

def process_property_files(
    repo_id: str,
    output_dir: Path,
    token: Optional[str] = None
) -> List[Path]:
    """Download all relevant files for a property dataset."""
    logger = get_logger(__name__)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = fetch_dataset_metadata(repo_id)
    if not metadata:
        raise DownloadError(f"Could not fetch metadata for {repo_id}")
    
    files_to_download = metadata.get('siblings', [])
    downloaded_files = []
    
    for filename in files_to_download:
        # Filter for data files (csv, parquet, json)
        if filename.endswith(('.csv', '.parquet', '.json')):
            local_path = download_with_retry(repo_id, filename, output_dir, token=token)
            downloaded_files.append(local_path)
            # Log checksum
            log_checksum(local_path, output_dir / "checksums.json")
    
    return downloaded_files

def download_all_datasets(
    dataset_list: List[str],
    output_base_dir: Path,
    token: Optional[str] = None
) -> Dict[str, List[Path]]:
    """Download multiple datasets from the provided list."""
    logger = get_logger(__name__)
    results = {}
    
    for repo_id in dataset_list:
        logger.info(f"Processing dataset: {repo_id}")
        try:
            files = process_property_files(repo_id, output_base_dir, token)
            results[repo_id] = files
        except DownloadError as e:
            logger.error(f"Failed to download {repo_id}: {e}")
            results[repo_id] = []
        except Exception as e:
            logger.error(f"Unexpected error processing {repo_id}: {e}")
            results[repo_id] = []
    
    return results

def main():
    """Main entry point for data download with chunked loading and memory monitoring."""
    parser = argparse.ArgumentParser(description="Download material property datasets with memory optimization.")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory for raw data")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--datasets", type=str, nargs="+", help="List of dataset IDs to download (overrides config)")
    args = parser.parse_args()

    # Setup logging
    log_dir = Path("state/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=log_dir / "download_data.log")
    logger = get_logger(__name__)

    logger.info("Starting data download with chunked loading and memory optimization.")

    # Check dependencies
    if not HF_HUB_AVAILABLE:
        logger.error("huggingface_hub is not installed. Please run: pip install huggingface_hub")
        sys.exit(1)
    
    if not PANDAS_AVAILABLE:
        logger.error("pandas is not installed. Please run: pip install pandas")
        sys.exit(1)

    # Load config or use defaults
    try:
        config = get_config(args.config)
        token = config.get('huggingface_token')
        # Default datasets if not specified in args
        default_datasets = config.get('datasets', [])
        dataset_list = args.datasets if args.datasets else default_datasets
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using default datasets.")
        dataset_list = args.datasets if args.datasets else []
        token = None

    if not dataset_list:
        logger.error("No datasets specified. Please provide --datasets or configure in config.yaml.")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Monitor memory during download
    with memory_monitor(TARGET_MEMORY_GB):
        results = download_all_datasets(dataset_list, output_dir, token)

    # Summary
    total_files = sum(len(files) for files in results.values())
    logger.info(f"Download complete. Total files: {total_files}")
    
    # Verify memory usage one last time
    import resource
    current_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024  # GB
    logger.info(f"Final memory usage: {current_mem:.2f} GB")
    
    if current_mem > TARGET_MEMORY_GB:
        logger.warning(f"Final memory usage ({current_mem:.2f} GB) exceeded target ({TARGET_MEMORY_GB} GB).")
    else:
        logger.info(f"Memory usage stayed within target ({TARGET_MEMORY_GB} GB).")

    return results

if __name__ == "__main__":
    main()
