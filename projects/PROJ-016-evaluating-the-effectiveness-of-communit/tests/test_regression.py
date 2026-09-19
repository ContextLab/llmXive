import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import tempfile
import os

# Add code directory to path for imports
@pytest.fixture
def add_code_to_path():
    code_path = Path(__file__).parent.parent
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def sample_panel_data():
    """
    Create a sample panel dataset with some time-invariant and time-variant countries.
    """
    data = {
        'country_code': ['USA', 'USA', 'USA', 'BRA', 'BRA', 'BRA', 'CHN', 'CHN', 'CHN', 'DEU', 'DEU', 'DEU'],
        'year': [2000, 2005, 2010, 2000, 2005, 2010, 2000, 2005, 2010, 2000, 2005, 2010],
        'regime_type': [1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0], # USA: constant 1, BRA: varying, CHN: constant 1, DEU: varying
        'land_use_change': [0.1, 0.2, 0.15, -0.1, 0.05, -0.05, 0.3, 0.35, 0.32, 0.0, 0.1, 0.05],
        'gdp_per_capita': [40000, 42000, 44000, 8000, 9000, 10000, 10000, 11000, 12000, 35000, 37000, 39000],
        'population_density': [30, 31, 32, 25, 26, 27, 150, 152, 154, 230, 232, 234]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_detect_time_invariant_varying_countries(sample_panel_data):
    from analysis.regression import detect_time_invariant_countries
    
    # USA (all 1), CHN (all 1) should be time-invariant.
    # BRA (0, 1, 0), DEU (0, 1, 0) should be time-variant.
    invariant = detect_time_invariant_countries(sample_panel_data)
    
    assert 'USA' in invariant
    assert 'CHN' in invariant
    assert 'BRA' not in invariant
    assert 'DEU' not in invariant

def test_detect_time_invariant_constant_countries(sample_panel_data):
    from analysis.regression import detect_time_invariant_countries
    
    invariant = detect_time_invariant_countries(sample_panel_data)
    
    # Check that we found exactly the constant ones
    assert set(invariant) == {'USA', 'CHN'}

def test_save_time_invariant_report(sample_panel_data, temp_data_dir):
    from analysis.regression import detect_time_invariant_countries, save_time_invariant_report
    
    invariant = detect_time_invariant_countries(sample_panel_data)
    output_path = temp_data_dir / 'time_invariant.json'
    
    save_time_invariant_report(invariant, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    
    assert 'time_invariant_countries' in data
    assert data['count'] == len(invariant)
    assert set(data['time_invariant_countries']) == {'USA', 'CHN'}

def test_filter_time_invariant_countries(sample_panel_data):
    from analysis.regression import filter_time_invariant_countries
    
    invariant = ['USA', 'CHN']
    filtered = filter_time_invariant_countries(sample_panel_data, invariant)
    
    # Original had 12 rows. USA (3) + CHN (3) = 6 removed.
    # Expected 6 rows.
    assert len(filtered) == 6
    
    # Check that USA and CHN are gone
    assert 'USA' not in filtered['country_code'].values
    assert 'CHN' not in filtered['country_code'].values
    
    # Check that BRA and DEU remain
    assert 'BRA' in filtered['country_code'].values
    assert 'DEU' in filtered['country_code'].values

def test_detect_time_invariant_missing_columns(sample_panel_data):
    from analysis.regression import detect_time_invariant_countries
    
    df_missing = sample_panel_data.drop(columns=['regime_type'])
    
    with pytest.raises(ValueError):
        detect_time_invariant_countries(df_missing)

def test_detect_time_invariant_all_nan(sample_panel_data):
    from analysis.regression import detect_time_invariant_countries
    
    # Create a dataframe with NaN regime_type
    df_nan = sample_panel_data.copy()
    df_nan.loc[:, 'regime_type'] = np.nan
    
    # nunique() on NaNs might be 0 or 1 depending on pandas version, but usually 0 for NaN only
    # However, if all are NaN, unique count is 0 (or 1 if NaN counts).
    # If nunique() returns 0, it is considered invariant (<=1).
    # If nunique() returns 1 (NaN), it is also invariant.
    # So it should return all countries as invariant if all are NaN.
    invariant = detect_time_invariant_countries(df_nan)
    
    # All countries should be flagged as invariant if they have only 0 or 1 unique value
    assert len(invariant) == 4 # USA, BRA, CHN, DEU

def test_filter_time_invariant_empty_list(sample_panel_data):
    from analysis.regression import filter_time_invariant_countries
    
    filtered = filter_time_invariant_countries(sample_panel_data, [])
    
    assert len(filtered) == len(sample_panel_data)