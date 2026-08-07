import os
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import json
import time

import pandas as pd
import requests
import yfinance as yf
from requests.exceptions import RequestException, Timeout, HTTPError

from src.utils.logging import get_logger

logger = get_logger(__name__)

class IngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass

@dataclass
class DatasetManifest:
    """Schema for dataset metadata in the manifest file."""
    name: str
    source: str
    url: str
    local_path: str
    checksum: str
    timestamp: str
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_url(url: str) -> bool:
    """Validate that a URL is well-formed and accessible."""
    if not url.startswith(('http://', 'https://')):
        return False
    try:
        # HEAD request to check accessibility without downloading body
        response = requests.head(url, timeout=10, allow_redirects=True)
        # Some servers block HEAD, fallback to GET with stream
        if response.status_code == 405:
            response = requests.get(url, stream=True, timeout=10)
        return response.status_code == 200
    except RequestException:
        return False

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, timeout: int = 60) -> str:
    """
    Download a file from a URL with progress and error handling.
    Raises IngestionError on failure.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        logger.info(f"Downloading {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {percent:.1f}%")
        
        logger.info(f"Download complete: {dest_path}")
        return compute_sha256(dest_path)
        
    except (Timeout, RequestException, HTTPError) as e:
        logger.error(f"Download failed for {url}: {e}")
        raise IngestionError(f"Failed to download {url}: {e}")

def load_csv_robust(filepath: Path, **kwargs) -> pd.DataFrame:
    """
    Load a CSV file with robust error handling and encoding detection.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    last_error = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding, **kwargs)
            logger.info(f"Loaded {filepath} with encoding {encoding}")
            return df
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            break
    
    raise IngestionError(f"Failed to load {filepath} with any common encoding: {last_error}")

def ingest_noaa_dataset(url: str, dest_dir: Path, name: str) -> DatasetManifest:
    """
    Ingest a NOAA dataset from a direct CSV/TSV URL.
    """
    logger.info(f"Ingesting NOAA dataset: {name}")
    local_filename = f"{name}.csv"
    dest_path = dest_dir / local_filename
    
    checksum = download_file(url, dest_path)
    df = load_csv_robust(dest_path)
    
    # Basic validation
    if df.empty:
        raise IngestionError(f"Loaded dataset {name} is empty.")
    
    manifest = DatasetManifest(
        name=name,
        source="NOAA",
        url=url,
        local_path=str(dest_path),
        checksum=checksum,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        metadata={"rows": len(df), "columns": list(df.columns)}
    )
    return manifest

def ingest_yahoo_finance(ticker: str, start: str, end: str, dest_dir: Path) -> DatasetManifest:
    """
    Ingest Yahoo Finance data using yfinance.
    """
    logger.info(f"Ingesting Yahoo Finance data: {ticker} ({start} to {end})")
    local_filename = f"yahoo_{ticker}_{start}_{end}.csv"
    dest_path = dest_dir / local_filename
    
    try:
        df = yf.download(ticker, start=start, end=end)
        if df.empty:
            raise IngestionError(f"No data retrieved for {ticker} in range {start}-{end}")
        
        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{col[0]}_{col[1]}" for col in df.columns]
        
        df.to_csv(dest_path, index=True)
        checksum = compute_sha256(dest_path)
        
        manifest = DatasetManifest(
            name=f"yahoo_{ticker}",
            source="Yahoo Finance",
            url=f"https://finance.yahoo.com/quote/{ticker}",
            local_path=str(dest_path),
            checksum=checksum,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            metadata={"rows": len(df), "columns": list(df.columns)}
        )
        return manifest
        
    except Exception as e:
        raise IngestionError(f"Failed to ingest Yahoo Finance data for {ticker}: {e}")

