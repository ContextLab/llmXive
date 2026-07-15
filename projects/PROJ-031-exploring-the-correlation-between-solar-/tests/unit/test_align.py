"""
Unit tests for code/align.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from align import find_dst_minima, match_solar_events, load_dst_indices

def test_find_dst_minima_basic():
    """Test that argrelextrema correctly identifies a simple V-shape minimum."""
    # Create synthetic data: 10, 5, 0, 5, 10 -> min at index 2
    data = pd.DataFrame({
        'datetime': pd.date_range(start='2023-01-01', periods=5, freq='H'),
        'dst': [10, 5, -50, 5, 10]  # -50 is a clear storm
    })
    
    storms = find_dst_minima(data, window=1)
    
    assert len(storms) == 1
    assert storms[0]['dst_min'] == -50
    assert storms[0]['storm_start'] == data.iloc[2]['datetime']

def test_find_dst_minima_no_storm():
    """Test that trivial fluctuations above threshold are ignored."""
    data = pd.DataFrame({
        'datetime': pd.date_range(start='2023-01-01', periods=5, freq='H'),
        'dst': [10, 5, -10, 5, 10]  # -10 is above -30 threshold
    })
    
    storms = find_dst_minima(data, window=1)
    
    assert len(storms) == 0

def test_match_solar_events_within_window():
    """Test matching a flare within the 3-day window."""
    storm = {
        'storm_start': datetime(2023, 1, 10, 12, 0),
        'dst_min': -100,
        'storm_idx': 0
    }
    
    # Flare at 2023-01-09 (1 day before)
    flares = pd.DataFrame({
        'datetime': [datetime(2023, 1, 9, 10, 0)],
        'class': ['X1.0'],
        'peak_flux': [1e-4]
    })
    
    # CME at 2023-01-08 (2 days before)
    cmes = pd.DataFrame({
        'datetime': [datetime(2023, 1, 8, 10, 0)],
        'speed': [1000],
        'width': [360]
    })
    
    result = match_solar_events(storm, flares, cmes)
    
    assert result['has_solar_match'] is True
    assert result['matched_flare'] is not None
    assert result['matched_cme'] is not None
    assert result['flare_age_hours'] == 26.0  # 1 day + 2 hours
    assert result['cme_age_hours'] == 50.0   # 2 days + 2 hours

def test_match_solar_events_outside_window():
    """Test that events outside 3-day window are ignored."""
    storm = {
        'storm_start': datetime(2023, 1, 10, 12, 0),
        'dst_min': -100,
        'storm_idx': 0
    }
    
    # Flare at 2023-01-05 (5 days before)
    flares = pd.DataFrame({
        'datetime': [datetime(2023, 1, 5, 10, 0)],
        'class': ['X5.0'],
        'peak_flux': [5e-4]
    })
    
    cmes = pd.DataFrame({
        'datetime': [datetime(2023, 1, 5, 10, 0)],
        'speed': [2000],
        'width': [360]
    })
    
    result = match_solar_events(storm, flares, cmes)
    
    assert result['has_solar_match'] is False
    assert result['matched_flare'] is None
    assert result['matched_cme'] is None

def test_match_solar_events_multiple_candidates():
    """Test selection of the most intense flare."""
    storm = {
        'storm_start': datetime(2023, 1, 10, 12, 0),
        'dst_min': -100,
        'storm_idx': 0
    }
    
    # Two flares within window
    flares = pd.DataFrame({
        'datetime': [datetime(2023, 1, 9, 10, 0), datetime(2023, 1, 9, 11, 0)],
        'class': ['M1.0', 'X2.0'],
        'peak_flux': [1e-5, 2e-4] # X2 is stronger
    })
    
    cmes = pd.DataFrame() # Empty CMEs
    
    result = match_solar_events(storm, flares, cmes)
    
    assert result['matched_flare']['flare_class'] == 'X2.0'
    assert result['matched_flare']['flare_peak_flux'] == 2e-4