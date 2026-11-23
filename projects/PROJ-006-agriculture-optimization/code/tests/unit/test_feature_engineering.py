"""
Unit Tests for Feature Engineering Module (T018a)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.data.processing.feature_engineering import (
    calculate_stability_score,
    calculate_csa_index,
    derive_village_id,
    perform_village_aggregation,
    extract_raw_ndvi_timeseries
)

def test_calculate_stability_score_perfect():
    """Test stability score with zero variance."""
    series = pd.Series([0.5, 0.5, 0.5, 0.5])
    score = calculate_stability_score(series)
    assert score == 100.0

def test_calculate_stability_score_zero_mean():
    """Test stability score when mean is zero."""
    series = pd.Series([0.0, 0.0, 0.0])
    score = calculate_stability_score(series)
    assert score == 0.0

def test_calculate_stability_score_normal():
    """Test stability score with normal variance."""
    # Mean ~ 0.5, Std ~ 0.1 -> CV = 0.2 -> Score = 5
    series = pd.Series([0.4, 0.6, 0.4, 0.6])
    score = calculate_stability_score(series)
    assert 4.0 < score < 6.0

def test_calculate_csa_index_basic():
    """Test CSA Index calculation."""
    row = pd.Series({
        'practice_mixed_farming': 1,
        'practice_terracing': 0,
        'practice_conservation_tillage': 1,
        'practice_agroforestry': 0,
        'extension_visits': 3
    })
    score = calculate_csa_index(row)
    assert score == 1 + 0 + 1 + 0 + 3

def test_calculate_csa_index_missing():
    """Test CSA Index with missing columns."""
    row = pd.Series({})
    score = calculate_csa_index(row)
    assert score == 0.0

def test_derive_village_id():
    """Test village ID derivation."""
    lat, lon = 10.5, 20.5
    grid = 1.0
    vid = derive_village_id(lat, lon, grid)
    assert vid == "10.0_20.0"

def test_derive_village_id_precision():
    """Test village ID derivation with smaller grid."""
    lat, lon = 10.55, 20.55
    grid = 0.1
    vid = derive_village_id(lat, lon, grid)
    # int(10.55 / 0.1) = 105 -> 105 * 0.1 = 10.5
    assert vid == "10.5_20.5"

def test_extract_raw_ndvi_timeseries_structure():
    """Test that NDVI extraction returns correct columns."""
    df_input = pd.DataFrame({
        'household_id': [1, 2],
        'country': ['A', 'B'],
        'survey_year': [2020, 2021]
    })
    df_out = extract_raw_ndvi_timeseries(df_input, synthetic_mode=True)
    
    required_cols = ['household_id', 'month', 'ndvi_value', 'country', 'survey_year']
    assert all(col in df_out.columns for col in required_cols)
    assert len(df_out) > 0
    assert df_out['ndvi_value'].between(0.0, 1.0).all()