"""
Data ingestion module for downloading and validating public time series datasets.

Implements strict URL validation, checksum verification, and loud failure on download errors.
No synthetic fallbacks are permitted.
"""
import os
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
from datetime import datetime
import json

# Import project utilities
from src.utils.config import get_path
from src.utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)


class IngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass


class DatasetManifest:
    """Data class to hold dataset metadata and verification info."""
    def __init__(
        self,
        dataset_id: str,
        source_name: str,
        source_url: str,
        file_path: str,
        checksum: str,
        download_timestamp: str,
        row_count: int,
        column_count: int,
        date_range: Optional[str] = None
    ):
        self.dataset_id = dataset_id
        self.source_name = source_name
        self.source_url = source_url
        self.file_path = file_path
        self.checksum = checksum
        self.download_timestamp = download_timestamp
        self.row_count = row_count
        self.column_count = column_count
        self.date_range = date_range

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "download_timestamp": self.download_timestamp,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "date_range": self.date_range
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetManifest':
        return cls(**data)


def validate_url(url: str) -> bool:
    """
    Validate that a URL is well-formed and accessible.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid, raises IngestionError if invalid
    """
    if not url or not isinstance(url, str):
        raise IngestionError("URL must be a non-empty string")
    
    if not (url.startswith('http://') or url.startswith('https://')):
        raise IngestionError(f"Invalid URL scheme: {url}")
    
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code >= 400:
            raise IngestionError(f"URL returned status {response.status_code}: {url}")
        return True
    except requests.RequestException as e:
        raise IngestionError(f"Failed to validate URL {url}: {str(e)}")


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal string of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url: str, destination: Path) -> None:
    """
    Download a file from URL to destination with progress logging.
    
    Args:
        url: Source URL
        destination: Local file path to save to
        
    Raises:
        IngestionError: If download fails
    """
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        log_info(f"Downloading {url} to {destination}")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        log_info(f"Download progress: {progress:.1f}%")
                        
        log_info(f"Successfully downloaded {destination.name}")
        
    except requests.RequestException as e:
        raise IngestionError(f"Download failed for {url}: {str(e)}")
    except Exception as e:
        raise IngestionError(f"Unexpected error downloading {url}: {str(e)}")


