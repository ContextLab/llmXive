import os
import sys
import time
import logging
import hashlib
import urllib.request
from typing import Optional, Callable, Any

# Ensure parent directory is in path if running as script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import get_config

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculates the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for checksum calculation: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {file_path}: {e}")

def download_with_retry(
    url: str, 
    output_path: str, 
    max_retries: int = 5, 
    base_delay: float = 2.0,
    chunk_size: int = 8192
) -> bool:
    """
    Downloads a file from a URL with exponential backoff retry logic.
    
    Args:
        url: The URL to download from.
        output_path: Local path to save the file.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        chunk_size: Size of chunks to read during download.
        
    Returns:
        True if download successful, False otherwise.
        
    Raises:
        RuntimeError: If download fails after all retries.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Downloading {url} to {output_path} (Attempt {attempt + 1}/{max_retries})")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            urllib.request.urlretrieve(url, output_path)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully downloaded {url}")
                return True
            else:
                raise RuntimeError("Downloaded file is empty or missing.")
                
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                logger.error(f"Failed to download {url} after {max_retries} attempts: {e}")
                raise RuntimeError(f"Download failed after {max_retries} retries: {e}") from e
            
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Download failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    
    return False

def download_qm9_subset(output_path: str) -> bool:
    """
    Placeholder for QM9 subset download logic.
    Implemented in specific task scripts using datasets library.
    """
    raise NotImplementedError("Use specific download scripts for QM9.")

def download_kinetic_dataset(output_path: str) -> bool:
    """
    Placeholder for kinetic dataset download logic.
    Implemented in specific download scripts (e.g., code/01_download_kinetic_data.py).
    """
    raise NotImplementedError("Use code/01_download_kinetic_data.py for kinetic dataset.")

def download_reference_substructures(output_path: str) -> bool:
    """
    Placeholder for reference substructures download logic.
    Implemented in specific download scripts.
    """
    raise NotImplementedError("Use specific download scripts for reference substructures.")

def main():
    """Main entry point for utils.loaders (for testing)."""
    print("Loaders module loaded successfully.")

if __name__ == "__main__":
    main()