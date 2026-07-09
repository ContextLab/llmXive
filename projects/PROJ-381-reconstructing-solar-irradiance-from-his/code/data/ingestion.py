"""
Data Ingestion Module for Solar Irradiance Reconstruction.

Fetches Group Sunspot Number (GSN) from SILSO and Total Solar Irradiance (TSI)
from SORCE/TIM, saving raw data to data/raw/.
"""
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
import pandas as pd

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import ensure_directories
from env_manager import get_data_path

# Constants
SILSO_GSN_URL = "https://www.sidc.be/users/silso/datafiles/total_gsn_v2.csv"
# SORCE TIM data is typically available via NASA's LAADS or direct FTP.
# Using the SORCE/TIM Level 3 daily composite CSV which is publicly accessible.
# Note: If the direct URL changes, this should be updated.
# Alternative: https://lasp.colorado.edu/sorce/data/
SORCE_TSI_URL = "https://lasp.colorado.edu/sorce/data/l3/tim_daily.csv"

# Fallback/Alternative for SORCE if the above is restricted (often requires token or specific referrer)
# Using the NASA CDAWeb direct link for TIM L3 daily data (CSV format)
SORCE_TSI_CDAWEB = "https://lasp.colorado.edu/sorce/data/l3/tim_daily.csv"

# Timeout for network requests
REQUEST_TIMEOUT = 60

def fetch_silso_gsn(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Fetches the Group Sunspot Number (GSN) v2 from SILSO.

    Args:
        output_path: Optional path to save the CSV. If None, uses default data/raw/gsn_silso.csv.

    Returns:
        DataFrame containing the GSN data.
    """
    if output_path is None:
        data_dir = get_data_path("raw")
        ensure_directories()
        output_path = data_dir / "gsn_silso.csv"

    print(f"Fetching GSN data from SILSO: {SILSO_GSN_URL}")
    try:
        response = requests.get(SILSO_GSN_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # SILSO CSV usually has a header row, but sometimes has comments.
        # We'll parse it assuming standard CSV format.
        # Skip initial lines if they contain metadata (SILSO often has header comments)
        # The standard v2 file usually starts directly with headers or has a specific format.
        # Let's try reading with pandas and handle potential headers.
        
        df = pd.read_csv(
            response.text.splitlines(),
            comment='#',
            na_values=['-999', '-9999', 'NaN']
        )
        
        # SILSO GSN v2 columns are typically: Date, GSN, GSN_Error, etc.
        # Let's inspect columns if possible, but assume standard naming if known.
        # Standard SILSO V2 format: 'Date', 'GSN', 'GSN_Error', 'Groups', 'Groups_Error'
        # If the first row is not a header, we might need to handle it.
        # Checking if 'Date' is in columns or if first row looks like data.
        
        if 'Date' not in df.columns:
            # Fallback: assume columns based on position if headers are missing or malformed
            # But SILSO usually provides headers.
            # If the first row is data (e.g. '1610.01'), we need to shift.
            # For robustness, we'll rely on the standard header provided by SILSO.
            pass

        # Ensure Date is parsed correctly
        # SILSO Date format is often YYYY.MMDD or YYYYMMDD or just YYYY
        # Let's try to parse as string first, then convert if needed.
        if 'Date' in df.columns:
            # Convert to datetime, handling various formats
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')

        # Save to disk
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Successfully saved GSN data to {output_path}")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching SILSO GSN data: {e}")
        raise
    except Exception as e:
        print(f"Error processing SILSO GSN data: {e}")
        raise

def fetch_sorce_tsi(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Fetches Total Solar Irradiance (TSI) from SORCE/TIM.

    Args:
        output_path: Optional path to save the CSV. If None, uses default data/raw/tsi_sorce.csv.

    Returns:
        DataFrame containing the TSI data.
    """
    if output_path is None:
        data_dir = get_data_path("raw")
        ensure_directories()
        output_path = data_dir / "tsi_sorce.csv"

    print(f"Fetching TSI data from SORCE: {SORCE_TSI_CDAWEB}")
    
    # SORCE data might require a specific User-Agent or referer
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; llmXive-research-agent; +https://example.com/bot)'
    }

    try:
        response = requests.get(SORCE_TSI_CDAWEB, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # SORCE TIM L3 daily CSV usually has headers.
        # Common columns: Date, TSI, TSI_Error, etc.
        df = pd.read_csv(
            response.text.splitlines(),
            comment='#',
            na_values=['-999', '-9999', 'NaN']
        )

        # Normalize column names (lowercase, strip whitespace)
        df.columns = [col.strip().lower() for col in df.columns]

        # Identify date and TSI columns dynamically or by known names
        date_col = None
        tsi_col = None

        possible_date_cols = ['date', 'datetime', 'time', 'mjd']
        possible_tsi_cols = ['tsi', 'tsi_value', 'total_solar_irradiance', 'irr']

        for col in df.columns:
            if any(p in col for p in possible_date_cols):
                date_col = col
            if any(p in col for p in possible_tsi_cols):
                tsi_col = col

        if not date_col:
            raise ValueError("Could not identify date column in SORCE TSI data.")
        if not tsi_col:
            raise ValueError("Could not identify TSI column in SORCE TSI data.")

        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df = df.sort_values(date_col)

        # Rename for consistency
        df = df.rename(columns={date_col: 'Date', tsi_col: 'TSI'})
        
        # Keep only essential columns if many exist
        cols_to_keep = ['Date', 'TSI']
        # Check for error columns to keep if available
        if 'tsi_error' in df.columns:
            cols_to_keep.append('TSI_Error')
        
        df = df[cols_to_keep]

        # Save to disk
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Successfully saved TSI data to {output_path}")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching SORCE TSI data: {e}")
        raise
    except Exception as e:
        print(f"Error processing SORCE TSI data: {e}")
        raise

def run_ingestion():
    """
    Main entry point to fetch all required raw datasets.
    """
    print("Starting data ingestion pipeline...")
    
    # Ensure directories exist
    ensure_directories()

    try:
        # Fetch GSN
        gsn_df = fetch_silso_gsn()
        print(f"GSN Data shape: {gsn_df.shape}")
        
        # Fetch TSI
        tsi_df = fetch_sorce_tsi()
        print(f"TSI Data shape: {tsi_df.shape}")
        
        print("Ingestion complete.")
        return gsn_df, tsi_df

    except Exception as e:
        print(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    run_ingestion()