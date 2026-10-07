"""
Module: src/data/download.py
Purpose: Fetch VAERS 2020-2023 CSVs from the verified CDC source.
Requirements:
  - Uses `requests` with explicit error handling.
  - NO synthetic fallbacks.
  - Post-download validation: verifies required columns (VAX_TYPE, SOC_CODE/LLT, REPT_DATE).
  - Exits with E_SCHEMA_MISSING if validation fails.
"""
import os
import sys
import hashlib
import zipfile
import logging
from pathlib import Path
from typing import Dict, Optional, List

import requests
import pandas as pd

# Constants
BASE_URL = "https://vaers.hhs.gov/data/datasets"
YEARS = ["2020", "2021", "2022", "2023"]
REQUIRED_COLUMNS = {"VAX_TYPE", "REPT_DATE"}
# SOC_CODE is often derived or present as LLT in raw data, but spec requires checking for SOC_CODE or LLT
# The raw VAERS data usually has LLT. We check for LLT as the proxy for SOC mapping input.
REQUIRED_COLUMNS_FOR_MAPPING = {"LLT"}

# Error codes
E_SCHEMA_MISSING = 1
E_DOWNLOAD_FAILED = 2
E_NETWORK_ERROR = 3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/download.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from URL to dest_path.
    Raises Exception on failure.
    """
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        # Log progress occasionally to avoid spam
                        if downloaded % (1024 * 1024 * 10) == 0: 
                            logger.info(f"Progress: {progress:.1f}%")
        
        logger.info(f"Download complete: {dest_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error downloading {url}: {e}")
        raise E_NETWORK_ERROR from e
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise E_DOWNLOAD_FAILED from e

def extract_csv_from_zip(zip_path: Path, extract_to: Path) -> Path:
    """
    Extract CSV from a zip file.
    Returns the path to the extracted CSV.
    """
    logger.info(f"Extracting {zip_path} to {extract_to}")
    csv_file = None
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the CSV file inside
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                raise ValueError(f"No CSV file found in {zip_path}")
            
            # VAERS datasets usually have one main CSV per year
            target_csv = csv_files[0]
            zip_ref.extract(target_csv, extract_to)
            csv_file = extract_to / target_csv
            logger.info(f"Extracted {target_csv}")
    except zipfile.BadZipFile as e:
        logger.error(f"Corrupted zip file {zip_path}: {e}")
        raise E_DOWNLOAD_FAILED from e
    except Exception as e:
        logger.error(f"Failed to extract {zip_path}: {e}")
        raise E_DOWNLOAD_FAILED from e
    
    # Clean up zip
    if zip_path.exists():
        zip_path.unlink()
        logger.info(f"Removed temporary zip file: {zip_path}")
    
    return csv_file

def validate_schema(file_path: Path) -> bool:
    """
    Validate that the downloaded CSV contains required columns.
    Required: VAX_TYPE, REPT_DATE, and (SOC_CODE or LLT).
    Returns True if valid, raises exception if invalid.
    """
    logger.info(f"Validating schema for {file_path}")
    try:
        # Read only the header to check columns
        df = pd.read_csv(file_path, nrows=0)
        columns = set(df.columns)
        
        missing_required = REQUIRED_COLUMNS - columns
        if missing_required:
            logger.error(f"Missing required columns: {missing_required}")
            return False
        
        # Check for mapping column (SOC_CODE or LLT)
        # VAERS raw data typically has LLT for MedDRA Low Level Term
        has_mapping = bool(REQUIRED_COLUMNS_FOR_MAPPING & columns)
        if not has_mapping:
            logger.error(f"Missing mapping column (expected {REQUIRED_COLUMNS_FOR_MAPPING}, found {columns})")
            return False
        
        logger.info(f"Schema validation passed for {file_path}. Columns: {list(columns)[:10]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to validate schema for {file_path}: {e}")
        return False

def fetch_vaers_data(output_dir: Path) -> List[Path]:
    """
    Fetch VAERS data for years 2020-2023.
    Returns a list of paths to the extracted CSV files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    
    for year in YEARS:
        # Construct URL for VAERS data
        # The standard pattern is: https://vaers.hhs.gov/data/datasets/VAERS_{YEAR}_DATA.zip
        filename = f"VAERS_{year}_DATA.zip"
        url = f"{BASE_URL}/{filename}"
        zip_path = output_dir / filename
        extracted_csv_path = output_dir / f"vaers_{year}.csv"
        
        # Skip if already exists (optional, but good practice)
        if extracted_csv_path.exists():
            logger.info(f"File {extracted_csv_path} already exists. Skipping download.")
            downloaded_files.append(extracted_csv_path)
            continue
        
        try:
            # Download
            download_file(url, zip_path)
            
            # Extract
            csv_path = extract_csv_from_zip(zip_path, output_dir)
            
            # Validate
            if not validate_schema(csv_path):
                logger.critical(f"Schema validation failed for {year}. Exiting.")
                sys.exit(E_SCHEMA_MISSING)
            
            # Rename to standard name if needed (extract_csv_from_zip returns the extracted path)
            # The extraction might keep the original name, so we ensure consistency
            if csv_path.name != f"vaers_{year}.csv":
                csv_path.rename(output_dir / f"vaers_{year}.csv")
                downloaded_files.append(output_dir / f"vaers_{year}.csv")
            else:
                downloaded_files.append(csv_path)
                
        except Exception as e:
            logger.error(f"Failed to process year {year}: {e}")
            # Fail loudly as per requirements
            if isinstance(e, int):
                sys.exit(e)
            raise e
    
    return downloaded_files

def main():
    """Main entry point for the download script."""
    logger.info("Starting VAERS data download for 2020-2023")
    
    # Define output directory based on project structure
    # Assuming this runs from project root or code/
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "raw"
    
    try:
        files = fetch_vaers_data(data_dir)
        logger.info(f"Successfully downloaded and validated {len(files)} files.")
        for f in files:
            logger.info(f"  - {f.name} ({f.stat().st_size / (1024*1024):.1f} MB)")
    except Exception as e:
        logger.error(f"Critical error in download process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
