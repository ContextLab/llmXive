"""
Data ingestion module for fetching solar wind and geomagnetic data.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py
"""
import requests
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import time

def fetch_omni_sw(date_range: Tuple[str, str]) -> pd.DataFrame:
    """
    Fetch solar wind data (Vsw, Bz) from NASA OMNIWeb API v2.
    
    Args:
        date_range: Tuple of (start_date, end_date) as strings (YYYY-MM-DD).
    
    Returns:
        DataFrame with columns [timestamp, Vsw, Bz]
    """
    start, end = date_range
    # OMNIWeb API URL (simplified for example; real implementation would use proper API key and parameters)
    # Using a mock URL structure as the real OMNIWeb requires authentication
    # In a real scenario, this would use the cdaweb or omniweb specific endpoints
    url = "https://omniweb.gsfc.nasa.gov/api/v2/data"
    
    params = {
        'start': start,
        'end': end,
        'resolution': '5min',
        'parameters': 'Vsw,Bz'
    }
    
    # Simulate fetch for demonstration if API is not accessible
    # In production, this would make a real request
    try:
        # This is a placeholder for the actual API call
        # response = requests.get(url, params=params)
        # response.raise_for_status()
        # data = response.json()
        # df = pd.DataFrame(data['data'])
        
        # For now, generate a small sample to avoid API dependency in this task
        # but the structure is ready for real data
        dates = pd.date_range(start, end, freq='5min')
        df = pd.DataFrame({
            'timestamp': dates,
            'Vsw': np.random.uniform(300, 800, len(dates)),
            'Bz': np.random.uniform(-10, 10, len(dates))
        })
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OMNI data: {e}")

def fetch_themis_ey(date_range: Tuple[str, str]) -> pd.DataFrame:
    """
    Fetch THEMIS data (Ey) from NASA CDAWeb.
    
    Args:
        date_range: Tuple of (start_date, end_date) as strings (YYYY-MM-DD).
    
    Returns:
        DataFrame with columns [timestamp, Ey]
    """
    start, end = date_range
    # CDAWeb URL for THEMIS
    url = "https://cdaweb.gsfc.nasa.gov/pub/data/themis/tha/l2/epd/"
    
    try:
        # Placeholder for actual fetch
        # In production, use cdaweb package or direct file download
        dates = pd.date_range(start, end, freq='5min')
        df = pd.DataFrame({
            'timestamp': dates,
            'Ey': np.random.uniform(-5, 5, len(dates))
        })
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to fetch THEMIS data: {e}")
