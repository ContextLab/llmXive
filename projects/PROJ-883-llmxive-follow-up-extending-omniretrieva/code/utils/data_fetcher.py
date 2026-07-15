"""
Data Fetcher Module for llmXive.

Handles real dataset downloads from URLs defined in config.py.
Implements checksum verification and partial download handling
to ensure data integrity (Constitution Principle III).
"""
import os
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests
from requests.exceptions import RequestException, Timeout

# Import config for URLs and constants
# We assume config.py is in the same parent directory structure relative to utils
try:
    from ..config import DATASET_URLS, DATA_DIR, EXIT_CODE_THROTTLING_FAILURE
except ImportError:
    # Fallback for direct execution or different import context
    from config import DATASET_URLS, DATA_DIR, EXIT_CODE_THROTTLING_FAILURE


class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


def calculate_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest string.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def fetch_dataset(
    dataset_name: str,
    force_download: bool = False,
    chunk_size: int = 8192
) -> Tuple[bool, str]:
    """
    Fetch a dataset from a remote URL, verifying integrity via checksums.
    
    This function handles:
    - Downloading from the URL defined in config.DATASET_URLS
    - Resuming partial downloads if possible (via Range header if supported)
    - Verifying SHA256 checksums if provided in config
    - Saving to the local DATA_DIR structure
    
    Args:
        dataset_name: Key name in DATASET_URLS dict (e.g., 'ms_marco_subset').
        force_download: If True, re-download even if file exists.
        chunk_size: Size of chunks for streaming download.
        
    Returns:
        Tuple of (success: bool, message: str).
        
    Raises:
        DataFetchError: If download fails, checksum mismatches, or URL is missing.
    """
    if dataset_name not in DATASET_URLS:
        raise DataFetchError(f"Dataset '{dataset_name}' not found in DATASET_URLS.")
    
    config = DATASET_URLS[dataset_name]
    url = config.get('url')
    expected_checksum = config.get('checksum')
    filename = config.get('filename', dataset_name)
    
    if not url:
        raise DataFetchError(f"URL missing for dataset '{dataset_name}'.")
    
    # Ensure target directory exists
    target_dir = Path(DATA_DIR) / 'raw'
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    
    # Check if file exists and skip if not forced
    if target_path.exists() and not force_download:
        # Verify existing file checksum if available
        if expected_checksum:
            try:
                actual_checksum = calculate_checksum(str(target_path))
                if actual_checksum.lower() != expected_checksum.lower():
                    raise DataFetchError(
                        f"Checksum mismatch for existing '{filename}'. "
                        f"Expected: {expected_checksum}, Got: {actual_checksum}. "
                        f"Use force_download=True to re-fetch."
                    )
                return True, f"Dataset '{filename}' already exists and verified."
            except FileNotFoundError:
                pass # Should not happen if exists() is True
        else:
            return True, f"Dataset '{filename}' already exists (no checksum to verify)."
    
    # Temporary file for atomic write
    temp_fd, temp_path = tempfile.mkstemp(dir=target_dir, suffix='.tmp')
    temp_file = os.fdopen(temp_fd, 'wb')
    
    try:
        headers = {}
        start_byte = 0
        
        # Attempt to resume if file exists partially (simple heuristic)
        if target_path.exists():
            start_byte = target_path.stat().st_size
            headers['Range'] = f'bytes={start_byte}-'
        
        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=60  # 60s timeout per task
        )
        
        # Handle Range request responses
        if response.status_code == 206:  # Partial Content
            print(f"Resuming download for '{filename}' from byte {start_byte}...")
        elif response.status_code == 200:
            if start_byte > 0:
                # Server ignored Range header, start fresh
                print(f"Download started fresh for '{filename}' (server ignored resume).")
                start_byte = 0
        else:
            raise DataFetchError(f"Failed to download '{filename}': HTTP {response.status_code}")
        
        # Write to temp file
        # If resuming, we need to append to the existing file content in the temp
        # But simpler: just write to temp, then rename/move.
        # Actually, if resuming, we should write to the temp file starting at offset?
        # To keep it simple and robust: if resuming, we open temp file in 'ab' mode if it exists?
        # No, temp file is new. We just download the rest.
        
        # If we are resuming, we need to copy existing data to temp first?
        # Or just download the rest and append.
        
        download_mode = 'wb' if start_byte == 0 else 'ab'
        
        # If resuming, we need to prepend existing data?
        # Actually, let's just download the whole thing again if resume is tricky or not supported.
        # But the spec asks for partial download handling.
        # Let's implement a simple resume: if Range was sent and got 206, we append.
        # If we are resuming, we must have the existing file content.
        # We will write to temp, then if resuming, we copy existing file to temp first?
        # No, that's inefficient.
        
        # Strategy: 
        # 1. If resuming, open temp file in 'ab' mode? No, temp file is empty.
        # 2. We need to copy existing target file to temp, then append.
        if start_byte > 0 and response.status_code == 206:
            with open(target_path, 'rb') as f_in:
                shutil.copyfileobj(f_in, temp_file)
            temp_file.flush()
            # Now append the new chunks
            download_mode = 'ab' 
        
        with open(temp_path, download_mode) as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)
        
        temp_file.close() # Close the file handle we opened via os.fdopen
        
        # Verify checksum if available
        if expected_checksum:
            actual_checksum = calculate_checksum(temp_path)
            if actual_checksum.lower() != expected_checksum.lower():
                os.remove(temp_path)
                raise DataFetchError(
                    f"Checksum mismatch for '{filename}'. "
                    f"Expected: {expected_checksum}, Got: {actual_checksum}."
                )
        
        # Atomic move
        shutil.move(temp_path, target_path)
        print(f"Successfully fetched and verified: {filename}")
        return True, f"Dataset '{filename}' downloaded and verified."
        
    except Timeout:
        os.remove(temp_path)
        raise DataFetchError(f"Download timeout for '{filename}'.")
    except RequestException as e:
        os.remove(temp_path)
        raise DataFetchError(f"Network error downloading '{filename}': {str(e)}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise DataFetchError(f"Unexpected error during download: {str(e)}")


def verify_all_datasets() -> Dict[str, bool]:
    """
    Verify integrity of all datasets defined in config.
    
    Returns:
        Dict mapping dataset name to verification status (True/False).
    """
    results = {}
    for name in DATASET_URLS:
        try:
            # Just check existence and checksum if defined
            config = DATASET_URLS[name]
            filename = config.get('filename', name)
            expected_checksum = config.get('checksum')
            target_path = Path(DATA_DIR) / 'raw' / filename
            
            if not target_path.exists():
                results[name] = False
                continue
            
            if expected_checksum:
                actual = calculate_checksum(str(target_path))
                results[name] = actual.lower() == expected_checksum.lower()
            else:
                results[name] = True
        except Exception:
            results[name] = False
    return results


def main():
    """
    CLI entry point to fetch datasets.
    
    Usage:
        python -m code.utils.data_fetcher --dataset <name> [--force]
        python -m code.utils.data_fetcher --verify
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch and verify datasets for llmXive.')
    parser.add_argument('--dataset', type=str, help='Dataset name to fetch (from config).')
    parser.add_argument('--force', action='store_true', help='Force re-download.')
    parser.add_argument('--verify', action='store_true', help='Verify all existing datasets.')
    
    args = parser.parse_args()
    
    if args.verify:
        results = verify_all_datasets()
        all_ok = all(results.values())
        for name, status in results.items():
            print(f"{name}: {'OK' if status else 'FAILED/MISSING'}")
        if not all_ok:
            print("Some datasets are missing or corrupted.")
            return EXIT_CODE_THROTTLING_FAILURE
        return 0
    
    if args.dataset:
        try:
            success, msg = fetch_dataset(args.dataset, force_download=args.force)
            print(msg)
            return 0 if success else EXIT_CODE_THROTTLING_FAILURE
        except DataFetchError as e:
            print(f"Error: {e}")
            return EXIT_CODE_THROTTLING_FAILURE
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit(main())