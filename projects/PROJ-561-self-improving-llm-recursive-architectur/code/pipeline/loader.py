"""
pipeline/loader.py
------------------
Utilities for dataset downloading, checksum handling, and URL verification.
Implements the required `download_and_checksum` function for task T001d.
"""

import os
import time
import hashlib
import logging
import random
import requests

from typing import List, Tuple

from datasets import load_dataset

logger = logging.getLogger(__name__)


class HFTransientError(Exception):
    """Exception raised for transient errors when accessing HuggingFace Hub."""
    pass


def exponential_backoff(func):
    """
    Decorator implementing exponential backoff with jitter.
    Initial delay: 30 seconds, maximum retries: 5.
    Retries are performed for any exception (including HFTransientError).
    After the maximum number of retries, the original exception is re‑raised.
    """
    def wrapper(*args, **kwargs):
        max_retries = 5
        delay = 30  # seconds
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if attempt == max_retries:
                    logger.error(f"Exponential backoff exhausted after {max_retries} retries.")
                    raise
                # exponential increase with jitter
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                logger.warning(f"Retry {attempt + 1}/{max_retries} after exception: {exc}. Sleeping {sleep_time:.2f}s.")
                time.sleep(sleep_time)
                delay *= 2
    return wrapper


@exponential_backoff
def _head_request(url: str) -> requests.Response:
    """
    Perform a ``HEAD`` request to ``url`` with a short timeout.

    The ``exponential_backoff`` decorator will automatically retry the call
    on any exception (including network errors and non‑2xx HTTP responses).

    Args:
        url: The URL to probe.

    Returns:
        The ``requests.Response`` object if the request succeeds.

    Raises:
        requests.HTTPError: If the response status is not successful.
    """
    response = requests.head(url, timeout=5, allow_redirects=True)
    response.raise_for_status()
    return response


def verify_urls(urls: List[str]) -> bool:
    """
    Verify that all URLs in ``urls`` are reachable.

    The function iterates over the supplied URLs and performs a ``HEAD``
    request for each, using exponential back‑off to handle transient failures
    (e.g., rate‑limits or temporary network issues).  If any URL remains
    unreachable after the maximum number of retries, a ``ValueError`` is raised
    with a clear message indicating which URL failed.

    Args:
        urls: List of URL strings to verify.

    Returns:
        ``True`` if every URL responded successfully.

    Raises:
        ValueError: If any URL is unreachable after retries.
    """
    for url in urls:
        try:
            _head_request(url)
        except Exception as exc:
            raise ValueError(f"Unable to reach URL: {url}") from exc
    return True


