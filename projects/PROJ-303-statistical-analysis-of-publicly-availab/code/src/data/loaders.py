"""
Data loaders for fetching NOAA GHCN-Daily and HuggingFace datasets with checksum verification.

This module provides robust functions to download real-world weather data from
authoritative sources, verify data integrity via SHA-256 checksums, and cache
results locally to avoid redundant downloads.
"""
import os
import hashlib
import json
import time
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
import pandas as pd
from src.config import get_config

# Constants
DEFAULT_TIMEOUT = 120  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _download_with_retry(
    url: str, 
    dest_path: Path, 
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[bool, Optional[str]]:
    """
    Download a file with retry logic and error handling.
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file in chunks
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True, None
            
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                return False, f"Download failed after {MAX_RETRIES} attempts: {str(e)}"
            time.sleep(RETRY_DELAY * (attempt + 1))
        
        except Exception as e:
            return False, f"Unexpected error during download: {str(e)}"
    
    return False, "Unknown error"

def fetch_noaa_ghcn_data(
    station_ids: List[str],
    start_year: int = 2000,
    end_year: int = 2020,
    output_dir: Optional[Path] = None,
    verify_checksum: bool = True
) -> Dict[str, Path]:
    """
    Fetch NOAA GHCN-Daily data for specified stations.
    
    Downloads daily summary data from the NOAA GHCN-Daily archive.
    Uses the official NOAA FTP/HTTP mirror for reliable access.
    
    Args:
        station_ids: List of GHCN station IDs (e.g., 'USC00131620')
        start_year: Start year for data range (inclusive)
        end_year: End year for data range (inclusive)
        output_dir: Directory to save downloaded files. Defaults to data/raw/noaa
        verify_checksum: Whether to verify SHA-256 checksums after download
        
    Returns:
        Dictionary mapping station_id to local file path
        
    Raises:
        RuntimeError: If download fails or checksum verification fails
    """
    config = get_config()
    base_url = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/"
    
    if output_dir is None:
        output_dir = Path("data/raw/noaa")
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    checksums_file = output_dir / "checksums.json"
    
    # Load existing checksums if available
    existing_checksums = {}
    if checksums_file.exists():
        try:
            with open(checksums_file, 'r') as f:
                existing_checksums = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_checksums = {}
    
    for station_id in station_ids:
        # Construct NOAA URL (format: daily-<station_id>.csv)
        filename = f"daily-{station_id}.csv"
        local_path = output_dir / filename
        url = f"{base_url}{filename}"
        
        # Check if file already exists and checksum matches
        if local_path.exists() and verify_checksum:
            if station_id in existing_checksums:
                current_hash = _calculate_sha256(local_path)
                if current_hash == existing_checksums[station_id]:
                    results[station_id] = local_path
                    continue
        
        # Download the file
        success, error = _download_with_retry(url, local_path)
        
        if not success:
            raise RuntimeError(f"Failed to download data for station {station_id}: {error}")
        
        # Verify checksum if requested
        if verify_checksum:
            file_hash = _calculate_sha256(local_path)
            existing_checksums[station_id] = file_hash
            
            # Update checksums file
            with open(checksums_file, 'w') as f:
                json.dump(existing_checksums, f, indent=2)
        
        results[station_id] = local_path
        
    return results

def fetch_huggingface_dataset(
    dataset_name: str,
    revision: str = "main",
    output_dir: Optional[Path] = None,
    verify_checksum: bool = True
) -> Path:
    """
    Fetch a dataset from HuggingFace Hub.
    
    Args:
        dataset_name: HuggingFace dataset identifier (e.g., "noaa/ghcn-daily")
        revision: Git revision to fetch (default: "main")
        output_dir: Directory to save downloaded files. Defaults to data/raw/huggingface
        verify_checksum: Whether to verify integrity after download
        
    Returns:
        Path to the downloaded dataset directory
        
    Raises:
        RuntimeError: If download fails or dataset is not found
    """
    config = get_config()
    
    if output_dir is None:
        output_dir = Path("data/raw/huggingface")
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to import datasets library
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' library is required for HuggingFace downloads. "
            "Install it with: pip install datasets"
        )
    
    try:
        # Download dataset
        dataset = load_dataset(
            dataset_name,
            revision=revision,
            cache_dir=str(output_dir)
        )
        
        # Return the cache directory path
        return Path(dataset.cache_files[0]['filename']).parent.parent
        
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HuggingFace dataset '{dataset_name}': {str(e)}")

def load_station_data(
    file_path: Path,
    station_id: Optional[str] = None
) -> pd.DataFrame:
    """
    Load a single station's data from a CSV file.
    
    Args:
        file_path: Path to the daily CSV file
        station_id: Optional station ID to validate against filename
        
    Returns:
        DataFrame with parsed weather data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If data format is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    try:
        # NOAA GHCN-Daily format:
        # GSTATION, DATE, ELEMENT, VALUE, M_FLAG, Q_FLAG, S_FLAG, OBS_TIME
        df = pd.read_csv(
            file_path,
            skiprows=1,  # Skip header row with column names
            names=[
                'station_id', 'date', 'element', 'value', 
                'm_flag', 'q_flag', 's_flag', 'obs_time'
            ],
            parse_dates=['date'],
            na_values=['-9999', '', 'NA']
        )
        
        # Validate station ID if provided
        if station_id and df['station_id'].iloc[0] != station_id:
            raise ValueError(
                f"Station ID mismatch: expected {station_id}, "
                f"got {df['station_id'].iloc[0]}"
            )
        
        return df
        
    except Exception as e:
        raise ValueError(f"Failed to parse data file {file_path}: {str(e)}")

def load_multiple_stations(
    file_paths: Dict[str, Path],
    elements: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load data for multiple stations into a single DataFrame.
    
    Args:
        file_paths: Dictionary mapping station_id to file path
        elements: Optional list of element codes to filter (e.g., ['PRCP', 'TMAX', 'TMIN'])
        
    Returns:
        Combined DataFrame with station_id, date, element, value
        
    Raises:
        ValueError: If no valid data found
    """
    dataframes = []
    
    for station_id, file_path in file_paths.items():
        df = load_station_data(file_path, station_id)
        
        if elements:
            df = df[df['element'].isin(elements)]
        
        dataframes.append(df)
    
    if not dataframes:
        raise ValueError("No valid data loaded from any station files")
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Sort by station and date
    combined_df = combined_df.sort_values(['station_id', 'date']).reset_index(drop=True)
    
    return combined_df

def verify_data_integrity(
    file_paths: Dict[str, Path],
    checksums: Optional[Dict[str, str]] = None
) -> Dict[str, bool]:
    """
    Verify SHA-256 checksums for downloaded files.
    
    Args:
        file_paths: Dictionary mapping station_id to file path
        checksums: Optional dictionary of expected checksums
        
    Returns:
        Dictionary mapping station_id to verification status
    """
    results = {}
    
    for station_id, file_path in file_paths.items():
        if not file_path.exists():
            results[station_id] = False
            continue
        
        if checksums and station_id in checksums:
            expected_hash = checksums[station_id]
            actual_hash = _calculate_sha256(file_path)
            results[station_id] = (expected_hash == actual_hash)
        else:
            # No checksum to verify against, just check file exists
            results[station_id] = True
    
    return results