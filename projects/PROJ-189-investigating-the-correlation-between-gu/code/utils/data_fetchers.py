"""
Deterministic data fetching utilities with checksum validation.

This module provides robust functions to fetch data from remote sources,
validate integrity via SHA-256 checksums, and cache results locally.
It raises DataFetchError on any validation failure.
"""
import hashlib
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, List
import requests
import logging
from datetime import datetime

# Configure logger for this module
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching and validation errors."""
    pass

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
        
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file for hashing: {e}")

def fetch_data_with_validation(
    url: str,
    output_path: Union[str, Path],
    expected_checksum: Optional[str] = None,
    chunk_size: int = 8192,
    timeout: int = 300
) -> Tuple[Path, str]:
    """
    Fetch data from a URL, validate checksum, and save to disk.
    
    This function downloads a file from the given URL, calculates its
    SHA-256 checksum, and compares it against the expected checksum if provided.
    If validation fails, it raises a DataFetchError.
    
    Args:
        url: The URL to fetch data from.
        output_path: Path where the downloaded file should be saved.
        expected_checksum: Optional expected SHA-256 checksum for validation.
        chunk_size: Size of chunks to read during download.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (Path to saved file, Calculated checksum)
        
    Raises:
        DataFetchError: If download fails, checksum mismatch occurs, or I/O errors.
        ValueError: If the URL is invalid or empty.
    """
    output_path = Path(output_path)
    
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
        
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL scheme: {url}")
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    temp_fd = None
    temp_path = None
    
    try:
        logger.info(f"Downloading from {url} to {output_path}...")
        
        # Use a temporary file to avoid partial downloads being used
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir) / output_path.name
        
        # Stream the download
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    
        # Calculate checksum
        calculated_checksum = calculate_sha256(temp_path)
        logger.info(f"Download complete. Calculated checksum: {calculated_checksum}")
        
        # Validate checksum if expected is provided
        if expected_checksum:
            if calculated_checksum.lower() != expected_checksum.lower():
                # Clean up temp file on failure
                if temp_path.exists():
                    temp_path.unlink()
                raise DataFetchError(
                    f"Checksum validation failed for {url}. "
                    f"Expected: {expected_checksum}, Got: {calculated_checksum}"
                )
        
        # Move temp file to final destination
        shutil.move(str(temp_path), str(output_path))
        logger.info(f"File saved successfully to {output_path}")
        
        return output_path, calculated_checksum
        
    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Failed to download data from {url}: {e}")
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Unexpected error during fetch/validation: {e}")
    finally:
        # Clean up temp directory if it exists
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up temp directory: {cleanup_err}")

def fetch_and_cache(
    url: str,
    cache_dir: Union[str, Path],
    expected_checksum: Optional[str] = None,
    force_refresh: bool = False
) -> Path:
    """
    Fetch data with caching and validation.
    
    Checks if a valid, cached copy exists. If so, returns it.
    If not, downloads, validates, caches, and returns the path.
    
    Args:
        url: URL to fetch data from.
        cache_dir: Directory to use for caching.
        expected_checksum: Expected SHA-256 checksum for validation.
        force_refresh: If True, re-download even if cached copy exists.
        
    Returns:
        Path to the cached file.
        
    Raises:
        DataFetchError: If validation fails or download errors occur.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Derive filename from URL (simple approach)
    filename = url.split('/')[-1] or "downloaded_file"
    cached_path = cache_dir / filename
    
    # Check if cached version exists and is valid
    if cached_path.exists() and not force_refresh:
        logger.info(f"Checking cached file: {cached_path}")
        try:
            cached_checksum = calculate_sha256(cached_path)
            if expected_checksum:
                if cached_checksum.lower() == expected_checksum.lower():
                    logger.info(f"Cached file validated successfully. Using cached copy.")
                    return cached_path
                else:
                    logger.warning(f"Cached file checksum mismatch. Re-fetching.")
                    cached_path.unlink()
            else:
                logger.info(f"Using cached file (no checksum provided for validation).")
                return cached_path
        except Exception as e:
            logger.warning(f"Error validating cache: {e}. Re-fetching.")
            if cached_path.exists():
                cached_path.unlink()
    
    # Fetch and validate
    logger.info("Fetching data...")
    return fetch_data_with_validation(
        url=url,
        output_path=cached_path,
        expected_checksum=expected_checksum
    )[0]

# Example usage and verification can be added here if needed
# This module is designed to be imported and used by other pipeline components