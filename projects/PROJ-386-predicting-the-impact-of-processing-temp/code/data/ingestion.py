"""
code/data/ingestion.py
Handles data ingestion, validation, filtering, and storage logic.
Includes streaming loading, URL verification, schema checks, and checksum generation.
"""

import os
import sys
import json
import hashlib
import logging
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator

# Conditional imports for optional dependencies
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from datasets import load_dataset, Dataset
except ImportError:
    load_dataset = None
    Dataset = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = ['rolling temperature', 'grain size']
COMPOSITION_COLUMNS = ['Mg', 'Si', 'Cu', 'Zn', 'Mn', 'Cr', 'Fe', 'Ti'] # Common alloying elements

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
        
    Returns:
        Hexadecimal string of the hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksum(file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Generate a SHA-256 checksum for a file and optionally save it.
    
    This function implements the storage logic for T016.
    
    Args:
        file_path: Path to the file to checksum.
        output_path: Optional path to save the checksum JSON. If None, only returns the dict.
        
    Returns:
        Dictionary containing 'path', 'hash', 'size', 'timestamp'.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    file_size = file_path.stat().st_size
    file_hash = calculate_file_hash(file_path)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(file_path.stat().st_mtime))
    
    result = {
        "path": str(file_path.absolute()),
        "hash": file_hash,
        "size_bytes": file_size,
        "timestamp": timestamp
    }
    
    if output_path:
        output_path = Path(output_path)
        ensure_directory(output_path.parent)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Checksum saved to {output_path}")
    
    return result

def load_streaming_dataset(url: str, chunk_size: int = 10000) -> Union['pd.DataFrame', 'Dataset']:
    """
    Load a dataset from a URL using streaming to handle large files.
    
    Args:
        url: URL to the dataset (CSV or supported format).
        chunk_size: Number of rows per chunk for pandas.
        
    Returns:
        A pandas DataFrame (if small) or a streaming Dataset object.
        
    Raises:
        RuntimeError: If the URL is invalid or data cannot be fetched.
    """
    if pd is None:
        raise RuntimeError("pandas is required for streaming dataset loading.")
        
    logger.info(f"Attempting to load streaming dataset from {url}")
    
    # Check if it's a local file or remote URL
    if url.startswith('http'):
        try:
            # Attempt to load with datasets library if available for better streaming
            if load_dataset:
                try:
                    # Try to infer format, default to csv
                    ds = load_dataset('csv', data_files=url, streaming=True)
                    # Return the split dataset (usually 'train')
                    return ds['train']
                except Exception as e:
                    logger.warning(f"datasets library failed: {e}. Falling back to pandas chunks.")
            
            # Fallback to pandas read_csv with chunksize
            # Note: pandas read_csv with chunksize returns a TextFileReader, not a DataFrame
            # We return the reader object which is iterable
            reader = pd.read_csv(url, chunksize=chunk_size)
            return reader
            
        except Exception as e:
            raise RuntimeError(f"Failed to load dataset from URL: {e}")
    else:
        # Local file
        if not os.path.exists(url):
            raise FileNotFoundError(f"Local file not found: {url}")
        
        # Check size to decide strategy
        if os.path.getsize(url) > 100 * 1024 * 1024: # > 100MB
            logger.info("Large file detected, using streaming chunks.")
            return pd.read_csv(url, chunksize=chunk_size)
        else:
            logger.info("Small file detected, loading into memory.")
            return pd.read_csv(url)

def verify_source_urls(urls: List[str]) -> List[str]:
    """
    Verify accessibility of source URLs using HEAD requests.
    
    Args:
        urls: List of URLs to verify.
        
    Returns:
        List of valid, accessible URLs.
        
    Raises:
        ValueError: If no valid URLs are found.
    """
    if not urls:
        raise ValueError("No URLs provided to verify.")
        
    valid_urls = []
    
    # Try to import requests, fall back to urllib if not available
    try:
        import requests
        use_requests = True
    except ImportError:
        import urllib.request
        import urllib.error
        use_requests = False
    
    for url in urls:
        try:
            logger.info(f"Verifying URL: {url}")
            if use_requests:
                # Use requests for better timeout handling
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    valid_urls.append(url)
                    logger.info(f"URL accessible: {url}")
                else:
                    logger.warning(f"URL returned status {response.status_code}: {url}")
            else:
                # Fallback to urllib
                req = urllib.request.Request(url, method='HEAD')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        valid_urls.append(url)
                        logger.info(f"URL accessible: {url}")
                    else:
                        logger.warning(f"URL returned status {response.status}: {url}")
                        
        except Exception as e:
            logger.warning(f"Failed to verify URL {url}: {e}")
    
    if not valid_urls:
        raise ValueError("Source Unreachable: No valid URLs found.")
        
    return valid_urls

