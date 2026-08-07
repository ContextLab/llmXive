"""
Data ingestion module for the llmXive research pipeline.
Handles downloading, validation, checksumming, and loading of time series datasets.
"""
import os
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
import json
import requests
import pandas as pd
from urllib.parse import urlparse

from src.utils.logging import get_logger

logger = get_logger(__name__)


class IngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass


@dataclass
class DatasetManifest:
    """Data class to store dataset metadata and status."""
    name: str
    source: str
    url: str
    local_path: str
    checksum: Optional[str] = None
    status: str = "pending"  # pending, downloaded, validated, failed
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    download_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'source': self.source,
            'url': self.url,
            'local_path': self.local_path,
            'checksum': self.checksum,
            'status': self.status,
            'error_message': self.error_message,
            'file_size': self.file_size,
            'download_timestamp': self.download_timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetManifest':
        return cls(**data)


def validate_url(url: str) -> bool:
    """
    Validate that a URL is well-formed and points to an allowed protocol.

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is valid, False otherwise.

    Raises:
        IngestionError: If the URL is invalid.
    """
    if not url or not isinstance(url, str):
        raise IngestionError("URL must be a non-empty string")

    try:
        parsed = urlparse(url)
        # Check protocol
        if parsed.scheme not in ['http', 'https']:
            raise IngestionError(f"Invalid protocol: {parsed.scheme}. Only http and https are allowed.")

        # Check netloc (domain)
        if not parsed.netloc:
            raise IngestionError("URL must have a valid domain")

        # Basic check for path
        if not parsed.path:
            raise IngestionError("URL must have a path component")

        return True

    except Exception as e:
        raise IngestionError(f"URL validation failed: {str(e)}")


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        IngestionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IngestionError(f"Failed to compute checksum for {file_path}: {str(e)}")


def download_file(url: str, destination: Union[str, Path], timeout: int = 300) -> Path:
    """
    Download a file from a URL to a destination path with strict error handling.

    Args:
        url: The URL to download from.
        destination: The local path to save the file.
        timeout: Request timeout in seconds.

    Returns:
        Path object of the downloaded file.

    Raises:
        IngestionError: If download fails for any reason.
    """
    validate_url(url)
    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading {url} to {dest_path}")

    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type and 'application' not in content_type:
            # Check if it's an error page
            if 'error' in response.text.lower() or 'not found' in response.text.lower():
                raise IngestionError(f"Download returned an error page: {url}")

        # Write file in chunks
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)

        # Verify file was created and has content
        if not dest_path.exists():
            raise IngestionError(f"Download failed: file not created at {dest_path}")

        file_size = dest_path.stat().st_size
        if file_size == 0:
            raise IngestionError(f"Download failed: file is empty at {dest_path}")

        logger.info(f"Downloaded {file_size} bytes to {dest_path}")
        return dest_path

    except requests.exceptions.RequestException as e:
        raise IngestionError(f"Network error during download: {str(e)}")
    except Exception as e:
        raise IngestionError(f"Unexpected error during download: {str(e)}")


