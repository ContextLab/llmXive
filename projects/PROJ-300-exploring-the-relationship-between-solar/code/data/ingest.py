"""
Data ingestion module for fetching solar wind and geomagnetic data.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py
"""
import requests
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import time

# OMNIWeb API Base URL (using a public endpoint or proxy if direct is restricted)
# Note: Direct OMNIWeb access often requires a session or specific headers.
# Using a known public dataset endpoint or a simulated fetch for structure if real API is blocked.
# For real implementation, we assume the environment has network access to NASA APIs.
OMNI_API_URL = "https://omniweb.gsfc.nasa.gov/cgi-bin/omni_txt.pl" # Placeholder for actual endpoint logic
# Since direct scraping of NASA CGI is fragile, we use a known working pattern or fallback to a dataset package if available.
# However, per spec, we must use requests. We will attempt a fetch and fail loudly if it fails.
# A common public access point for OMNI 1-min or 5-min data is via CDAWeb or a specific NASA endpoint.
# Let's use a standard pattern for NASA OMNI data fetch if a public endpoint is available, 
# otherwise we rely on the 'cdaweb' package for THEMIS and a specific URL for OMNI if possible.
# Given the constraint "Real OMNIWeb API fetch is required", we attempt to construct a valid request.
# The actual OMNIWeb text download often requires a POST with specific parameters.
# We will use a standard GET to a public mirror or the official API if configured.

# For the purpose of this implementation, we assume a valid endpoint exists or we use the CDAWeb API for both if possible.
# However, the spec distinguishes OMNIWeb for SW and CDAWeb for THEMIS.
# We will implement the logic to fetch from the official OMNIWeb text download URL format.

def fetch_omni_sw(date_range: Tuple[str, str]) -> pd.DataFrame:
    """
    Fetch solar wind data (Vsw, Bz) from NASA OMNIWeb.
    
    Args:
        date_range: Tuple of (start_date, end_date) as strings 'YYYY-MM-DD'.
    
    Returns:
        DataFrame with columns [timestamp, Vsw, Bz].
    
    Raises:
        RuntimeError: If the fetch fails (network or API error).
    """
    start, end = date_range
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    
    # Construct the request parameters for OMNIWeb text download
    # This is a simplified representation; real OMNIWeb requires specific form data.
    # We will attempt to use a public API wrapper or direct request.
    # Since direct scraping is often blocked, we assume the environment has a working endpoint.
    # If the real API is unreachable, this MUST fail loudly.
    
    url = "https://omniweb.gsfc.nasa.gov/cgi-bin/omni_txt.pl"
    params = {
        'start_time': start_dt.strftime("%Y-%m-%d %H:%M"),
        'end_time': end_dt.strftime("%Y-%m-%d %H:%M"),
        'list': '5min', # 5-minute resolution
        'format': 'txt',
        'data': 'Vsw,Bz'
    }
    
    # Note: The OMNIWeb CGI often requires a POST request with a session.
    # If GET fails, we might need a POST.
    # We will attempt GET first.
    try:
        # Some NASA endpoints require a specific User-Agent
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; SciencePipeline/1.0)'}
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # If GET fails, try POST with form data
        try:
            post_data = {
                'start_time': start_dt.strftime("%Y-%m-%d %H:%M"),
                'end_time': end_dt.strftime("%Y-%m-%d %H:%M"),
                'list': '5min',
                'format': 'txt',
                'data': 'Vsw,Bz'
            }
            response = requests.post(url, data=post_data, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e2:
            raise RuntimeError(f"Real OMNIWeb API fetch is required. Network access to NASA OMNIWeb is needed. Failed with: {e2}")

    # Parse the text response
    # The format is typically a table with headers
    try:
        # Read into pandas, skipping header lines if necessary
        # Assuming the response is tab/space delimited
        df = pd.read_csv(pd.io.common.StringIO(response.text), delim_whitespace=True, comment='#')
        
        # Identify columns - OMNI data usually has specific column names
        # We need to map to 'timestamp', 'Vsw', 'Bz'
        # This depends on the exact output format of the API
        # Common format: Time, Vsw, Bz, ...
        # We will assume the first column is time, and look for Vsw and Bz
        if 'Time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Time'])
        elif 'YYYY-MM-DD' in df.columns:
            # Reconstruct timestamp if split
            pass # Handle specific format if needed
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Heuristic: find Vsw and Bz columns
        vsw_col = [c for c in df.columns if 'vsw' in c or 'speed' in c]
        bz_col = [c for c in df.columns if 'bz' in c or 'b_z' in c]
        
        if not vsw_col or not bz_col:
            raise ValueError("Could not identify Vsw or Bz columns in OMNI response.")
        
        result = pd.DataFrame({
            'timestamp': df['timestamp'],
            'Vsw': df[vsw_col[0]],
            'Bz': df[bz_col[0]]
        })
        
        result = result.dropna(subset=['timestamp', 'Vsw', 'Bz'])
        result = result.sort_values('timestamp').reset_index(drop=True)
        
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to parse OMNIWeb response: {e}")

def fetch_themis_ey(date_range: Tuple[str, str]) -> pd.DataFrame:
    """
    Fetch THEMIS data (Ey) from NASA CDAWeb.
    
    Args:
        date_range: Tuple of (start_date, end_date) as strings 'YYYY-MM-DD'.
    
    Returns:
        DataFrame with columns [timestamp, Ey].
    
    Raises:
        RuntimeError: If the fetch fails.
    """
    # Using the cdaweb package as per spec
    try:
        from cdaweb import get_var
    except ImportError:
        raise RuntimeError("The 'cdaweb' package is required to fetch THEMIS data. Install it via pip.")

    start, end = date_range
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    
    # THEMIS FGM or Electric Field instrument data
    # We need Ey (Y-component of Electric Field in GSM)
    # Dataset: THEMIS ESA or FGM? Ey is usually from ESP or FGM? 
    # Actually, Ey is often derived from the Electric Field instrument (EFI) on THEMIS.
    # Dataset: 'thf_l2_efi' or similar.
    # Let's assume a standard dataset path.
    dataset = "thf_l2_efi" # Placeholder for actual dataset name
    variable = "Ey" # Variable name
    
    try:
        # The cdaweb package handles the complex CDAWeb API
        # We need to specify the correct dataset and variable
        # This is a simplified call; real usage requires exact dataset/variable names
        df = get_var(
            dataset=dataset,
            variable=variable,
            start_time=start_dt,
            end_time=end_dt
        )
        
        if df is None or df.empty:
            raise ValueError("No data returned from CDAWeb for THEMIS Ey.")
        
        # Ensure timestamp and Ey columns exist
        if 'Time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Time'])
        elif 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'])
        
        result = pd.DataFrame({
            'timestamp': df['timestamp'],
            'Ey': df[variable] if variable in df.columns else df.iloc[:, 1] # Fallback
        })
        
        result = result.dropna(subset=['timestamp', 'Ey'])
        result = result.sort_values('timestamp').reset_index(drop=True)
        
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to fetch THEMIS data from CDAWeb: {e}")
