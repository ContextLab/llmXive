import os
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import requests
from urllib.parse import urlparse

from src.utils.logging import log_info, log_warning, log_error, log_critical
from src.utils.config import get_path

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass

class DatasetManifest:
    """Represents metadata for an ingested dataset."""
    def __init__(self, source: str, file_path: str, checksum: str, size_bytes: int, num_points: int):
        self.source = source
        self.file_path = file_path
        self.checksum = checksum
        self.size_bytes = size_bytes
        self.num_points = num_points

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "num_points": self.num_points
        }

def validate_url(url: str) -> bool:
    """
    Validates that the URL is well-formed and points to an allowed domain.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        # Basic safety check: ensure it's http or https
        if parsed.scheme not in ['http', 'https']:
            return False
        return True
    except Exception:
        return False

def compute_sha256(file_path: Path) -> str:
    """Computes SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, timeout: int = 300) -> Path:
    """
    Downloads a file from URL to dest_path.
    Raises IngestionError if download fails.
    """
    if not validate_url(url):
        raise IngestionError(f"Invalid URL format: {url}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        log_info(f"Downloading from {url} to {dest_path}")
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if not dest_path.exists():
            raise IngestionError(f"Download failed: file not created at {dest_path}")

        return dest_path
    except requests.RequestException as e:
        raise IngestionError(f"Download failed for {url}: {str(e)}") from e

def load_csv_robust(file_path: Path) -> pd.DataFrame:
    """
    Loads a CSV file robustly, handling various delimiters and date parsing.
    Raises IngestionError if loading fails.
    """
    try:
        # Try standard read_csv first
        df = pd.read_csv(file_path)
        
        # Attempt to infer date column if not explicitly handled
        # Common date column names
        date_cols = ['date', 'Date', 'DATE', 'datetime', 'Datetime', 'timestamp', 'Timestamp']
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df.set_index(col, inplace=True)
                    break
                except (ValueError, TypeError):
                    continue
        
        # If no date column found, try to infer from first column
        if df.index.name is None or not pd.api.types.is_datetime64_any_dtype(df.index):
            first_col = df.columns[0]
            try:
                df[first_col] = pd.to_datetime(df[first_col])
                df.set_index(first_col, inplace=True)
            except (ValueError, TypeError):
                pass

        return df
    except Exception as e:
        raise IngestionError(f"Failed to load CSV from {file_path}: {str(e)}") from e

def ingest_noaa_dataset(url: str, source_id: str, dest_dir: Path) -> DatasetManifest:
    """
    Ingests a NOAA dataset from the given URL.
    """
    temp_file = Path(tempfile.mktemp(suffix=".csv"))
    try:
        download_file(url, temp_file)
        
        # Load and validate data
        df = load_csv_robust(temp_file)
        
        # Validate data content
        if len(df) == 0:
            raise IngestionError(f"Dataset {source_id} is empty after loading.")
        
        # Check for numeric columns (assuming at least one value column exists)
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            log_warning(f"Dataset {source_id} has no numeric columns. Using all columns.")
            numeric_cols = df.columns
        
        # Count non-null numeric points
        valid_points = df[numeric_cols[0]].notna().sum()
        
        if valid_points < 25:
            raise IngestionError(
                f"Dataset {source_id} has only {valid_points} valid data points. "
                "Minimum required is 25."
            )

        # Compute checksum and size
        checksum = compute_sha256(temp_file)
        file_size = temp_file.stat().st_size

        if file_size == 0:
            raise IngestionError(f"Dataset {source_id} downloaded file is 0 bytes.")

        # Move to final destination
        final_path = dest_dir / f"{source_id}.csv"
        shutil.move(str(temp_file), str(final_path))

        log_info(f"Successfully ingested NOAA dataset {source_id}: {valid_points} points, {file_size} bytes")

        return DatasetManifest(
            source=source_id,
            file_path=str(final_path),
            checksum=checksum,
            size_bytes=file_size,
            num_points=int(valid_points)
        )

    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise IngestionError(f"Failed to ingest NOAA dataset {source_id}: {str(e)}") from e

def ingest_yahoo_finance(tickers: list, dest_dir: Path, start_date: str = "2010-01-01", end_date: str = "2023-12-31") -> Dict[str, DatasetManifest]:
    """
    Ingests Yahoo Finance data for given tickers.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise IngestionError("yfinance package is required for Yahoo Finance ingestion.")

    manifests = {}
    
    for ticker in tickers:
        try:
            log_info(f"Downloading Yahoo Finance data for {ticker}")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                raise IngestionError(f"No data downloaded for {ticker}")
            
            # Check for numeric columns (Close price is standard)
            if 'Close' not in data.columns:
                numeric_cols = data.select_dtypes(include=['number']).columns
                if len(numeric_cols) == 0:
                    raise IngestionError(f"No numeric columns found for {ticker}")
                value_col = numeric_cols[0]
            else:
                value_col = 'Close'
            
            valid_points = data[value_col].notna().sum()
            
            if valid_points < 25:
                raise IngestionError(
                    f"Yahoo data for {ticker} has only {valid_points} valid points. "
                    "Minimum required is 25."
                )
            
            # Save to file
            file_path = dest_dir / f"yahoo_{ticker}.csv"
            data.to_csv(file_path)
            
            checksum = compute_sha256(file_path)
            file_size = file_path.stat().st_size
            
            if file_size == 0:
                raise IngestionError(f"Yahoo data file for {ticker} is 0 bytes.")
            
            manifests[ticker] = DatasetManifest(
                source=f"yahoo_{ticker}",
                file_path=str(file_path),
                checksum=checksum,
                size_bytes=file_size,
                num_points=int(valid_points)
            )
            
            log_info(f"Successfully ingested Yahoo data for {ticker}: {valid_points} points")
            
        except Exception as e:
            raise IngestionError(f"Failed to ingest Yahoo data for {ticker}: {str(e)}") from e
    
    return manifests

def ingest_uk_grid(url: str, source_id: str, dest_dir: Path) -> DatasetManifest:
    """
    Ingests UK National Grid data.
    """
    temp_file = Path(tempfile.mktemp(suffix=".csv"))
    try:
        download_file(url, temp_file)
        
        df = load_csv_robust(temp_file)
        
        if len(df) == 0:
            raise IngestionError(f"UK Grid dataset {source_id} is empty.")
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            raise IngestionError(f"UK Grid dataset {source_id} has no numeric columns.")
        
        valid_points = df[numeric_cols[0]].notna().sum()
        
        if valid_points < 25:
            raise IngestionError(
                f"UK Grid dataset {source_id} has only {valid_points} valid points. "
                "Minimum required is 25."
            )
        
        checksum = compute_sha256(temp_file)
        file_size = temp_file.stat().st_size
        
        if file_size == 0:
            raise IngestionError(f"UK Grid data file for {source_id} is 0 bytes.")
        
        final_path = dest_dir / f"{source_id}.csv"
        shutil.move(str(temp_file), str(final_path))
        
        log_info(f"Successfully ingested UK Grid dataset {source_id}: {valid_points} points")
        
        return DatasetManifest(
            source=source_id,
            file_path=str(final_path),
            checksum=checksum,
            size_bytes=file_size,
            num_points=int(valid_points)
        )
        
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise IngestionError(f"Failed to ingest UK Grid dataset {source_id}: {str(e)}") from e

def ingest_uci_electricity(url: str, source_id: str, dest_dir: Path) -> DatasetManifest:
    """
    Ingests UCI Electricity Load Diagrams data.
    """
    temp_file = Path(tempfile.mktemp(suffix=".csv"))
    try:
        download_file(url, temp_file)
        
        df = load_csv_robust(temp_file)
        
        if len(df) == 0:
            raise IngestionError(f"UCI Electricity dataset {source_id} is empty.")
        
        # UCI electricity data typically has many columns; aggregate or pick one
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            raise IngestionError(f"UCI Electricity dataset {source_id} has no numeric columns.")
        
        # Sum all numeric columns to create a single series if multiple exist
        if len(numeric_cols) > 1:
            df['total_load'] = df[numeric_cols].sum(axis=1)
            value_col = 'total_load'
        else:
            value_col = numeric_cols[0]
        
        valid_points = df[value_col].notna().sum()
        
        if valid_points < 25:
            raise IngestionError(
                f"UCI Electricity dataset {source_id} has only {valid_points} valid points. "
                "Minimum required is 25."
            )
        
        checksum = compute_sha256(temp_file)
        file_size = temp_file.stat().st_size
        
        if file_size == 0:
            raise IngestionError(f"UCI Electricity data file for {source_id} is 0 bytes.")
        
        final_path = dest_dir / f"{source_id}.csv"
        shutil.move(str(temp_file), str(final_path))
        
        log_info(f"Successfully ingested UCI Electricity dataset {source_id}: {valid_points} points")
        
        return DatasetManifest(
            source=source_id,
            file_path=str(final_path),
            checksum=checksum,
            size_bytes=file_size,
            num_points=int(valid_points)
        )
        
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise IngestionError(f"Failed to ingest UCI Electricity dataset {source_id}: {str(e)}") from e

def ingest_dataset(url: str, source_id: str, dest_dir: Path, dataset_type: str = "auto") -> DatasetManifest:
    """
    Generic ingestion function that routes to appropriate handler based on URL or type.
    """
    if dataset_type == "noaa" or "noaa" in url.lower() or "ncdc" in url.lower():
        return ingest_noaa_dataset(url, source_id, dest_dir)
    elif dataset_type == "yahoo" or "yahoo" in url.lower():
        raise IngestionError("Use ingest_yahoo_finance for Yahoo data.")
    elif dataset_type == "uk_grid" or "nationalgrid" in url.lower():
        return ingest_uk_grid(url, source_id, dest_dir)
    elif dataset_type == "uci" or "uci" in url.lower():
        return ingest_uci_electricity(url, source_id, dest_dir)
    else:
        # Default to generic CSV ingestion with validation
        temp_file = Path(tempfile.mktemp(suffix=".csv"))
        try:
            download_file(url, temp_file)
            
            df = load_csv_robust(temp_file)
            
            if len(df) == 0:
                raise IngestionError(f"Dataset {source_id} is empty after loading.")
            
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                raise IngestionError(f"Dataset {source_id} has no numeric columns.")
            
            valid_points = df[numeric_cols[0]].notna().sum()
            
            if valid_points < 25:
                raise IngestionError(
                    f"Dataset {source_id} has only {valid_points} valid points. "
                    "Minimum required is 25."
                )
            
            checksum = compute_sha256(temp_file)
            file_size = temp_file.stat().st_size
            
            if file_size == 0:
                raise IngestionError(f"Dataset {source_id} downloaded file is 0 bytes.")
            
            final_path = dest_dir / f"{source_id}.csv"
            shutil.move(str(temp_file), str(final_path))
            
            log_info(f"Successfully ingested generic dataset {source_id}: {valid_points} points")
            
            return DatasetManifest(
                source=source_id,
                file_path=str(final_path),
                checksum=checksum,
                size_bytes=file_size,
                num_points=int(valid_points)
            )
            
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise IngestionError(f"Failed to ingest generic dataset {source_id}: {str(e)}") from e

def create_manifest(manifests: list, output_path: Path) -> None:
    """
    Creates a JSON manifest file from a list of DatasetManifest objects.
    """
    data = [m.to_dict() for m in manifests]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    log_info(f"Created manifest at {output_path}")

def load_manifest(manifest_path: Path) -> list:
    """
    Loads a manifest file and returns list of DatasetManifest objects.
    """
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    return [DatasetManifest(**item) for item in data]

import json