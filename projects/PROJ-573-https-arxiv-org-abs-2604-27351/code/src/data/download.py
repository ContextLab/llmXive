"""
Dataset download and verification utilities.

Implements robust dataset downloading with retry logic, checksum verification,
and integrity checks for the Heterogeneous Scientific Foundation Model Benchmark.
"""

import hashlib
import os
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Any, Dict, List

# Import from existing API surface
from src.utils.logging import get_logger

logger = get_logger(__name__)


def compute_dataset_checksum(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def verify_dataset_integrity(file_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify dataset integrity by computing checksum and comparing if expected provided.

    Args:
        file_path: Path to the dataset file
        expected_checksum: Optional expected checksum for validation

    Returns:
        True if file exists and (optionally) matches expected checksum
    """
    if not os.path.exists(file_path):
        logger.error(f"Dataset file does not exist: {file_path}")
        return False

    try:
        actual_checksum = compute_dataset_checksum(file_path)
        logger.info(f"Computed checksum for {file_path}: {actual_checksum[:16]}...")

        if expected_checksum:
            if actual_checksum == expected_checksum:
                logger.info("Checksum verification PASSED")
                return True
            else:
                logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
                return False
        else:
            logger.info("Checksum computed (no expected value to compare against)")
            return True
    except Exception as e:
        logger.error(f"Integrity verification failed: {e}")
        return False


def download_dataset(url: str, max_retries: int = 3, timeout: int = 300) -> Tuple[str, str]:
    """
    Download a dataset with retry logic and timeout enforcement.

    Supports both direct URL downloads and HuggingFace datasets.

    Args:
        url: Dataset identifier (URL or HuggingFace dataset name)
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout in seconds for download operations (default: 300)

    Returns:
        Tuple of (local_path, checksum)

    Raises:
        RuntimeError: If download fails after all retries
        TimeoutError: If download exceeds timeout
    """
    from pathlib import Path
    import tempfile

    # Determine if this is a HuggingFace dataset or direct URL
    is_hf_dataset = not url.startswith(('http://', 'https://')) and '/' in url

    download_path = None
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries} for: {url}")

            if is_hf_dataset:
                # Handle HuggingFace datasets
                logger.info(f"Loading HuggingFace dataset: {url}")
                try:
                    from datasets import load_dataset
                    import pandas as pd

                    # Load dataset
                    dataset = load_dataset(url, split='train')

                    # Create output directory
                    output_dir = Path("data/raw")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Sanitize dataset name for filename
                    safe_name = url.replace('/', '_').replace(':', '_')
                    output_file = output_dir / f"{safe_name}.csv"

                    # Convert to pandas and save
                    df = dataset.to_pandas()
                    df.to_csv(output_file, index=False)

                    download_path = str(output_file)
                    logger.info(f"Dataset saved to: {download_path}")

                except Exception as e:
                    logger.error(f"Failed to load HuggingFace dataset {url}: {e}")
                    raise RuntimeError(f"HuggingFace download failed: {e}")

            else:
                # Handle direct URL downloads
                import urllib.request

                # Create output directory
                output_dir = Path("data/raw")
                output_dir.mkdir(parents=True, exist_ok=True)

                # Extract filename from URL or generate one
                filename = url.split('/')[-1]
                if not filename or '.' not in filename:
                    filename = f"dataset_{int(time.time())}.zip"

                output_file = output_dir / filename
                download_path = str(output_file)

                logger.info(f"Downloading from {url} to {download_path}")

                # Download with timeout
                def download_with_timeout():
                    urllib.request.urlretrieve(url, download_path)

                # Simple timeout wrapper using threading
                import threading
                import sys

                result = [None]
                exception = [None]

                def target():
                    try:
                        urllib.request.urlretrieve(url, download_path)
                        result[0] = True
                    except Exception as e:
                        exception[0] = e

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout=timeout)

                if thread.is_alive():
                    raise TimeoutError(f"Download timed out after {timeout} seconds")

                if exception[0]:
                    raise exception[0]

                if not result[0]:
                    raise RuntimeError("Download failed without explicit error")

            # Verify download integrity
            if download_path and os.path.exists(download_path):
                checksum = compute_dataset_checksum(download_path)
                logger.info(f"Download complete. Checksum: {checksum[:16]}...")
                return (download_path, checksum)

            else:
                raise FileNotFoundError(f"Downloaded file not found: {download_path}")

        except TimeoutError as e:
            last_error = e
            logger.warning(f"Timeout on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise RuntimeError(f"Download failed after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    # Should not reach here, but just in case
    raise RuntimeError(f"Download failed after {max_retries} attempts. Last error: {last_error}")


def main():
    """
    Main entry point for dataset download testing and verification.
    Demonstrates download functionality with sample datasets.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting dataset download verification...")

    # Test cases for different dataset types
    test_datasets = [
        # HuggingFace datasets
        ("ucihar", "UCI HAR Dataset (Time Series)"),
        ("DROP", "DROP Dataset (Text QA)"),
    ]

    results = []

    for dataset_id, description in test_datasets:
        logger.info(f"\n--- Testing: {description} ({dataset_id}) ---")
        try:
            # Use a smaller subset or specific split if available
            # For UCI HAR, we use the standard dataset
            if dataset_id == "ucihar":
                # UCI HAR is available via datasets library
                url = "ucihar"
            elif dataset_id == "DROP":
                url = "drop"
            else:
                url = dataset_id

            path, checksum = download_dataset(url, max_retries=2, timeout=120)
            results.append({
                "dataset": description,
                "status": "SUCCESS",
                "path": path,
                "checksum": checksum,
                "size_mb": os.path.getsize(path) / (1024 * 1024)
            })
            logger.info(f"✓ Download successful: {path}")

        except Exception as e:
            logger.error(f"✗ Download failed: {e}")
            results.append({
                "dataset": description,
                "status": "FAILED",
                "error": str(e)
            })

    # Summary
    logger.info("\n" + "="*50)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("="*50)
    for result in results:
        status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
        logger.info(f"{status_icon} {result['dataset']}: {result['status']}")
        if result["status"] == "SUCCESS":
            logger.info(f"   Path: {result['path']}")
            logger.info(f"   Size: {result['size_mb']:.2f} MB")
            logger.info(f"   Checksum: {result['checksum'][:32]}...")

    return results


if __name__ == "__main__":
    main()