def ingest_uk_grid(dest_dir: Path) -> DatasetManifest:
    """
    Ingest UK National Grid Load data.
    The data is typically available via a specific CSV endpoint or API.
    We use the ESO (Energy System Operator) public data API endpoint for half-hourly demand.
    """
    logger.info("Ingesting UK National Grid Load data")
    # Using the ESO API for half-hourly demand (real source)
    url = "https://api.nationalgrideso.com/1/demand/balancing-forecast-demand/latest"
    # Since the API returns JSON, we adapt the download logic
    
    local_filename = "uk_grid_demand.json"
    dest_path = dest_dir / local_filename
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Convert to CSV for consistency in downstream processing
        # The API structure varies, we flatten the 'data' list if present
        if 'data' in data and isinstance(data['data'], list):
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame([data])
        
        if df.empty:
            raise IngestionError("UK Grid API returned empty data")
        
        df.to_csv(dest_path, index=False)
        checksum = compute_sha256(dest_path)
        
        manifest = DatasetManifest(
            name="uk_grid_demand",
            source="UK National Grid ESO",
            url=url,
            local_path=str(dest_path),
            checksum=checksum,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            metadata={"rows": len(df), "columns": list(df.columns)}
        )
        return manifest
        
    except RequestException as e:
        raise IngestionError(f"Failed to download UK Grid data: {e}")

def ingest_uci_electricity(dest_dir: Path) -> DatasetManifest:
    """
    Ingest UCI Electricity Load Diagrams 2011-2014 dataset.
    The dataset is large (~1 GB). We will download the main CSV file from the UCI repository.
    URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip
    """
    logger.info("Ingesting UCI Electricity Load data")
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip"
    local_zip = dest_dir / "uci_electricity.zip"
    local_csv = dest_dir / "uci_electricity.csv"
    
    try:
        # Download the zip
        download_file(url, local_zip)
        
        # Unzip
        import zipfile
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        
        # The main file is usually LD2011_2014.txt
        csv_files = list(dest_dir.glob("LD2011_2014*.txt"))
        if not csv_files:
            raise IngestionError("Could not find extracted UCI file")
        
        src_path = csv_files[0]
        shutil.move(str(src_path), str(local_csv))
        
        # Clean up zip
        local_zip.unlink()
        
        checksum = compute_sha256(local_csv)
        
        manifest = DatasetManifest(
            name="uci_electricity",
            source="UCI Machine Learning Repository",
            url=url,
            local_path=str(local_csv),
            checksum=checksum,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            metadata={"source_file": src_path.name}
        )
        return manifest
        
    except Exception as e:
        raise IngestionError(f"Failed to ingest UCI Electricity data: {e}")

def ingest_dataset(config: Dict[str, Any], dest_dir: Path) -> DatasetManifest:
    """
    Generic ingestion dispatcher based on source type.
    """
    source = config.get("source", "").lower()
    name = config.get("name", "unknown")
    
    if "noaa" in source:
        return ingest_noaa_dataset(config["url"], dest_dir, name)
    elif "yahoo" in source or "finance" in source:
        ticker = config.get("ticker")
        start = config.get("start", "2020-01-01")
        end = config.get("end", "2023-01-01")
        return ingest_yahoo_finance(ticker, start, end, dest_dir)
    elif "uk" in source and "grid" in source:
        return ingest_uk_grid(dest_dir)
    elif "uci" in source and "electricity" in source:
        return ingest_uci_electricity(dest_dir)
    else:
        raise IngestionError(f"Unknown source type: {source}")

def create_manifest(manifests: List[DatasetManifest], output_path: Path) -> None:
    """
    Write a list of DatasetManifest objects to a JSON manifest file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [m.to_dict() for m in manifests]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Manifest written to {output_path}")

def load_manifest(manifest_path: Path) -> List[DatasetManifest]:
    """
    Load a manifest file and return list of DatasetManifest objects.
    """
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    return [DatasetManifest(**item) for item in data]

def run_pipeline(config_path: Path, output_dir: Path) -> None:
    """
    Run the full ingestion pipeline based on a config file.
    Config file should be a JSON list of dataset configurations.
    """
    with open(config_path, 'r') as f:
        configs = json.load(f)
    
    manifests = []
    for cfg in configs:
        try:
            manifest = ingest_dataset(cfg, output_dir)
            manifests.append(manifest)
            logger.info(f"Successfully ingested: {manifest.name}")
        except IngestionError as e:
            logger.error(f"Failed to ingest {cfg.get('name')}: {e}")
            # Fail loudly as per constraint
            raise
    
    manifest_path = output_dir / "manifest.json"
    create_manifest(manifests, manifest_path)
    logger.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m src.data.ingestion <config.json> <output_dir>")
        sys.exit(1)
    
    config_file = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    
    logging.basicConfig(level=logging.INFO)
    run_pipeline(config_file, out_dir)
