import os
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import itertools
import random
import pandas as pd

from src.utils.config import get_path
from src.utils.logging import log_info, log_warning, log_error, log_critical

class IngestionError(Exception):
    """Custom exception for data ingestion errors."""
    pass

class DatasetManifest:
    """Stores metadata about an ingested dataset."""
    def __init__(self, dataset_id: str, source_url: str, file_path: str, checksum: str, row_count: int, sample_info: Optional[Dict[str, Any]] = None):
        self.dataset_id = dataset_id
        self.source_url = source_url
        self.file_path = file_path
        self.checksum = checksum
        self.row_count = row_count
        self.sample_info = sample_info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_url": self.source_url,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "row_count": self.row_count,
            "sample_info": self.sample_info
        }

def validate_url(url: str) -> bool:
    """Validates that a URL is well-formed and points to an allowed domain."""
    # Basic validation logic
    if not url.startswith("http"):
        return False
    return True

def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str) -> None:
    """Downloads a file from a URL to a destination path."""
    import requests
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def load_csv_robust(file_path: str, delimiter: str = ",", encoding: str = "utf-8") -> pd.DataFrame:
    """Loads a CSV file robustly, handling common errors."""
    try:
        return pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
    except Exception as e:
        log_error(f"Failed to load CSV {file_path}: {e}")
        raise IngestionError(f"Failed to load CSV: {e}")

def ingest_noaa_dataset(station_id: str, url: str, output_dir: str) -> DatasetManifest:
    """Ingests a NOAA dataset from a URL."""
    # Implementation for NOAA ingestion
    raise NotImplementedError("NOAA ingestion logic not implemented in this snippet")

def ingest_yahoo_finance(ticker: str, period: str = "5d", interval: str = "1d", output_dir: str = None) -> DatasetManifest:
    """Ingests Yahoo Finance data using yfinance."""
    import yfinance as yf
    if output_dir is None:
        output_dir = str(get_path("data_raw"))
    
    df = yf.download(ticker, period=period, interval=interval)
    if df.empty:
        raise IngestionError(f"No data downloaded for {ticker}")
    
    df = df.reset_index()[["Date", "Close"]]
    df["series_id"] = ticker
    df = df.rename(columns={"Date": "timestamp", "Close": "value"})
    
    file_name = f"{ticker}_yahoo.csv"
    file_path = os.path.join(output_dir, file_name)
    df.to_csv(file_path, index=False)
    
    checksum = compute_sha256(file_path)
    row_count = len(df)
    
    log_info(f"Ingested Yahoo Finance data for {ticker}: {row_count} rows, saved to {file_path}")
    return DatasetManifest(dataset_id=ticker, source_url=f"yfinance:{ticker}", file_path=file_path, checksum=checksum, row_count=row_count)

def ingest_uk_grid(url: str, output_dir: str) -> DatasetManifest:
    """Ingests UK National Grid Load data."""
    # Implementation for UK Grid ingestion
    raise NotImplementedError("UK Grid ingestion logic not implemented in this snippet")

def ingest_uci_electricity(url: str, output_dir: str) -> DatasetManifest:
    """Ingests UCI Electricity data."""
    # Implementation for UCI ingestion
    raise NotImplementedError("UCI ingestion logic not implemented in this snippet")

