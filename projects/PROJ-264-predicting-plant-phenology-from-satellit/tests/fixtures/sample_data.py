"""
Module for generating valid sample data structures for testing.

These fixtures are used to validate schema contracts and test logic
without requiring live API access or large datasets.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def create_sample_phenology_df(n_rows: int = 10) -> pd.DataFrame:
    """
    Create a sample DataFrame mimicking phenology observations.
    
    Columns match the expected schema from data-model.md:
    - site_id: str
    - date: datetime
    - event_type: str (e.g., 'leaf_out', 'flowering')
    - value: float
    """
    dates = pd.date_range(start="2020-03-01", periods=n_rows, freq="D")
    site_ids = ["site_001"] * (n_rows // 2) + ["site_002"] * (n_rows - n_rows // 2)
    events = ["leaf_out", "flowering"] * (n_rows // 2)
    values = np.random.uniform(0.5, 5.0, n_rows)
    
    return pd.DataFrame({
        "site_id": site_ids,
        "date": dates,
        "event_type": events,
        "value": values
    })


def create_sample_satellite_df(n_rows: int = 10) -> pd.DataFrame:
    """
    Create a sample DataFrame mimicking satellite data (NDVI/EVI).
    
    Columns:
    - site_id: str
    - date: datetime
    - ndvi: float
    - evi: float
    - cloud_cover: float
    """
    dates = pd.date_range(start="2020-01-01", periods=n_rows, freq="10D")
    site_ids = ["site_001"] * n_rows
    ndvi = np.random.uniform(0.1, 0.9, n_rows)
    evi = np.random.uniform(0.05, 0.7, n_rows)
    cloud_cover = np.random.uniform(0.0, 0.3, n_rows)
    
    return pd.DataFrame({
        "site_id": site_ids,
        "date": dates,
        "ndvi": ndvi,
        "evi": evi,
        "cloud_cover": cloud_cover
    })


def create_sample_climate_df(n_rows: int = 10) -> pd.DataFrame:
    """
    Create a sample DataFrame mimicking climate data.
    
    Columns:
    - site_id: str
    - date: datetime
    - tavg: float (average temperature)
    - tmin: float
    - tmax: float
    - precip: float
    """
    dates = pd.date_range(start="2020-01-01", periods=n_rows, freq="D")
    site_ids = ["site_001"] * n_rows
    tavg = np.random.uniform(10.0, 25.0, n_rows)
    tmin = tavg - np.random.uniform(5.0, 10.0, n_rows)
    tmax = tavg + np.random.uniform(5.0, 10.0, n_rows)
    precip = np.random.uniform(0.0, 10.0, n_rows)
    
    return pd.DataFrame({
        "site_id": site_ids,
        "date": dates,
        "tavg": tavg,
        "tmin": tmin,
        "tmax": tmax,
        "precip": precip
    })
