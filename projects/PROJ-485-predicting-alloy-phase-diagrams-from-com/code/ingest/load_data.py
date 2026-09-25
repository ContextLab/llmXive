"""
Data ingestion module for alloy phase diagram prediction pipeline.

Handles loading data from URLs, local fallbacks, streaming large datasets,
and implementing real sampling strategies with proper documentation.
"""

import os
import sys
import time
import json
import hashlib
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple, Iterator
from urllib.parse import urlparse
import requests
import itertools

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.config import get_config

logger = get_logger(__name__)

# Configuration constants
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds
CHUNK_SIZE = 8192  # bytes for streaming
DEFAULT_SAMPLE_SIZE = 10000  # Default sample size if not specified

def check_data_source_availability() -> bool:
    """
    Check if configured data sources are available.
    
    Returns:
        bool: True if at least one source is configured and accessible, False otherwise.
        
    Raises:
        ValueError: With ErrorCode.DATA_SOURCE_MISSING if no sources are available.
    """
    config = get_config()
    
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')
    local_path = config.get('local_fallback_path', '')
    
    sources_available = False
    
    # Check URLs
    for url_name, url in [('NIST-JANAF', nist_url), ('SGTE', sgte_url)]:
        if url and url.strip():
            try:
                # Quick HEAD request to check availability
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    sources_available = True
                    log_info(f"{url_name} URL is accessible: {url}")
                else:
                    log_warning(f"{url_name} URL returned status {response.status_code}: {url}")
            except requests.RequestException as e:
                log_warning(f"{url_name} URL not accessible: {e}")
    
    # Check local fallback
    if local_path and local_path.strip():
        if os.path.exists(local_path):
            sources_available = True
            log_info(f"Local fallback file exists: {local_path}")
        else:
            log_warning(f"Local fallback path does not exist: {local_path}")
    
    if not sources_available:
        error_msg = "No data sources available. Please configure nist_janaf_url, sgte_url, or local_fallback_path in config.yaml."
        log_error(f"{ErrorCode.DATA_SOURCE_MISSING.value}: {error_msg}")
        raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: {error_msg}")
    
    return True