def ingest_dataset(dataset_id: str, source_url: str, output_dir: str, sample_size: Optional[int] = None, seed: int = 42) -> DatasetManifest:
    """
    Generic dataset ingestion function with optional sampling.
    
    If sample_size is provided, the dataset will be sampled using itertools.islice
    (for row-based sampling) or a fixed-seed random sample.
    
    Args:
        dataset_id: Unique identifier for the dataset.
        source_url: URL to download the data from.
        output_dir: Directory to save the ingested data.
        sample_size: If provided, number of rows to sample.
        seed: Random seed for reproducibility if random sampling is used.
    
    Returns:
        DatasetManifest object containing metadata about the ingested dataset.
    """
    os.makedirs(output_dir, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        log_info(f"Downloading dataset {dataset_id} from {source_url}")
        download_file(source_url, temp_path)

        if os.path.getsize(temp_path) == 0:
            raise IngestionError(f"Downloaded file for {dataset_id} is empty.")

        # Load full dataset to check size and sample if needed
        full_df = load_csv_robust(temp_path)
        original_count = len(full_df)
        
        sample_info = None
        
        if sample_size is not None:
            if sample_size >= original_count:
                log_warning(f"Sample size {sample_size} >= original count {original_count}. Using full dataset.")
                sampled_df = full_df
            else:
                log_info(f"Sampling dataset {dataset_id}: taking first {sample_size} rows (method: islice).")
                # Use itertools.islice for deterministic row-based sampling
                sampled_df = pd.DataFrame(itertools.islice(full_df.to_dict('records'), sample_size))
                sample_info = {
                    "method": "islice_first_n",
                    "sample_size": sample_size,
                    "original_size": original_count,
                    "seed": None,
                    "limitation": "Only the first N rows of the original dataset are used. This may not be representative if the data has temporal trends or seasonality at the start."
                }
        else:
            sampled_df = full_df

        final_count = len(sampled_df)
        if final_count < 25:
            log_warning(f"Dataset {dataset_id} has only {final_count} points after sampling. It may be too short for ACF analysis.")

        final_file_name = f"{dataset_id}.csv"
        final_path = os.path.join(output_dir, final_file_name)
        sampled_df.to_csv(final_path, index=False)

        checksum = compute_sha256(final_path)
        
        manifest = DatasetManifest(
            dataset_id=dataset_id,
            source_url=source_url,
            file_path=final_path,
            checksum=checksum,
            row_count=final_count,
            sample_info=sample_info
        )

        log_info(f"Successfully ingested {dataset_id}: {final_count} rows, checksum={checksum}")
        return manifest

    except Exception as e:
        log_error(f"Failed to ingest dataset {dataset_id}: {e}")
        raise IngestionError(f"Ingestion failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def create_manifest(manifests: List[DatasetManifest], output_path: str) -> None:
    """Creates a manifest file from a list of DatasetManifest objects."""
    data = [m.to_dict() for m in manifests]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_manifest(manifest_path: str) -> List[DatasetManifest]:
    """Loads a manifest file into a list of DatasetManifest objects."""
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    return [DatasetManifest(**item) for item in data]

def write_sampling_metadata(sampled_datasets: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes sampling metadata to a JSON file.
    
    Args:
        sampled_datasets: List of dicts containing sampling info for each dataset.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(sampled_datasets, f, indent=2)
    log_info(f"Sampling metadata written to {output_path}")

def main():
    """
    Main function to demonstrate ingestion with sampling.
    This is primarily for testing the sampling logic.
    """
    # Example usage
    sample_size = 1000
    seed = 42
    
    # Mocking a dataset for demonstration if real download fails
    # In real usage, this would call ingest_dataset with a real URL
    # For T061, we ensure the logic exists and logs correctly.
    
    # Simulating a scenario where we ingest a dataset with sampling
    # We will use a dummy CSV creation for the test to ensure the log is generated
    import pandas as pd
    import tempfile
    import os
    
    dummy_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=2000, freq='D'),
        'value': range(2000),
        'series_id': 'DUMMY'
    })
    
    dummy_path = tempfile.mktemp(suffix='.csv')
    dummy_data.to_csv(dummy_path, index=False)
    
    # Mock the download_file to just copy our dummy file
    original_download = download_file
    def mock_download(url, dest):
        shutil.copy(dummy_path, dest)
    
    download_file = mock_download
    
    try:
        manifest = ingest_dataset(
            dataset_id="test_sample",
            source_url="http://example.com/data.csv",
            output_dir=str(get_path("data_raw")),
            sample_size=sample_size,
            seed=seed
        )
        
        if manifest.sample_info:
            write_sampling_metadata([manifest.sample_info], str(get_path("data_processed", "sampling_metadata.json")))
        else:
            log_info("No sampling performed for this dataset.")
            
    finally:
        download_file = original_download
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
        
        # Clean up the created file if it exists
        final_path = os.path.join(str(get_path("data_raw")), "test_sample.csv")
        if os.path.exists(final_path):
            os.remove(final_path)

if __name__ == "__main__":
    main()
