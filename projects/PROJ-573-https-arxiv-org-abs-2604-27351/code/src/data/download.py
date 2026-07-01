"""
Dataset download and verification utilities.

Implements robust dataset downloading with retry logic, checksum verification,
and support for HuggingFace datasets and direct URL downloads.
"""

import hashlib
import os
import time
import logging
import shutil
from pathlib import Path
from typing import Tuple, Optional, Union, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import from project utils
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Base data directory
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def ensure_data_dirs() -> None:
    """Ensure all required data directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directories ensured: {RAW_DIR}, {PROCESSED_DIR}")


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the file checksum
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def compute_directory_checksum(dir_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute a combined checksum for all files in a directory.

    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of the combined checksum
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    hash_func = hashlib.new(algorithm)
    # Sort files for deterministic ordering
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            # Include relative path in hash
            rel_path = str(file_path.relative_to(dir_path))
            hash_func.update(rel_path.encode("utf-8"))
            # Include file content
            file_checksum = compute_file_checksum(file_path, algorithm)
            hash_func.update(file_checksum.encode("utf-8"))

    return hash_func.hexdigest()


def compute_dataset_checksum(dataset_name: str, base_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Compute checksum for a downloaded dataset.

    Args:
        dataset_name: Name of the dataset
        base_dir: Base directory for datasets (default: data/raw)

    Returns:
        Hex digest of the dataset checksum
    """
    base_dir = Path(base_dir) if base_dir else RAW_DIR
    dataset_dir = base_dir / dataset_name

    if dataset_dir.exists():
        return compute_directory_checksum(dataset_dir)
    else:
        # Check for single file
        file_path = base_dir / f"{dataset_name}.zip"
        if file_path.exists():
            return compute_file_checksum(file_path)

        raise FileNotFoundError(f"Dataset not found: {dataset_name}")


def verify_dataset_integrity(
    dataset_name: str,
    expected_checksum: Optional[str] = None,
    base_dir: Optional[Union[str, Path]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Verify the integrity of a downloaded dataset.

    Args:
        dataset_name: Name of the dataset
        expected_checksum: Expected checksum (optional)
        base_dir: Base directory for datasets

    Returns:
        Tuple of (is_valid, actual_checksum)
    """
    try:
        actual_checksum = compute_dataset_checksum(dataset_name, base_dir)
        if expected_checksum:
            is_valid = actual_checksum == expected_checksum
            if not is_valid:
                logger.warning(
                    f"Checksum mismatch for {dataset_name}: "
                    f"expected={expected_checksum}, actual={actual_checksum}"
                )
            return is_valid, actual_checksum
        else:
            logger.info(f"Dataset {dataset_name} checksum: {actual_checksum}")
            return True, actual_checksum
    except FileNotFoundError as e:
        logger.error(f"Cannot verify dataset integrity: {e}")
        return False, None


def _create_session_with_retries(max_retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def download_dataset(
    url: str,
    output_path: Optional[Union[str, Path]] = None,
    max_retries: int = 3,
    timeout: int = 300
) -> Tuple[Path, str]:
    """
    Download a dataset from a URL with retry logic.

    Args:
        url: URL to download from
        output_path: Path to save the file (default: data/raw/{filename})
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for the download

    Returns:
        Tuple of (output_path, checksum)

    Raises:
        RuntimeError: If download fails after all retries
        ValueError: If URL is invalid or empty
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    ensure_data_dirs()

    # Determine output path
    if output_path is None:
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = "dataset.zip"
        output_path = RAW_DIR / filename
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading {url} to {output_path}")

    session = _create_session_with_retries(max_retries)

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries}")
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            # Get file size from headers if available
            total_size = int(response.headers.get("content-length", 0))

            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (8192 * 100) < 8192:  # Log every ~1MB
                                logger.debug(f"Download progress: {progress:.1f}%")

            # Verify download completed
            if total_size > 0 and output_path.stat().st_size != total_size:
                logger.warning(
                    f"Download size mismatch: expected {total_size}, got {output_path.stat().st_size}"
                )

            checksum = compute_file_checksum(output_path)
            logger.info(f"Download complete: {output_path}, checksum: {checksum}")
            return output_path, checksum

        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** (attempt - 1))
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed for {url}")

    raise RuntimeError(f"Failed to download {url} after {max_retries} attempts: {last_exception}")


def download_huggingface_dataset(
    dataset_name: str,
    output_dir: Optional[Union[str, Path]] = None,
    max_retries: int = 3
) -> Tuple[Path, str]:
    """
    Download a dataset from HuggingFace datasets library.

    Args:
        dataset_name: Name of the dataset on HuggingFace (e.g., 'UCI_HAR')
        output_dir: Directory to save the dataset (default: data/raw/{dataset_name})
        max_retries: Maximum retry attempts for loading

    Returns:
        Tuple of (output_path, checksum)

    Raises:
        ImportError: If datasets library is not installed
        RuntimeError: If dataset cannot be loaded after retries
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' library is required. Install with: pip install datasets"
        )

    ensure_data_dirs()

    if output_dir is None:
        output_dir = RAW_DIR / dataset_name
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading HuggingFace dataset: {dataset_name}")

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Load attempt {attempt}/{max_retries}")
            dataset = load_dataset(dataset_name, trust_remote_code=True)
            
            # Save dataset to disk
            save_path = output_dir / "dataset.arrow"
            dataset.save_to_disk(str(output_dir))
            
            checksum = compute_directory_checksum(output_dir)
            logger.info(
                f"Dataset {dataset_name} saved to {output_dir}, "
                f"checksum: {checksum}"
            )
            return output_dir, checksum

        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))  # Exponential backoff
            else:
                logger.error(f"All {max_retries} attempts failed for {dataset_name}")

    raise RuntimeError(f"Failed to load dataset {dataset_name} after {max_retries} attempts: {last_exception}")


def main() -> None:
    """Main entry point for dataset download and verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Download and verify datasets")
    parser.add_argument(
        "--url",
        type=str,
        help="URL to download from"
    )
    parser.add_argument(
        "--hf-dataset",
        type=str,
        help="HuggingFace dataset name"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path (default: data/raw/{filename})"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify dataset integrity after download"
    )
    parser.add_argument(
        "--expected-checksum",
        type=str,
        default=None,
        help="Expected checksum for verification"
    )

    args = parser.parse_args()

    if not args.url and not args.hf_dataset:
        parser.error("Either --url or --hf-dataset must be specified")

    try:
        if args.hf_dataset:
          path, checksum = download_huggingface_dataset(
              args.hf_dataset,
              output_dir=args.output,
              max_retries=3
          )
        else:
            path, checksum = download_dataset(
                args.url,
                output_path=args.output,
                max_retries=3
            )

        print(f"Downloaded: {path}")
        print(f"Checksum: {checksum}")

        if args.verify:
            is_valid, actual = verify_dataset_integrity(
                str(path),
                args.expected_checksum
            )
            print(f"Verification: {'PASSED' if is_valid else 'FAILED'}")
            if not is_valid:
                print(f"Expected: {args.expected_checksum}")
                print(f"Actual: {actual}")

    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise


if __name__ == "__main__":
    main()
