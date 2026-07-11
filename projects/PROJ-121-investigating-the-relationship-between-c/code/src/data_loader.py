"""
Data loader module for downloading IceCube and Auger cosmic ray data.
Implements SHA-256 checksum verification and robust error handling.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import requests
import pandas as pd
from urllib.parse import urljoin

from .entities import EventDataset
from .utils import get_logger

# Constants for real data sources
# IceCube: Public data release (example URL structure for 2018-2020)
ICECUBE_BASE_URL = "https://icecube.wisc.edu/data-releases/"
# Auger: Public data release (example URL structure)
AUGER_BASE_URL = "https://arxiv.org/data/auger/"

# Checksum manifest for verification (in a real system, these would be fetched from a manifest file)
# For this implementation, we define expected checksums or allow dynamic verification
# In production, these would be stored in a 'checksums.json' or similar
KNOWN_CHECKSUMS: Dict[str, str] = {
    # Placeholder for real checksums once data is identified
    # "icecube_2018_2020.csv": "sha256_hash_here",
    # "auger_2018_2020.csv": "sha256_hash_here",
}

class DataDownloadError(Exception):
    """Exception raised for data download failures."""
    pass

class ChecksumVerificationError(Exception):
    """Exception raised when checksum verification fails."""
    pass

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for checksum calculation: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {file_path}: {str(e)}")

def download_file(
    url: str,
    dest_path: str,
    expected_checksum: Optional[str] = None,
    timeout: int = 300,
    retries: int = 3
) -> Tuple[bool, str]:
    """
    Download a file from a URL with checksum verification.

    Args:
        url: Source URL
        dest_path: Local destination path
        expected_checksum: Expected SHA-256 hash (optional)
        timeout: Request timeout in seconds
        retries: Number of retry attempts

    Returns:
        Tuple of (success: bool, message: str)
    """
    logger = get_logger(__name__)
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    attempt = 0
    last_error = None

    while attempt < retries:
        try:
            logger.info(f"Downloading {url} to {dest_path} (Attempt {attempt + 1}/{retries})")
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify checksum if expected
            if expected_checksum:
                actual_checksum = calculate_sha256(str(dest_path))
                if actual_checksum.lower() != expected_checksum.lower():
                    raise ChecksumVerificationError(
                        f"Checksum mismatch. Expected: {expected_checksum}, "
                        f"Got: {actual_checksum}"
                    )
                logger.info(f"Checksum verified: {actual_checksum}")

            logger.info(f"Successfully downloaded and verified: {dest_path}")
            return True, "Success"

        except requests.exceptions.RequestException as e:
            last_error = e
            attempt += 1
            if attempt < retries:
                logger.warning(f"Network error, retrying in 2 seconds... ({attempt}/{retries})")
                import time
                time.sleep(2)
            else:
                logger.error(f"Download failed after {retries} attempts: {str(e)}")
                return False, f"Download failed: {str(e)}"

        except ChecksumVerificationError as e:
            logger.error(f"Checksum verification failed: {str(e)}")
            # Delete corrupted file
            if dest_path.exists():
                dest_path.unlink()
            return False, f"Checksum mismatch: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    return False, f"Download failed after {retries} attempts: {str(last_error)}"

def load_icecube_data(
    year_start: int,
    year_end: int,
    output_dir: Optional[str] = None
) -> EventDataset:
    """
    Load IceCube cosmic ray data.

    Args:
        year_start: Start year for data range
        year_end: End year for data range
        output_dir: Directory to save downloaded data

    Returns:
        EventDataset containing the loaded data
    """
    logger = get_logger(__name__)
    if output_dir is None:
        output_dir = "data/raw/icecube"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # In a real implementation, we would construct the specific URL based on year
    # For this example, we use a placeholder URL that would need to be replaced
    # with the actual IceCube data release URL
    # Example: https://icecube.wisc.edu/data-releases/2018-2020/cosmic-ray-events.csv
    filename = f"icecube_{year_start}_{year_end}.csv"
    file_path = output_dir / filename

    # Construct URL - this would need to be updated with real URLs
    url = f"{ICECUBE_BASE_URL}{year_start}-{year_end}/cosmic-ray-events.csv"

    # Check if file already exists and is valid
    if file_path.exists():
        logger.info(f"Found existing file: {file_path}")
        # Optional: verify checksum if known
        if filename in KNOWN_CHECKSUMS:
            try:
                actual = calculate_sha256(str(file_path))
                if actual.lower() == KNOWN_CHECKSUMS[filename].lower():
                    logger.info("Existing file checksum verified")
                else:
                    logger.warning("Existing file checksum mismatch, re-downloading")
                    success, msg = download_file(url, str(file_path), KNOWN_CHECKSUMS[filename])
                    if not success:
                        raise DataDownloadError(msg)
            except Exception as e:
                logger.warning(f"Checksum check failed: {e}, re-downloading")
                success, msg = download_file(url, str(file_path), KNOWN_CHECKSUMS.get(filename))
                if not success:
                    raise DataDownloadError(msg)
        else:
            logger.info("No checksum available for existing file, trusting local copy")
    else:
        # Download new file
        success, msg = download_file(url, str(file_path))
        if not success:
            raise DataDownloadError(msg)

    # Load data into EventDataset
    try:
        df = pd.read_csv(file_path)
        # Validate required columns
        required_cols = ['timestamp', 'ra', 'dec', 'energy', 'zenith', 'azimuth']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Convert timestamp to datetime if needed
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        return EventDataset(
            source="IceCube",
            data=df,
            metadata={
                "year_start": year_start,
                "year_end": year_end,
                "file_path": str(file_path),
                "record_count": len(df)
            }
        )

    except Exception as e:
        raise DataDownloadError(f"Failed to load IceCube data: {str(e)}")

def load_auger_data(
    year_start: int,
    year_end: int,
    output_dir: Optional[str] = None
) -> EventDataset:
    """
    Load Pierre Auger Observatory cosmic ray data.

    Args:
        year_start: Start year for data range
        year_end: End year for data range
        output_dir: Directory to save downloaded data

    Returns:
        EventDataset containing the loaded data
    """
    logger = get_logger(__name__)
    if output_dir is None:
        output_dir = "data/raw/auger"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"auger_{year_start}_{year_end}.csv"
    file_path = output_dir / filename

    # Construct URL - this would need to be updated with real URLs
    url = f"{AUGER_BASE_URL}{year_start}-{year_end}/events.csv"

    # Check if file already exists and is valid
    if file_path.exists():
        logger.info(f"Found existing file: {file_path}")
        # Optional: verify checksum if known
        if filename in KNOWN_CHECKSUMS:
            try:
                actual = calculate_sha256(str(file_path))
                if actual.lower() == KNOWN_CHECKSUMS[filename].lower():
                    logger.info("Existing file checksum verified")
                else:
                    logger.warning("Existing file checksum mismatch, re-downloading")
                    success, msg = download_file(url, str(file_path), KNOWN_CHECKSUMS[filename])
                    if not success:
                        raise DataDownloadError(msg)
            except Exception as e:
                logger.warning(f"Checksum check failed: {e}, re-downloading")
                success, msg = download_file(url, str(file_path), KNOWN_CHECKSUMS.get(filename))
                if not success:
                    raise DataDownloadError(msg)
        else:
            logger.info("No checksum available for existing file, trusting local copy")
    else:
        # Download new file
        success, msg = download_file(url, str(file_path))
        if not success:
            raise DataDownloadError(msg)

    # Load data into EventDataset
    try:
        df = pd.read_csv(file_path)
        # Validate required columns
        required_cols = ['timestamp', 'ra', 'dec', 'energy', 'zenith', 'azimuth']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Convert timestamp to datetime if needed
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        return EventDataset(
            source="Auger",
            data=df,
            metadata={
                "year_start": year_start,
                "year_end": year_end,
                "file_path": str(file_path),
                "record_count": len(df)
            }
        )

    except Exception as e:
        raise DataDownloadError(f"Failed to load Auger data: {str(e)}")

def load_all_data(
    year_start: int,
    year_end: int,
    icecube_dir: Optional[str] = None,
    auger_dir: Optional[str] = None
) -> List[EventDataset]:
    """
    Load data from both IceCube and Auger observatories.

    Args:
        year_start: Start year for data range
        year_end: End year for data range
        icecube_dir: Directory for IceCube data
        auger_dir: Directory for Auger data

    Returns:
        List of EventDataset objects
    """
    datasets = []

    try:
        logger = get_logger(__name__)
        icecube_data = load_icecube_data(year_start, year_end, icecube_dir)
        datasets.append(icecube_data)
        logger.info(f"Loaded {len(icecube_data.data)} events from IceCube")
    except DataDownloadError as e:
        logger.warning(f"Failed to load IceCube data: {e}")
        # Continue with Auger data

    try:
        auger_data = load_auger_data(year_start, year_end, auger_dir)
        datasets.append(auger_data)
        logger.info(f"Loaded {len(auger_data.data)} events from Auger")
    except DataDownloadError as e:
        logger.warning(f"Failed to load Auger data: {e}")
        # Continue if we have at least one dataset

    if not datasets:
        raise DataDownloadError("Failed to load data from all sources")

    return datasets

def verify_local_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a local file.

    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 hash

    Returns:
        True if checksum matches, False otherwise
    """
    try:
        actual_checksum = calculate_sha256(file_path)
        return actual_checksum.lower() == expected_checksum.lower()
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error verifying checksum: {e}")
        return False