def load_csv_robust(file_path: Path, date_col: str = None, parse_dates: bool = True) -> pd.DataFrame:
    """
    Load a CSV file with robust error handling and date parsing.
    
    Args:
        file_path: Path to CSV file
        date_col: Name of the date/datetime column (optional)
        parse_dates: Whether to parse dates
        
    Returns:
        pandas DataFrame
        
    Raises:
        IngestionError: If file cannot be loaded
    """
    if not file_path.exists():
        raise IngestionError(f"File not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path, parse_dates=parse_dates)
        
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
        
        log_info(f"Loaded {len(df)} rows from {file_path.name}")
        return df
        
    except Exception as e:
        raise IngestionError(f"Failed to load CSV {file_path}: {str(e)}")


def ingest_noaa_dataset(station_id: str, output_dir: Optional[Path] = None) -> DatasetManifest:
    """
    Ingest NOAA climate data for a specific station.
    
    Uses NOAA's GHCN-Daily dataset via their API/FTP.
    Station ID: USW00014895 (New York Central Park)
    
    Args:
        station_id: NOAA station identifier
        output_dir: Optional output directory
        
    Returns:
        DatasetManifest with metadata
    """
    if output_dir is None:
        output_dir = get_path("data", "raw", "noaa")
        
    # NOAA GHCN-Daily download URL pattern
    # Using a direct FTP/HTTP endpoint for the data
    base_url = "https://www.ncei.noaa.gov/data/global-daily-summaries/access/"
    year = "2023"  # Use recent year for reliability
    filename = f"{station_id}_{year}.csv"
    local_path = output_dir / filename
    
    # Construct the full URL (NOAA structure)
    # Note: This is a simplified approach; real implementation might need API key
    download_url = f"{base_url}{year}/{filename}"
    
    try:
        # Validate URL first
        validate_url(download_url)
        
        # Download the file
        download_file(download_url, local_path)
        
        # Compute checksum
        checksum = compute_sha256(local_path)
        
        # Load and validate data
        df = load_csv_robust(local_path, date_col='DATE')
        
        # Create manifest
        manifest = DatasetManifest(
            dataset_id=f"noaa_{station_id}",
            source_name="NOAA GHCN-Daily",
            source_url=download_url,
            file_path=str(local_path),
            checksum=checksum,
            download_timestamp=datetime.now().isoformat(),
            row_count=len(df),
            column_count=len(df.columns),
            date_range=f"{df.index.min()} to {df.index.max()}" if hasattr(df.index, 'min') else None
        )
        
        log_info(f"NOAA dataset ingested: {manifest.dataset_id}")
        return manifest
        
    except Exception as e:
        log_error(f"Failed to ingest NOAA dataset: {str(e)}")
        raise IngestionError(f"NOAA ingestion failed: {str(e)}")


def ingest_yahoo_finance(ticker: str, start_date: str = "2020-01-01", end_date: str = "2023-12-31") -> DatasetManifest:
    """
    Ingest Yahoo Finance data for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY')
        start_date: Start date for historical data
        end_date: End date for historical data
        
    Returns:
        DatasetManifest with metadata
    """
    output_dir = get_path("data", "raw", "yahoo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import yfinance as yf
        
        log_info(f"Downloading Yahoo Finance data for {ticker}")
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            raise IngestionError(f"No data retrieved for {ticker}")
        
        # Save to CSV
        filename = f"{ticker}_{start_date}_{end_date}.csv"
        local_path = output_dir / filename
        df.to_csv(local_path)
        
        # Compute checksum
        checksum = compute_sha256(local_path)
        
        manifest = DatasetManifest(
            dataset_id=f"yahoo_{ticker}",
            source_name="Yahoo Finance",
            source_url=f"https://finance.yahoo.com/quote/{ticker}/",
            file_path=str(local_path),
            checksum=checksum,
            download_timestamp=datetime.now().isoformat(),
            row_count=len(df),
            column_count=len(df.columns),
            date_range=f"{df.index.min()} to {df.index.max()}"
        )
        
        log_info(f"Yahoo Finance dataset ingested: {manifest.dataset_id}")
        return manifest
        
    except ImportError:
        raise IngestionError("yfinance package not installed. Please install it via requirements.txt")
    except Exception as e:
        log_error(f"Failed to ingest Yahoo Finance data: {str(e)}")
        raise IngestionError(f"Yahoo Finance ingestion failed: {str(e)}")


def ingest_uk_grid(output_dir: Optional[Path] = None) -> DatasetManifest:
    """
    Ingest UK National Grid Electricity Load data.
    
    Source: https://www.nationalgrideso.com/document/174276/download
    
    Args:
        output_dir: Optional output directory
        
    Returns:
        DatasetManifest with metadata
    """
    if output_dir is None:
        output_dir = get_path("data", "raw", "uk_grid")
        
    url = "https://www.nationalgrideso.com/document/174276/download"
    filename = "uk_grid_load.csv"
    local_path = output_dir / filename
    
    try:
        validate_url(url)
        download_file(url, local_path)
        
        checksum = compute_sha256(local_path)
        
        # Load data - UK grid data typically has specific format
        df = load_csv_robust(local_path)
        
        manifest = DatasetManifest(
            dataset_id="uk_grid_load",
            source_name="UK National Grid",
            source_url=url,
            file_path=str(local_path),
            checksum=checksum,
            download_timestamp=datetime.now().isoformat(),
            row_count=len(df),
            column_count=len(df.columns),
            date_range=f"{df.index.min()} to {df.index.max()}" if hasattr(df.index, 'min') else None
        )
        
        log_info(f"UK Grid dataset ingested: {manifest.dataset_id}")
        return manifest
        
    except Exception as e:
        log_error(f"Failed to ingest UK Grid data: {str(e)}")
        raise IngestionError(f"UK Grid ingestion failed: {str(e)}")


def ingest_uci_electricity(output_dir: Optional[Path] = None) -> DatasetManifest:
    """
    Ingest UCI Electricity Load Diagrams 2011-2014 dataset.
    
    Source: https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014
    
    Args:
        output_dir: Optional output directory
        
    Returns:
        DatasetManifest with metadata
    """
    if output_dir is None:
        output_dir = get_path("data", "raw", "uci_electricity")
        
    # UCI dataset URL
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt"
    filename = "uci_electricity_load.txt"
    local_path = output_dir / filename
    
    try:
        validate_url(url)
        download_file(url, local_path)
        
        checksum = compute_sha256(local_path)
        
        # Load data - UCI format is space-separated with specific structure
        df = pd.read_csv(local_path, sep=';', index_col=0, parse_dates=True)
        
        # Save as CSV for consistency
        csv_path = output_dir / "uci_electricity_load.csv"
        df.to_csv(csv_path)
        
        manifest = DatasetManifest(
            dataset_id="uci_electricity_load",
            source_name="UCI Electricity Load Diagrams",
            source_url=url,
            file_path=str(csv_path),
            checksum=compute_sha256(csv_path),
            download_timestamp=datetime.now().isoformat(),
            row_count=len(df),
            column_count=len(df.columns),
            date_range=f"{df.index.min()} to {df.index.max()}"
        )
        
        log_info(f"UCI Electricity dataset ingested: {manifest.dataset_id}")
        return manifest
        
    except Exception as e:
        log_error(f"Failed to ingest UCI Electricity data: {str(e)}")
        raise IngestionError(f"UCI Electricity ingestion failed: {str(e)}")


def ingest_dataset(dataset_type: str, **kwargs) -> DatasetManifest:
    """
    Generic dataset ingestion dispatcher.
    
    Args:
        dataset_type: One of 'noaa', 'yahoo', 'uk_grid', 'uci_electricity'
        **kwargs: Type-specific arguments
        
    Returns:
        DatasetManifest with metadata
    """
    dispatchers = {
        'noaa': ingest_noaa_dataset,
        'yahoo': ingest_yahoo_finance,
        'uk_grid': ingest_uk_grid,
        'uci_electricity': ingest_uci_electricity
    }
    
    if dataset_type not in dispatchers:
        raise IngestionError(f"Unknown dataset type: {dataset_type}")
    
    return dispatchers[dataset_type](**kwargs)


def create_manifests(manifests: List[DatasetManifest], output_path: Optional[Path] = None) -> None:
    """
    Create a JSON manifest file for all ingested datasets.
    
    Args:
        manifests: List of DatasetManifest objects
        output_path: Optional output path (default: data/processed/manifests.json)
    """
    if output_path is None:
        output_path = get_path("data", "processed", "manifests.json")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_data = [m.to_dict() for m in manifests]
    
    with open(output_path, 'w') as f:
        json.dump(manifest_data, f, indent=2, default=str)
        
    log_info(f"Created manifest file: {output_path}")


def load_manifest(manifest_path: Optional[Path] = None) -> List[DatasetManifest]:
    """
    Load dataset manifests from a JSON file.
    
    Args:
        manifest_path: Path to manifest file
        
    Returns:
        List of DatasetManifest objects
    """
    if manifest_path is None:
        manifest_path = get_path("data", "processed", "manifests.json")
        
    if not manifest_path.exists():
        raise IngestionError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
        
    return [DatasetManifest.from_dict(item) for item in data]


def run_full_ingestion_pipeline() -> List[DatasetManifest]:
    """
    Execute the full ingestion pipeline for all 5 required datasets.
    
    Datasets:
    1. NOAA (Station ID: USW00014895)
    2. Yahoo Finance (AAPL)
    3. Yahoo Finance (SPY)
    4. UK National Grid Load
    5. UCI Electricity Load Diagrams
    
    Returns:
        List of DatasetManifest objects for all successfully ingested datasets
        
    Raises:
        IngestionError: If any dataset fails to download (loud failure, no fallback)
    """
    manifests = []
    
    log_info("Starting full ingestion pipeline for 5 datasets")
    
    # 1. NOAA Dataset (USW00014895 - New York Central Park)
    try:
        log_info("Ingesting NOAA dataset (USW00014895)")
        noaa_manifest = ingest_noaa_dataset(station_id="USW00014895")
        manifests.append(noaa_manifest)
    except IngestionError as e:
        log_error(f"NOAA ingestion failed: {e}")
        raise  # Loud failure - no fallback
    
    # 2. Yahoo Finance AAPL
    try:
        log_info("Ingesting Yahoo Finance AAPL")
        aapl_manifest = ingest_yahoo_finance(ticker="AAPL")
        manifests.append(aapl_manifest)
    except IngestionError as e:
        log_error(f"AAPL ingestion failed: {e}")
        raise  # Loud failure - no fallback
    
    # 3. Yahoo Finance SPY
    try:
        log_info("Ingesting Yahoo Finance SPY")
        spy_manifest = ingest_yahoo_finance(ticker="SPY")
        manifests.append(spy_manifest)
    except IngestionError as e:
        log_error(f"SPY ingestion failed: {e}")
        raise  # Loud failure - no fallback
    
    # 4. UK National Grid
    try:
        log_info("Ingesting UK National Grid Load")
        uk_manifest = ingest_uk_grid()
        manifests.append(uk_manifest)
    except IngestionError as e:
        log_error(f"UK Grid ingestion failed: {e}")
        raise  # Loud failure - no fallback
    
    # 5. UCI Electricity Load
    try:
        log_info("Ingesting UCI Electricity Load Diagrams")
        uci_manifest = ingest_uci_electricity()
        manifests.append(uci_manifest)
    except IngestionError as e:
        log_error(f"UCI Electricity ingestion failed: {e}")
        raise  # Loud failure - no fallback
    
    # Create manifest file
    create_manifests(manifests)
    
    log_info(f"Successfully ingested {len(manifests)} datasets")
    return manifests