def check_schema_preconditions(url: str) -> bool:
    """
    Fetch a small sample of the dataset and verify presence of critical columns.
    
    Args:
        url: URL to the dataset.
        
    Returns:
        True if schema matches, False otherwise.
    """
    logger.info(f"Checking schema preconditions for {url}")
    
    try:
        # Load a small sample to check schema
        # Using pandas read_csv with nrows=100 for quick check
        if url.startswith('http'):
            df_sample = pd.read_csv(url, nrows=100)
        else:
            df_sample = pd.read_csv(url, nrows=100)
            
        columns = [col.lower().strip() for col in df_sample.columns]
        
        # Normalize required columns for comparison
        required_lower = [col.lower().strip() for col in REQUIRED_COLUMNS]
        
        # Check if all required columns are present
        missing = [req for req in required_lower if req not in columns]
        
        if missing:
            logger.warning(f"Missing required columns in {url}: {missing}")
            return False
            
        logger.info("Schema precondition check passed.")
        return True
        
    except Exception as e:
        logger.error(f"Error checking schema for {url}: {e}")
        return False

def accumulate_streaming_stats(chunk_iterable: Iterator) -> Dict[str, Any]:
    """
    Iterate over chunks from a streaming loader and update running statistics.
    
    Args:
        chunk_iterable: An iterable of pandas DataFrames (chunks).
        
    Returns:
        Dictionary of accumulated statistics (mean, count, null counts).
    """
    stats = {
        'count': 0,
        'sum': {},
        'null_counts': {}
    }
    
    # Determine critical columns to track
    # We'll track all numeric columns found in the first chunk
    critical_cols = None
    
    for i, chunk in enumerate(chunk_iterable):
        if i == 0:
            # Initialize stats for numeric columns
            numeric_cols = chunk.select_dtypes(include=['number']).columns.tolist()
            for col in numeric_cols:
                stats['sum'][col] = 0.0
                stats['null_counts'][col] = 0
            critical_cols = numeric_cols
        
        # Update counts
        stats['count'] += len(chunk)
        
        # Update sums and null counts
        for col in critical_cols:
            if col in chunk.columns:
                # Sum
                stats['sum'][col] += chunk[col].sum()
                # Null counts
                stats['null_counts'][col] += chunk[col].isna().sum()
        if i % 100 == 0:
            logger.info(f"Processed {i} chunks, total rows: {stats['count']}")
            
    # Calculate means
    final_stats = {
        'total_rows': stats['count'],
        'means': {},
        'null_counts': stats['null_counts']
    }
    
    for col in critical_cols:
        if stats['count'] > 0:
            final_stats['means'][col] = stats['sum'][col] / stats['count']
        else:
            final_stats['means'][col] = 0.0
            
    return final_stats

