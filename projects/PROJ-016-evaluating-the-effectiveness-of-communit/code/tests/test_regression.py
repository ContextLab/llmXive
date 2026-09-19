import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import tempfile
import os

# Add code directory to path for imports
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

add_code_to_path()

from analysis.regression import detect_time_invariant_countries, save_time_invariant_report, filter_time_invariant_countries

@pytest.fixture
def sample_panel_data():
    """
    Creates a synthetic panel dataset with:
    - Country A: Time-varying regime (0, 1, 0, 1)
    - Country B: Time-invariant regime (1, 1, 1, 1)
    - Country C: Time-invariant regime (0, 0, 0, 0)
    - Country D: Only 1 year of data (should be flagged as invariant)
    """
    data = {
        'iso_code': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'D'],
        'year': [2000, 2001, 2002, 2003] * 4,
        'regime_type': [0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1], # D is invariant too
        'land_use_change': np.random.rand(16),
        'gdp_per_capita': np.random.rand(16) * 10000,
        'population_density': np.random.rand(16) * 100
    }
    # Make D have only 1 year to test edge case
    data['iso_code'] = ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'D']
    data['year'] = [2000, 2001, 2002, 2003, 2000, 2001, 2002, 2003, 2000, 2001, 2002, 2003, 2000, 2000, 2000, 2000]
    data['regime_type'] = [0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 5, 5, 5, 5] # D is constant
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_detect_time_invariant_varying_countries(sample_panel_data):
    """Test that varying countries are NOT flagged."""
    flagged = detect_time_invariant_countries(sample_panel_data, 'iso_code', 'regime_type')
    assert 'A' not in flagged, "Country A has varying regime_type and should not be flagged."

def test_detect_time_invariant_constant_countries(sample_panel_data):
    """Test that constant countries ARE flagged."""
    flagged = detect_time_invariant_countries(sample_panel_data, 'iso_code', 'regime_type')
    assert 'B' in flagged, "Country B has constant regime_type and should be flagged."
    assert 'C' in flagged, "Country C has constant regime_type and should be flagged."
    assert 'D' in flagged, "Country D has constant regime_type (and single year) and should be flagged."

def test_save_time_invariant_report(temp_data_dir, sample_panel_data):
    """Test saving the report to JSON."""
    output_path = os.path.join(temp_data_dir, 'test_output.json')
    flagged = detect_time_invariant_countries(sample_panel_data, 'iso_code', 'regime_type')
    save_time_invariant_report(flagged, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'time_invariant_countries' in data
    assert 'B' in data['time_invariant_countries']
    assert 'count' in data
    assert data['count'] == 3

def test_filter_time_invariant_countries(sample_panel_data):
    """Test filtering out flagged countries."""
    flagged = ['B', 'C']
    filtered_df = filter_time_invariant_countries(sample_panel_data, flagged, 'iso_code')
    
    assert len(filtered_df) < len(sample_panel_data)
    assert not filtered_df[filtered_df['iso_code'] == 'B'].empty == False
    assert not filtered_df[filtered_df['iso_code'] == 'C'].empty == False
    assert filtered_df[filtered_df['iso_code'] == 'A'].empty == False

def test_detect_time_invariant_missing_columns(sample_panel_data):
    """Test behavior when columns are missing."""
    # Create a df without 'regime_type'
    df_no_var = sample_panel_data.drop(columns=['regime_type'])
    flagged = detect_time_invariant_countries(df_no_var, 'iso_code', 'regime_type')
    assert flagged == [] # Should return empty list on error

def test_detect_time_invariant_all_nan(sample_panel_data):
    """Test behavior when all values are NaN."""
    df_nan = sample_panel_data.copy()
    df_nan['regime_type'] = np.nan
    flagged = detect_time_invariant_countries(df_nan, 'iso_code', 'regime_type')
    # If all are NaN, variance is NaN, so all should be flagged (or handled gracefully)
    # Based on implementation: variance_by_country will be NaN, so (variance.isna()) is True -> flagged
    assert len(flagged) == 4 # All countries flagged