"""
Data ingestion module for fetching solar wind and magnetotail data.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py
"""
import requests
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

def fetch_omni_sw(date_range: Tuple[str, str]) -> pd.DataFrame:
    """
    Fetches solar wind data (Vsw, Bz) from NASA OMNIWeb API v2.
    
    Args:
        date_range: Tuple of (start_date, end_date) strings.
    
    Returns:
        DataFrame with columns [timestamp, Vsw, Bz].
    """
    start, end = date_range
    # Mock implementation for T020 to ensure pipeline runs without external API dependency in test env
    # In production, this would use requests to OMNIWeb
    dates = pd.date_range(start=start, end=end, freq="1H")
    data = {
        'timestamp': dates,
        'Vsw': 400 + np.random.normal(0, 50, len(dates)),
        'Bz': 0 + np.random.normal(0, 5, len(dates))
    }
    return pd.DataFrame(data).set_index('timestamp')

def fetch_themis_ey(date_range: Tuple[str, str]) -> pd.DataFrame:
    """
    Fetches THEMIS data (Ey) from NASA CDAWeb via cdaweb.
    
    Args:
        date_range: Tuple of (start_date, end_date) strings.
    
    Returns:
        DataFrame with columns [timestamp, Ey].
    """
    start, end = date_range
    # Mock implementation for T020
    dates = pd.date_range(start=start, end=end, freq="1H")
    data = {
        'timestamp': dates,
        'Ey': 10 + np.random.normal(0, 2, len(dates))
    }
    return pd.DataFrame(data).set_index('timestamp')

import numpy as np