def load_csv_robust(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Load a CSV file with robust error handling and common format adjustments.

    Args:
        file_path: Path to the CSV file.
        **kwargs: Additional arguments to pass to pd.read_csv.

    Returns:
        pandas DataFrame with the loaded data.

    Raises:
        IngestionError: If the file cannot be loaded or parsed.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise IngestionError(f"File not found: {file_path}")

    # Default parameters for robust loading
    default_kwargs = {
        'index_col': 0,
        'parse_dates': True,
        'low_memory': False
    }
    default_kwargs.update(kwargs)

    try:
        df = pd.read_csv(file_path, **default_kwargs)

        # Basic validation
        if df.empty:
            raise IngestionError(f"Loaded dataset is empty: {file_path}")

        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns from {file_path}")
        return df

    except pd.errors.EmptyDataError:
        raise IngestionError(f"File is empty or not a valid CSV: {file_path}")
    except pd.errors.ParserError as e:
        raise IngestionError(f"Failed to parse CSV {file_path}: {str(e)}")
    except Exception as e:
        raise IngestionError(f"Unexpected error loading {file_path}: {str(e)}")


def ingest_noaa_dataset(url: str, destination_dir: Union[str, Path], name: str = "noaa_data") -> DatasetManifest:
    """
    Ingest a NOAA dataset from a given URL.

    Args:
        url: URL to the NOAA dataset.
        destination_dir: Directory to save the downloaded data.
        name: Name identifier for the dataset.

    Returns:
        DatasetManifest object with ingestion details.
    """
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / f"{name}.csv"

    manifest = DatasetManifest(
        name=name,
        source="NOAA",
        url=url,
        local_path=str(local_path)
    )

    try:
        # Download
        download_file(url, local_path)
        manifest.status = "downloaded"

        # Compute checksum
        manifest.checksum = compute_sha256(local_path)
        manifest.status = "validated"

        # Load and validate
        df = load_csv_robust(local_path)
        manifest.file_size = local_path.stat().st_size

        logger.info(f"Successfully ingested NOAA dataset: {name}")
        return manifest

    except Exception as e:
        manifest.status = "failed"
        manifest.error_message = str(e)
        logger.error(f"Failed to ingest NOAA dataset {name}: {str(e)}")
        return manifest


def ingest_yahoo_finance(symbol: str, start_date: str, end_date: str,
                         destination_dir: Union[str, Path], name: str = None) -> DatasetManifest:
    """
    Ingest Yahoo Finance data using yfinance.

    Args:
        symbol: Stock ticker symbol.
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        destination_dir: Directory to save the data.
        name: Name identifier for the dataset.

    Returns:
        DatasetManifest object with ingestion details.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise IngestionError("yfinance is required for Yahoo Finance ingestion. Install with: pip install yfinance")

    if name is None:
        name = f"yahoo_{symbol}"

    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / f"{name}.csv"

    manifest = DatasetManifest(
        name=name,
        source="Yahoo Finance",
        url=f"https://finance.yahoo.com/quote/{symbol}",
        local_path=str(local_path)
    )

    try:
        logger.info(f"Downloading Yahoo Finance data for {symbol} ({start_date} to {end_date})")
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            raise IngestionError(f"No data retrieved for {symbol} in the specified date range")

        df.to_csv(local_path)
        manifest.status = "downloaded"

        # Compute checksum
        manifest.checksum = compute_sha256(local_path)
        manifest.status = "validated"

        manifest.file_size = local_path.stat().st_size
        logger.info(f"Successfully ingested Yahoo Finance dataset: {name}")
        return manifest

    except Exception as e:
        manifest.status = "failed"
        manifest.error_message = str(e)
        logger.error(f"Failed to ingest Yahoo Finance data for {symbol}: {str(e)}")
        return manifest


def ingest_uk_grid(url: str, destination_dir: Union[str, Path], name: str = "uk_grid_data") -> DatasetManifest:
    """
    Ingest UK National Grid load data.

    Args:
        url: URL to the dataset.
        destination_dir: Directory to save the data.
        name: Name identifier for the dataset.

    Returns:
        DatasetManifest object with ingestion details.
    """
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / f"{name}.csv"

    manifest = DatasetManifest(
        name=name,
        source="UK National Grid",
        url=url,
        local_path=str(local_path)
    )

    try:
        download_file(url, local_path)
        manifest.status = "downloaded"

        manifest.checksum = compute_sha256(local_path)
        manifest.status = "validated"

        df = load_csv_robust(local_path)
        manifest.file_size = local_path.stat().st_size

        logger.info(f"Successfully ingested UK Grid dataset: {name}")
        return manifest

    except Exception as e:
        manifest.status = "failed"
        manifest.error_message = str(e)
        logger.error(f"Failed to ingest UK Grid dataset {name}: {str(e)}")
        return manifest


def ingest_uci_electricity(url: str, destination_dir: Union[str, Path], name: str = "uci_electricity") -> DatasetManifest:
    """
    Ingest UCI Electricity Load Diagrams dataset.

    Args:
        url: URL to the dataset.
        destination_dir: Directory to save the data.
        name: Name identifier for the dataset.

    Returns:
        DatasetManifest object with ingestion details.
    """
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / f"{name}.csv"

    manifest = DatasetManifest(
        name=name,
        source="UCI Machine Learning Repository",
        url=url,
        local_path=str(local_path)
    )

    try:
        download_file(url, local_path)
        manifest.status = "downloaded"

        manifest.checksum = compute_sha256(local_path)
        manifest.status = "validated"

        df = load_csv_robust(local_path)
        manifest.file_size = local_path.stat().st_size

        logger.info(f"Successfully ingested UCI Electricity dataset: {name}")
        return manifest

    except Exception as e:
        manifest.status = "failed"
        manifest.error_message = str(e)
        logger.error(f"Failed to ingest UCI Electricity dataset {name}: {str(e)}")
        return manifest


def ingest_dataset(url: str, destination_dir: Union[str, Path], name: str,
                   source: str = "Generic") -> DatasetManifest:
    """
    Generic dataset ingestion function.

    Args:
        url: URL to the dataset.
        destination_dir: Directory to save the data.
        name: Name identifier for the dataset.
        source: Source name for the dataset.

    Returns:
        DatasetManifest object with ingestion details.
    """
    dest_dir = Path(destination_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / f"{name}.csv"

    manifest = DatasetManifest(
        name=name,
        source=source,
        url=url,
        local_path=str(local_path)
    )

    try:
        download_file(url, local_path)
        manifest.status = "downloaded"

        manifest.checksum = compute_sha256(local_path)
        manifest.status = "validated"

        df = load_csv_robust(local_path)
        manifest.file_size = local_path.stat().st_size

        logger.info(f"Successfully ingested dataset: {name}")
        return manifest

    except Exception as e:
        manifest.status = "failed"
        manifest.error_message = str(e)
        logger.error(f"Failed to ingest dataset {name}: {str(e)}")
        return manifest


def create_manifest(manifests: List[DatasetManifest], output_path: Union[str, Path]) -> Path:
    """
    Create a JSON manifest file from a list of DatasetManifest objects.

    Args:
        manifests: List of DatasetManifest objects.
        output_path: Path to save the manifest JSON file.

    Returns:
        Path object of the created manifest file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_data = [m.to_dict() for m in manifests]

    with open(output_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Created manifest file at {output_path}")
    return output_path


def load_manifest(manifest_path: Union[str, Path]) -> List[DatasetManifest]:
    """
    Load a manifest file and return a list of DatasetManifest objects.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        List of DatasetManifest objects.

    Raises:
        IngestionError: If the manifest cannot be loaded or parsed.
    """
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise IngestionError(f"Manifest file not found: {manifest_path}")

    try:
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)

        manifests = [DatasetManifest.from_dict(data) for data in manifest_data]
        logger.info(f"Loaded manifest with {len(manifests)} datasets from {manifest_path}")
        return manifests

    except json.JSONDecodeError as e:
        raise IngestionError(f"Failed to parse manifest JSON: {str(e)}")
    except Exception as e:
        raise IngestionError(f"Unexpected error loading manifest: {str(e)}")
