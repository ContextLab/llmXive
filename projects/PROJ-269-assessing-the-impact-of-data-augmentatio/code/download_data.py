"""
Data download and verification module.

This module handles the fetching of UCI datasets from canonical URLs,
verification of cryptographic checksums, and logging of fetch deviations.
"""

import os
import hashlib
import logging
import json
import requests
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Raised when a dataset fetch fails or checksum mismatch occurs."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def compute_sha256(filepath: str) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        filepath: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_verified_datasets() -> Dict[str, Any]:
    """
    Load verified datasets configuration from JSON.

    Returns:
        Dictionary mapping dataset names to their configuration (URL, checksum).

    Raises:
        FileNotFoundError: If the verified_datasets.json file does not exist.
    """
    config_path = Path("code/verified_datasets.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Verified datasets config not found at {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def download_dataset(
    dataset_name: str,
    url: str,
    expected_checksum: str,
    output_dir: str
) -> str:
    """
    Download a dataset and verify its checksum.

    Args:
        dataset_name: Name of the dataset (used for filename).
        url: Canonical URL to fetch the dataset from.
        expected_checksum: Expected SHA256 checksum for verification.
        output_dir: Directory to save the downloaded file.

    Returns:
        Path to the downloaded and verified file.

    Raises:
        DataFetchError: If download fails or checksum mismatch occurs.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{dataset_name}.csv"
    filepath = os.path.join(output_dir, filename)

    logger.info(f"Downloading {dataset_name} from {url}")
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        actual_checksum = compute_sha256(filepath)

        if actual_checksum != expected_checksum:
            raise DataFetchError(
                f"Checksum mismatch for {dataset_name}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )

        logger.info(f"Successfully downloaded and verified {dataset_name}")
        return filepath

    except requests.RequestException as e:
        raise DataFetchError(f"Failed to download {dataset_name}: {str(e)}")


def log_deviation(
    dataset_name: str,
    message: str,
    log_path: str
) -> None:
    """
    Log a deviation event to a JSON log file.

    Args:
        dataset_name: Name of the dataset that caused the deviation.
        message: Description of the deviation.
        log_path: Path to the JSON log file.
    """
    log_entry = {
        "dataset_name": dataset_name,
        "status": "deviation",
        "message": message,
        "timestamp": "2024-01-01T00:00:00"  # Placeholder for actual timestamp logic
    }

    log_data: List[Dict[str, Any]] = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            log_data = []

    log_data.append(log_entry)

    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)

    logger.warning(f"Logged deviation for {dataset_name}: {message}")


def main() -> None:
    """Main entry point for data download."""
    base_dir = Path("projects/PROJ-269-assessing-the-impact-of-data-augmentatio")
    data_raw_dir = base_dir / "data" / "raw"
    data_derived_dir = base_dir / "data" / "derived"

    os.makedirs(data_raw_dir, exist_ok=True)
    os.makedirs(data_derived_dir, exist_ok=True)

    fetch_count_log_path = str(data_derived_dir / "fetch_count.log")

    try:
        verified_datasets = load_verified_datasets()
        fetched_count = 0
        total_count = len(verified_datasets)

        for dataset_name, config in verified_datasets.items():
            url = config["url"]
            expected_checksum = config["checksum"]

            try:
                download_dataset(dataset_name, url, expected_checksum, str(data_raw_dir))
                fetched_count += 1
            except DataFetchError as e:
                logger.error(f"Failed to fetch {dataset_name}: {str(e)}")
                log_deviation(dataset_name, str(e), fetch_count_log_path)

        # Log deviation if count doesn't meet spec (assuming spec requires all)
        if fetched_count < total_count:
            log_deviation(
                "summary",
                f"Only fetched {fetched_count}/{total_count} datasets",
                fetch_count_log_path
            )

        logger.info(f"Downloaded {fetched_count}/{total_count} datasets successfully")

    except Exception as e:
        logger.error(f"Fatal error in download process: {str(e)}")
        raise


if __name__ == "__main__":
    main()