def calculate_sha256(file_path: str) -> str:
    """
    Calculates the SHA‑256 checksum of a single file.

    Args:
        file_path: Path to the file whose checksum is to be computed.

    Returns:
        Hexadecimal SHA‑256 digest string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_directory_checksum(dir_path: str) -> str:
    """
    Calculates a SHA‑256 checksum for a directory by hashing the concatenation
    of the SHA‑256 checksums of all files (sorted by filename) within the directory.

    Args:
        dir_path: Path to the directory.

    Returns:
        Hexadecimal SHA‑256 digest representing the directory contents.
    """
    if not os.path.isdir(dir_path):
        raise ValueError(f"Provided path is not a directory: {dir_path}")

    file_hashes = []
    for root, _, files in os.walk(dir_path):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            # Skip the checksum file itself if it already exists
            if fname.upper() in ("SHA256SUM", "SHA256SUMS", "SHA256"):
                continue
            file_hashes.append(calculate_sha256(fpath))

    # Concatenate all file hashes in deterministic order and hash the result
    combined = "".join(file_hashes).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def download_and_checksum(dataset_name: str, dest_path: str) -> str:
    """
    Downloads a dataset from the HuggingFace Hub (if not already present) into
    ``dest_path``, computes the SHA‑256 checksum of the resulting directory,
    writes the checksum to a ``SHA256SUM`` file alongside the data, and returns
    the checksum string.

    The function is idempotent: if a checksum file already exists, it is read
    and returned without re‑downloading the dataset.

    Args:
        dataset_name: The identifier of the dataset on the HuggingFace Hub
                      (e.g., ``"openwebtext"`` or ``"gsm8k"``).
        dest_path:    Directory where the dataset should be materialised.

    Returns:
        Hexadecimal SHA‑256 checksum of the directory contents.

    Raises:
        Exception: Propagates any error raised by the HuggingFace ``datasets``
                   library or by filesystem operations.
    """
    # Ensure the destination directory exists
    os.makedirs(dest_path, exist_ok=True)

    checksum_file = os.path.join(dest_path, "SHA256SUM")

    # If a checksum already exists, trust that the dataset is present
    if os.path.isfile(checksum_file):
        with open(checksum_file, "r") as f:
            existing_checksum = f.read().strip()
        logger.info(f"Checksum file found for '{dataset_name}'. Using cached checksum.")
        return existing_checksum

    # Load the dataset (this triggers download into the cache_dir)
    try:
        logger.info(f"Downloading dataset '{dataset_name}' into '{dest_path}'.")
        ds = load_dataset(dataset_name, cache_dir=dest_path)
    except Exception as exc:
        logger.error(f"Failed to download dataset '{dataset_name}': {exc}")
        raise

    # Persist the dataset to the destination directory in a deterministic format
    try:
        # ``save_to_disk`` will create a sub‑directory structure under ``dest_path``.
        # If ``dest_path`` already contains a previous download, this will overwrite
        # the existing files, which is acceptable for reproducibility.
        ds.save_to_disk(dest_path)
    except Exception as exc:
        logger.error(f"Failed to save dataset '{dataset_name}' to disk: {exc}")
        raise

    # Compute the checksum of the directory
    checksum = calculate_directory_checksum(dest_path)

    # Write the checksum file
    with open(checksum_file, "w") as f:
        f.write(checksum)

    logger.info(f"Dataset '{dataset_name}' downloaded and checksummed: {checksum}")
    return checksum


# Stub implementations for dataset‑specific loaders (to be completed by later tasks)
def load_openwebtext(dest_path: str = None) -> str:
    """
    Stub for loading the OpenWebText dataset.
    Returns the path to the dataset directory if implemented.
    """
    raise NotImplementedError("load_openwebtext is not implemented yet.")


def load_gsm8k(dest_path: str = None) -> str:
    """
    Stub for loading the GSM8K dataset.
    Returns the path to the dataset directory if implemented.
    """
    raise NotImplementedError("load_gsm8k is not implemented yet.")


def load_arc_challenge(dest_path: str = None) -> str:
    """
    Stub for loading the ARC‑Challenge dataset.
    Returns the path to the dataset directory if implemented.
    """
    raise NotImplementedError("load_arc_challenge is not implemented yet.")


def load_boolq(dest_path: str = None) -> str:
    """
    Stub for loading the BoolQ dataset.
    Returns the path to the dataset directory if implemented.
    """
    raise NotImplementedError("load_boolq is not implemented yet.")


def load_and_verify(dataset_name: str, dest_path: str) -> Tuple[str, str]:
    """
    Convenience wrapper that downloads a dataset and returns both the path
    to the materialised data and its SHA‑256 checksum.

    Args:
        dataset_name: Name of the HuggingFace dataset.
        dest_path:    Destination directory for the dataset.

    Returns:
        Tuple of (path_to_dataset, checksum).
    """
    checksum = download_and_checksum(dataset_name, dest_path)
    return dest_path, checksum


def load_local_dataset(path: str):
    """
    Loads a dataset that has already been materialised on disk.
    Placeholder for future implementation.
    """
    raise NotImplementedError("load_local_dataset is not implemented yet.")


def load_all_datasets() -> None:
    """
    Convenience function to download and verify all required datasets.
    Currently invokes ``download_and_checksum`` for each dataset name.
    """
    from config import get_config

    cfg = get_config()
    datasets_info = {
        "openwebtext": cfg.paths.data_raw,
        "gsm8k": cfg.paths.data_raw,
        "arc_challenge": cfg.paths.data_raw,
        "boolq": cfg.paths.data_raw,
    }

    for name, path in datasets_info.items():
        download_and_checksum(name, path)
