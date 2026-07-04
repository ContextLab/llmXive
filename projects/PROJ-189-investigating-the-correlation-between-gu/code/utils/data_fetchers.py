"""
Deterministic data fetching utilities with checksum validation.

This module provides functions to fetch data from remote sources in a
reproducible manner, validating integrity via checksums (SHA-256).
It ensures that downloaded files match expected hashes to prevent
silent data corruption or version drift.
"""

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import requests
from tqdm import tqdm


class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def fetch_data_with_validation(
    url: str,
    output_path: Union[str, Path],
    expected_checksum: Optional[str] = None,
    chunk_size: int = 8192,
    timeout: int = 60,
    retries: int = 3,
) -> Tuple[bool, str]:
    """
    Fetch data from a URL with optional checksum validation.

    This function downloads a file from the specified URL, saves it to
    the output path, and validates its integrity if an expected checksum
    is provided. It includes retry logic for transient network failures.

    Args:
        url: The URL to fetch data from.
        output_path: Local path where the file should be saved.
        expected_checksum: Optional SHA-256 hex string to validate against.
        chunk_size: Size of chunks to read during download.
        timeout: Request timeout in seconds.
        retries: Number of retry attempts on failure.

    Returns:
        Tuple of (success: bool, message: str).
        If success is False, message contains the error description.
        If success is True, message contains the file path or validation status.

    Raises:
        DataFetchError: If download fails after retries or checksum mismatch.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            # Use a temporary file first to avoid partial writes
            with tempfile.NamedTemporaryFile(
                dir=output_path.parent, delete=False
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)

                response = requests.get(url, stream=True, timeout=timeout)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                desc = f"Downloading {output_path.name} (Attempt {attempt}/{retries})"

                with tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    desc=desc,
                    disable=total_size == 0,
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            tmp_file.write(chunk)
                            pbar.update(len(chunk))

                # Move temp file to final destination
                tmp_path.rename(output_path)

            # Validate checksum if provided
            if expected_checksum:
                actual_checksum = calculate_sha256(output_path)
                if actual_checksum.lower() != expected_checksum.lower():
                    os.remove(output_path)
                    return (
                        False,
                        f"Checksum mismatch for {output_path.name}. "
                        f"Expected: {expected_checksum}, Got: {actual_checksum}",
                    )

            return True, f"Successfully fetched and validated {output_path.name}"

        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < retries:
                continue
            return False, f"Download failed after {retries} attempts: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error during fetch: {str(e)}"

    return False, f"Download failed after {retries} attempts: {str(last_error)}"


def fetch_and_cache(
    url: str,
    cache_dir: Union[str, Path],
    filename: Optional[str] = None,
    expected_checksum: Optional[str] = None,
    force_refresh: bool = False,
) -> Tuple[bool, Path, str]:
    """
    Fetch data and cache it locally, skipping if already present and valid.

    Args:
        url: The URL to fetch data from.
        cache_dir: Directory to cache the file in.
        filename: Optional filename to use. If None, derived from URL.
        expected_checksum: Optional SHA-256 hex string for validation.
        force_refresh: If True, re-download even if file exists.

    Returns:
        Tuple of (success: bool, file_path: Path, message: str).
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = url.split("/")[-1].split("?")[0]

    local_path = cache_dir / filename

    # Check if file already exists and is valid
    if not force_refresh and local_path.exists():
        if expected_checksum:
            actual_checksum = calculate_sha256(local_path)
            if actual_checksum.lower() == expected_checksum.lower():
                return True, local_path, f"Using cached file: {local_path.name}"
        else:
            return True, local_path, f"Using cached file: {local_path.name}"

    success, message = fetch_data_with_validation(
        url, local_path, expected_checksum
    )

    if success:
        return True, local_path, message
    else:
        return False, local_path, message


# Example usage and basic validation
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch and validate data files with checksums."
    )
    parser.add_argument("--url", required=True, help="URL to fetch data from")
    parser.add_argument(
        "--output", required=True, help="Local path to save the file"
    )
    parser.add_argument(
        "--checksum", help="Expected SHA-256 checksum (optional)"
    )

    args = parser.parse_args()

    success, message = fetch_data_with_validation(
        args.url, args.output, args.checksum
    )

    if success:
        print(f"SUCCESS: {message}")
        exit(0)
    else:
        print(f"FAILED: {message}")
        exit(1)
