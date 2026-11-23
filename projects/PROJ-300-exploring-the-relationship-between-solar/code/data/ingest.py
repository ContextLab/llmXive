"""
Data ingestion module for fetching solar wind and THEMIS data.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py
"""
import requests
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

# NASA OMNIWeb API base URL (Example endpoint structure)
# Note: In a real environment, proper authentication or specific endpoint parameters might be needed.
OMNI_API_URL = "https://omniweb.gsfc.nasa.gov/cgi-bin/omni_text.cgi"
CDAWEB_URL_TEMPLATE = "https://cdaweb.gsfc.nasa.gov/pub/data/themis/tha/l2/epd/epd_eft_ssn/{year}/"

def fetch_omni_sw(date_range: Tuple[datetime, datetime]) -> pd.DataFrame:
    """
    Fetch solar wind data (Vsw, Bz) from NASA OMNIWeb API.
    
    Args:
        date_range: Tuple of (start_datetime, end_datetime)
        
    Returns:
        pd.DataFrame with columns [timestamp, Vsw, Bz]
        
    Raises:
        RuntimeError: If real data cannot be fetched.
    """
    start_dt, end_dt = date_range
    logger.info(f"Fetching OMNI data from {start_dt} to {end_dt}")
    
    # Construct parameters for OMNIWeb (simplified for demonstration)
    # In reality, this requires specific query parameters or file download logic
    # We simulate a direct fetch attempt that MUST succeed or fail loudly
    
    # Attempt to fetch from a known public dataset mirror or API if available
    # Since direct OMNIWeb scraping is complex, we use a verified public CSV source if possible
    # or raise an error if no real source is available.
    
    # For this implementation, we assume a direct API call structure that fails if network is down
    # or data is missing.
    
    # NOTE: Real OMNIWeb access often requires a specific form submission or file download.
    # We will attempt to fetch a pre-formatted text file from a public archive if possible,
    # otherwise raise an error.
    
    # Using a public mirror for demonstration if direct API is restricted
    # This URL is an example; in production, use the official NASA API endpoint
    base_url = "https://omniweb.gsfc.nasa.gov/api/omni_data"
    # Fallback to a known public CSV if API is blocked (still real data)
    # Example: https://omniweb.gsfc.nasa.gov/form/omni_min.html -> download link
    
    # Since we cannot guarantee API access without auth tokens in this environment,
    # we will attempt a request to a public endpoint. If it fails, we raise.
    
    params = {
        'start': start_dt.strftime('%Y%m%d'),
        'end': end_dt.strftime('%Y%m%d'),
        'resolution': '1min' # or 5min
    }
    
    # Attempt 1: Try official API (might fail without auth)
    # Attempt 2: Try public CSV mirror (more reliable for scripts)
    
    # We will use a robust fetcher that tries a known public CSV source
    # Source: NASA OMNI 1-min data (publicly available via FTP/HTTP)
    # Example path: https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni1_min_2023.csv
    
    year = start_dt.year
    # Construct a likely public URL for the specific year
    csv_url = f"https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni1_min_{year}.csv"
    
    try:
        # Try to fetch the yearly CSV
        logger.info(f"Attempting to fetch from {csv_url}")
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV
        # The OMNI low-res CSV format: Date, Time, Vsw, Bz, ...
        # We need to handle the specific format
        df = pd.read_csv(pd.io.common.StringIO(response.text), skiprows=1) # Skip header if needed
        
        # Standardize column names based on typical OMNI format
        # Assuming columns: Date, Time, VSW (km/s), BZ (nT)
        # Adjust parsing based on actual header of the fetched file
        if 'VSW' in df.columns and 'BZ' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            result_df = df[['timestamp', 'VSW', 'BZ']].copy()
            result_df.columns = ['timestamp', 'Vsw', 'Bz']
            result_df = result_df[(result_df['timestamp'] >= start_dt) & (result_df['timestamp'] <= end_dt)]
            return result_df
        else:
            # Fallback parsing if headers differ
            logger.warning("Unexpected column headers in OMNI data, attempting generic parse.")
            # ... (parsing logic)
            raise ValueError("Could not parse OMNI data columns correctly.")
            
    except Exception as e:
        logger.error(f"Failed to fetch real OMNI data: {e}")
        raise RuntimeError("Real OMNIWeb API fetch is required. Network access to NASA OMNI is needed.")

def fetch_themis_ey(date_range: Tuple[datetime, datetime]) -> pd.DataFrame:
    """
    Fetch THEMIS data (Ey) from NASA CDAWeb.
    
    Args:
        date_range: Tuple of (start_datetime, end_datetime)
        
    Returns:
        pd.DataFrame with columns [timestamp, Ey]
        
    Raises:
        RuntimeError: If real data cannot be fetched.
    """
    start_dt, end_dt = date_range
    logger.info(f"Fetching THEMIS data from {start_dt} to {end_dt}")
    
    # THEMIS ESA/EFD data is available via CDAWeb
    # We will attempt to fetch from a public mirror or use a known dataset path
    # Example: https://cdaweb.gsfc.nasa.gov/pub/data/themis/tha/l2/epd/
    
    # For robustness, we use a known public CSV if available, or raise.
    # Since direct CDAWeb listing is complex, we assume a specific file path for the year.
    
    year = start_dt.year
    # Example path structure (verify existence)
    # https://cdaweb.gsfc.nasa.gov/pub/data/themis/tha/l2/epd/tha_l2_epd_eft_ssn_2023.csv
    
    # We will try to fetch from a known public dataset mirror
    # If this fails, we must raise an error.
    
    # Attempt to fetch from a simulated public endpoint (replace with real URL if available)
    # For this implementation, we assume the existence of a real data source
    # and raise if it's not accessible.
    
    # Using a placeholder for the actual CDAWeb download logic which is complex
    # In a real scenario, we would use the `cdaweb` python package or direct FTP
    # Since we cannot guarantee network access to specific NASA endpoints in this environment,
    # we will raise an error if the fetch fails.
    
    # NOTE: To satisfy the "Real Data Only" constraint, we MUST NOT generate synthetic data.
    # If the real fetch fails, we raise.
    
    # We will attempt to fetch from a known public CSV if available
    # Example: https://spdf.gsfc.nasa.gov/pub/data/themis/tha/l2/epd/
    
    # Construct URL for THEMIS data (example)
    # This is a simplified example; real implementation requires specific file discovery
    url_template = "https://spdf.gsfc.nasa.gov/pub/data/themis/tha/l2/epd/tha_l2_epd_eft_ssn_{year}.csv"
    url = url_template.format(year=year)
    
    try:
        logger.info(f"Attempting to fetch THEMIS from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        # Parse columns (adjust based on actual file format)
        # Assuming columns: Date, Time, Ey
        if 'Date' in df.columns and 'Time' in df.columns and 'Ey' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            result_df = df[['timestamp', 'Ey']].copy()
            result_df = result_df[(result_df['timestamp'] >= start_dt) & (result_df['timestamp'] <= end_dt)]
            return result_df
        else:
            raise ValueError("Could not parse THEMIS data columns correctly.")
            
    except Exception as e:
        logger.error(f"Failed to fetch real THEMIS data: {e}")
        raise RuntimeError("Real THEMIS API fetch is required. Network access to NASA CDAWeb is needed.")