def save_streaming_stats(stats: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """Save streaming statistics to a JSON file."""
    output_path = Path(output_path)
    ensure_directory(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Streaming stats saved to {output_path}")

def filter_data(df: 'pd.DataFrame') -> 'pd.DataFrame':
    """
    Filter data to exclude rows with missing critical variables.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Filtering data. Original size: {len(df)}")
    
    # Normalize column names for matching
    df.columns = [col.lower().strip() for col in df.columns]
    
    # Identify critical columns present in the dataframe
    available_critical = [col for col in REQUIRED_COLUMNS if col in df.columns]
    
    if not available_critical:
        logger.warning("No critical columns found in dataframe.")
        return df # Return as is, or raise error depending on strictness
    
    # Drop rows with any NaN in critical columns
    initial_count = len(df)
    df_filtered = df.dropna(subset=available_critical)
    final_count = len(df_filtered)
    
    logger.info(f"Filtered data size: {final_count} (removed {initial_count - final_count} rows)")
    
    return df_filtered

def check_purity(df: 'pd.DataFrame') -> None:
    """
    Check if the dataset is mostly pure aluminum.
    
    Args:
        df: Input DataFrame.
        
    Raises:
        ValueError: If >90% of data is pure aluminum.
    """
    # Identify composition columns present
    present_comps = [col for col in COMPOSITION_COLUMNS if col in df.columns]
    
    if not present_comps:
        logger.warning("No composition columns found to check purity.")
        return
    
    # Check for rows where all composition elements are zero or missing
    # We assume missing implies 0 for purity check in this context
    purity_mask = df[present_comps].fillna(0).eq(0).all(axis=1)
    pure_count = purity_mask.sum()
    total_count = len(df)
    
    if total_count > 0:
        pure_ratio = pure_count / total_count
        logger.info(f"Pure aluminum ratio: {pure_ratio:.2%}")
        
        if pure_ratio > 0.90:
            raise ValueError(f"Dataset insufficient for interaction analysis: >90% pure aluminum ({pure_ratio:.2%})")
    else:
        logger.warning("No data to check purity.")

def run_pipeline(urls: List[str], output_path: Union[str, Path], stats_path: Optional[Union[str, Path]] = None) -> 'pd.DataFrame':
    """
    Run the full ingestion pipeline: verify, load, filter, checksum.
    
    Args:
        urls: List of source URLs.
        output_path: Path to save the ingested data.
        stats_path: Optional path to save streaming stats.
        
    Returns:
        The final filtered DataFrame.
    """
    logger.info("Starting Ingestion Pipeline")
    
    # 1. Verify URLs
    valid_urls = verify_source_urls(urls)
    logger.info(f"Valid URLs: {valid_urls}")
    
    # 2. Load Data (Streaming if large)
    # For simplicity in this pipeline, we assume the first valid URL is the source.
    # In a real scenario, we might concatenate multiple sources.
    source_url = valid_urls[0]
    
    # Check schema first
    if not check_schema_preconditions(source_url):
        raise ValueError(f"Schema check failed for {source_url}. Missing critical columns.")
    
    # Load data
    data_loader = load_streaming_dataset(source_url)
    
    if isinstance(data_loader, pd.DataFrame):
        df = data_loader
    elif hasattr(data_loader, 'to_pandas'):
        # HuggingFace Dataset
        df = data_loader.to_pandas()
    else:
        # Iterator (pandas chunkreader)
        logger.info("Aggregating chunks from streaming loader...")
        chunks = []
        for chunk in data_loader:
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    
    logger.info(f"Loaded {len(df)} rows.")
    
    # 3. Filter Data
    df_filtered = filter_data(df)
    
    # 4. Purity Check
    try:
        check_purity(df_filtered)
    except ValueError as e:
        logger.error(str(e))
        raise
    
    # 5. Ensure Output Directory
    output_path = Path(output_path)
    ensure_directory(output_path.parent)
    
    # 6. Save Data
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")
    
    # 7. Generate Checksum (T016 Implementation)
    checksum_info = generate_checksum(output_path)
    logger.info(f"Checksum generated: {checksum_info['hash'][:16]}...")
    
    # 8. Calculate and Save Stats (if requested)
    if stats_path:
        # Re-load in chunks for stats if we didn't already
        # For simplicity, if df is in memory, we can just calculate stats directly
        # But to be consistent with streaming stats logic:
        if stats_path:
             # Simple stats calculation on the final df
             stats = {
                 'total_rows': len(df_filtered),
                 'means': df_filtered.select_dtypes(include=['number']).mean().to_dict(),
                 'null_counts': df_filtered.isna().sum().to_dict()
             }
             save_streaming_stats(stats, stats_path)
    
    return df_filtered

def main():
    parser = argparse.ArgumentParser(description="Ingestion Pipeline")
    parser.add_argument('--urls', nargs='+', required=True, help='Source URLs')
    parser.add_argument('--output', required=True, help='Output CSV path')
    parser.add_argument('--stats', help='Output stats JSON path')
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.urls, args.output, args.stats)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