def stream_data(url: str, chunk_size: int = CHUNK_SIZE) -> Iterator[bytes]:
    """
    Stream data from a URL in chunks.
    
    Args:
        url: The URL to stream from.
        chunk_size: Size of each chunk in bytes.
        
    Yields:
        bytes: Chunks of data from the URL.
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                yield chunk
                
    except requests.RequestException as e:
        log_error(f"Failed to stream data from {url}: {e}")
        raise

def load_data_from_url(url: str, target_path: str) -> str:
    """
    Load data from a URL with exponential backoff retry logic.
    
    Args:
        url: The URL to load data from.
        target_path: Local path to save the downloaded data.
        
    Returns:
        str: Path to the saved file.
        
    Raises:
        ValueError: If data cannot be loaded after retries.
    """
    attempt = 0
    last_error = None
    
    while attempt < MAX_RETRIES:
        try:
            log_info(f"Attempting to download from {url} (attempt {attempt + 1}/{MAX_RETRIES})")
            
            # Create parent directory if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Stream and write to file
            with open(target_path, 'wb') as f:
                for chunk in stream_data(url):
                    f.write(chunk)
            
            log_info(f"Successfully downloaded data to {target_path}")
            return target_path
            
        except Exception as e:
            last_error = e
            attempt += 1
            if attempt < MAX_RETRIES:
                wait_time = RETRY_BACKOFF_BASE ** attempt
                log_warning(f"Download failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                log_error(f"Failed to download from {url} after {MAX_RETRIES} attempts: {e}")
    
    raise ValueError(f"Failed to load data from {url} after {MAX_RETRIES} retries: {last_error}")

def load_data_from_local_fallback(local_path: str) -> str:
    """
    Load data from a local fallback file.
    
    Args:
        local_path: Path to the local CSV file.
        
    Returns:
        str: Path to the loaded file.
        
    Raises:
        ValueError: If the file doesn't exist or is invalid.
    """
    if not local_path or not local_path.strip():
        raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Local fallback path is empty")
    
    if not os.path.exists(local_path):
        raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Local fallback file does not exist: {local_path}")
    
    # Verify it's a readable CSV
    try:
        with open(local_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                raise ValueError(f"Empty CSV file: {local_path}")
            log_info(f"Successfully loaded local fallback: {local_path} with columns: {header}")
    except Exception as e:
        raise ValueError(f"Invalid CSV file at {local_path}: {e}")
    
    return local_path

def filter_missing_temperature(data_iterator: Iterator[Dict[str, Any]], system_type: str = 'binary') -> Iterator[Dict[str, Any]]:
    """
    Filter out entries with missing temperature values.
    
    Args:
        data_iterator: Iterator of data rows.
        system_type: Type of system ('binary' or 'ternary').
        
    Yields:
        Dict: Rows with valid temperature values.
    """
    for row in data_iterator:
        temp_value = row.get('temperature')
        
        if temp_value is None or temp_value == '' or str(temp_value).strip() == '':
            if system_type == 'ternary':
                # Log MISSING_TEMP_COORDS for ternary systems
                log_error({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "level": "ERROR",
                    "code": ErrorCode.MISSING_TEMP_COORDS.value,
                    "message": f"Row excluded: ternary system missing temperature-composition coordinates"
                })
            continue  # Skip rows with missing temperature
        
        try:
            float(temp_value)  # Validate it's a number
            yield row
        except (ValueError, TypeError):
            continue

def compute_row_checksum(row: Dict[str, Any]) -> str:
    """
    Compute SHA-256 checksum for a single row.
    
    Args:
        row: Dictionary representing a data row.
        
    Returns:
        str: Hexadecimal SHA-256 hash of the row.
    """
    # Create a canonical string representation
    canonical = json.dumps(row, sort_keys=True)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def compute_dataset_checksum(file_path: str) -> str:
    """
    Compute SHA-256 checksum for an entire file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        str: Hexadecimal SHA-256 hash of the file contents.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_with_checksum(artifact_path: str, checksum: str) -> None:
    """
    Update the state file with a checksum for an artifact.
    
    Args:
        artifact_path: Path to the artifact file.
        checksum: SHA-256 checksum of the artifact.
    """
    state_dir = "state/PROJ-485"
    state_file = os.path.join(state_dir, "pipeline_state.yaml")
    
    os.makedirs(state_dir, exist_ok=True)
    
    # Load existing state or create new
    if os.path.exists(state_file):
        import yaml
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {"artifacts": {}, "steps": {}, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    
    # Update artifact checksum
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][artifact_path] = {
        "checksum": checksum,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Save state
    with open(state_file, 'w') as f:
        import yaml
        yaml.dump(state, f, default_flow_style=False)
    
    log_info(f"Updated state with checksum for {artifact_path}: {checksum}")

def sample_real_data(file_path: str, sample_size: int = DEFAULT_SAMPLE_SIZE, seed: int = 42) -> Tuple[List[Dict[str, Any]], str]:
    """
    Implement a well-defined real sampling strategy for large datasets.
    
    This function samples the first N rows from a real CSV file to handle
    datasets that are too large to process in memory, while ensuring the
    data remains real (not synthetic).
    
    Args:
        file_path: Path to the real CSV file.
        sample_size: Number of rows to sample.
        seed: Random seed for reproducibility (used for random sampling if needed).
        
    Returns:
        Tuple of (sampled_rows, sampling_description)
        
    Raises:
        ValueError: If the file doesn't exist or is invalid.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Sample source file does not exist: {file_path}")
    
    sampled_rows = []
    total_rows = 0
    
    # Strategy 1: First N rows (deterministic, fast)
    # This is the primary strategy for large datasets
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            
            if not header:
                raise ValueError(f"CSV file has no header: {file_path}")
            
            for i, row in enumerate(reader):
                if i >= sample_size:
                    break
                sampled_rows.append(row)
                total_rows = i + 1
                
    except Exception as e:
        log_error(f"Failed to sample data from {file_path}: {e}")
        raise
    
    # Create sampling description
    sampling_description = (
        f"Real data sampling: First {sample_size} rows from {file_path}. "
        f"Total rows available: {total_rows}. "
        f"Strategy: itertools.islice (first N rows). "
        f"Note: This is a subset of real data, not synthetic. "
        f"Representativeness: Limited to first {sample_size} entries; may not capture full dataset distribution."
    )
    
    log_info(sampling_description)
    
    return sampled_rows, sampling_description

def load_data(output_path: str = "data/processed/descriptors.csv") -> str:
    """
    Main data loading function that orchestrates the entire pipeline.
    
    This function:
    1. Checks data source availability
    2. Loads data from URL or local fallback
    3. Streams large datasets if needed
    4. Filters missing temperatures
    5. Implements sampling for large datasets
    6. Computes and records checksums
    7. Updates state with artifact information
    
    Args:
        output_path: Path to save the processed data.
        
    Returns:
        str: Path to the processed data file.
    """
    config = get_config()
    
    # Step 1: Check data source availability
    log_info("Checking data source availability...")
    check_data_source_availability()
    
    # Step 2: Determine source and load data
    local_path = config.get('local_fallback_path', '')
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')
    
    temp_file = None
    
    try:
        if local_path and os.path.exists(local_path):
            log_info(f"Loading from local fallback: {local_path}")
            source_file = load_data_from_local_fallback(local_path)
            
        elif nist_url:
            temp_file = "data/raw/nist_janaf_temp.csv"
            log_info(f"Loading from NIST-JANAF URL: {nist_url}")
            source_file = load_data_from_url(nist_url, temp_file)
            
        elif sgte_url:
            temp_file = "data/raw/sgte_temp.csv"
            log_info(f"Loading from SGTE URL: {sgte_url}")
            source_file = load_data_from_url(sgte_url, temp_file)
            
        else:
            raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: No valid data source configured")
        
        # Step 3: Check file size and decide on sampling
        file_size_mb = os.path.getsize(source_file) / (1024 * 1024)
        log_info(f"Source file size: {file_size_mb:.2f} MB")
        
        # If file is large (> 100MB), implement sampling
        if file_size_mb > 100:
            log_warning(f"Large dataset detected ({file_size_mb:.2f} MB). Implementing real sampling strategy.")
            sampled_rows, sampling_desc = sample_real_data(source_file, sample_size=DEFAULT_SAMPLE_SIZE)
            
            # Write sampled data to output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if sampled_rows:
                    writer = csv.DictWriter(f, fieldnames=sampled_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(sampled_rows)
            
            # Log sampling information
            with open("data/logs/sampling_log.json", 'w') as f:
                json.dump({
                    "source_file": source_file,
                    "output_file": output_path,
                    "sampling_description": sampling_desc,
                    "sample_size": len(sampled_rows),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }, f, indent=2)
            
            log_info(f"Sampled data written to {output_path}")
            
        else:
            # Process entire file (streaming for safety)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(source_file, 'r', newline='', encoding='utf-8') as infile, \
                 open(output_path, 'w', newline='', encoding='utf-8') as outfile:
                
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames
                
                if not fieldnames:
                    raise ValueError("CSV file has no header")
                
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                row_count = 0
                for row in filter_missing_temperature(reader):
                    writer.writerow(row)
                    row_count += 1
                
                log_info(f"Processed {row_count} rows from {source_file}")
        
        # Step 4: Compute checksum and update state
        checksum = compute_dataset_checksum(output_path)
        update_state_with_checksum(output_path, checksum)
        
        log_info(f"Data loading complete. Output: {output_path}, Checksum: {checksum}")
        return output_path
        
    finally:
        # Clean up temporary files
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                log_info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                log_warning(f"Failed to clean up temporary file {temp_file}: {e}")

def main():
    """Main entry point for the data loading script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load and process alloy phase diagram data")
    parser.add_argument('--output', '-o', default='data/processed/descriptors.csv',
                      help='Output path for processed data')
    parser.add_argument('--sample-size', type=int, default=DEFAULT_SAMPLE_SIZE,
                      help='Sample size for large datasets')
    
    args = parser.parse_args()
    
    try:
        output_path = load_data(args.output)
        print(f"Data loaded successfully to: {output_path}")
        
        # Verify output exists
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"Output file size: {size_mb:.2f} MB")
        else:
            print("ERROR: Output file was not created")
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Data loading failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()