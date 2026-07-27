import os
import logging
import hashlib
import urllib.request
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

from logger import get_logger

logger = get_logger(__name__)

# Configuration for data sources
GSS_URL = "https://gss.norc.org/files/stata/2022/2022_Stata.zip"
GSS_FILENAME = "GSS2022.dta"
GSS_CHECKSUM = None  # Placeholder; in production, verify with actual checksum

CYBER_URL = "https://raw.githubusercontent.com/example/cyberbullying-survey/main/data/cyberbullying_2021.csv"
CYBER_FILENAME = "cyberbullying_2021.csv"

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def validate_raw_data_file(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """Validate the integrity of a raw data file."""
    if not file_path.exists():
        return False
    
    if expected_checksum:
        actual_checksum = calculate_md5(file_path)
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
            return False
    return True

def download_dataset(url: str, filename: str, dest_dir: Path) -> Path:
    """Download a dataset from a URL."""
    ensure_dirs()
    dest_path = dest_dir / filename
    
    if dest_path.exists():
        logger.info(f"File {filename} already exists at {dest_path}. Skipping download.")
        return dest_path

    logger.info(f"Downloading {filename} from {url}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Downloaded {filename} successfully.")
        return dest_path
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")
        raise

def load_gss_data() -> Optional[pd.DataFrame]:
    """
    Load GSS 2022 data.
    Attempts to download if not present, then loads the Stata file.
    """
    try:
        # Attempt to download
        # Note: In a real environment, this URL might require authentication or specific headers.
        # We assume public access for this implementation.
        gss_zip_path = RAW_DIR / "2022_Stata.zip"
        if not gss_zip_path.exists():
            download_dataset(GSS_URL, "2022_Stata.zip", RAW_DIR)
        
        # Extract if needed
        gss_dta_path = RAW_DIR / GSS_FILENAME
        if not gss_dta_path.exists():
            with zipfile.ZipFile(gss_zip_path, 'r') as zip_ref:
                # Assuming the zip contains the dta file directly or in a subfolder
                # We try to find the .dta file
                dta_files = [f for f in zip_ref.namelist() if f.endswith('.dta')]
                if dta_files:
                    with zip_ref.open(dta_files[0]) as source, open(gss_dta_path, 'wb') as target:
                        target.write(source.read())
                else:
                    raise FileNotFoundError("No .dta file found in the archive.")

        # Load using pandas
        df = pd.read_stata(gss_dta_path)
        logger.info(f"GSS 2022 loaded with shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error loading GSS 2022: {e}")
        return None

def load_cyber_data() -> Optional[pd.DataFrame]:
    """
    Load Cyberbullying Survey 2021 data.
    """
    try:
        cyber_path = RAW_DIR / CYBER_FILENAME
        if not cyber_path.exists():
            download_dataset(CYBER_URL, CYBER_FILENAME, RAW_DIR)
        
        df = pd.read_csv(cyber_path)
        logger.info(f"Cyberbullying Survey 2021 loaded with shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error loading Cyberbullying Survey 2021: {e}")
        return None

def harmonize_datasets(gss_df: Optional[pd.DataFrame], cyber_df: Optional[pd.DataFrame]) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Harmonize variable names and types between GSS and Cyberbullying datasets.
    Returns the processed DataFrames.
    """
    # Placeholder for harmonization logic
    # In a real scenario, this would map column names to a common schema
    if gss_df is not None:
        # Example: standardize column names
        gss_df.columns = gss_df.columns.str.lower().str.replace(" ", "_")
    
    if cyber_df is not None:
        cyber_df.columns = cyber_df.columns.str.lower().str.replace(" ", "_")

    return gss_df, cyber_df

def get_data_summary(df: pd.DataFrame, name: str) -> str:
    """Generate a summary string for a dataset."""
    if df is None:
        return f"{name}: None"
    return f"{name}: {df.shape}, columns: {list(df.columns[:5])}..."

def validate_schema_presence(df: pd.DataFrame, required_cols: List[str], dataset_name: str) -> bool:
    """Check if required columns are present in the DataFrame."""
    if df is None:
        return False
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.warning(f"Missing columns in {dataset_name}: {missing}")
        return False
    return True

def run_ingestion_checks() -> Dict[str, Any]:
    """
    Run ingestion checks for both datasets.
    This is a preliminary check before T018 validation.
    """
    ensure_dirs()
    
    gss_df = load_gss_data()
    cyber_df = load_cyber_data()
    
    gss_df, cyber_df = harmonize_datasets(gss_df, cyber_df)
    
    return {
        'gss': gss_df,
        'cyber': cyber_df,
        'gss_summary': get_data_summary(gss_df, "GSS"),
        'cyber_summary': get_data_summary(cyber_df, "Cyber")
    }

def main():
    """Main entry point for ingestion."""
    logger.info("Starting data ingestion...")
    results = run_ingestion_checks()
    logger.info(f"Ingestion results: {results['gss_summary']}, {results['cyber_summary']}")
    return results

if __name__ == "__main__":
    main()
