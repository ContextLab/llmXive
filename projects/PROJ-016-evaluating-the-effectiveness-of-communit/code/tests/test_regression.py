import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import tempfile
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from analysis.regression import (
    detect_time_invariant_countries,
    save_time_invariant_report,
    filter_time_invariant_countries
)

@pytest.fixture
def sample_panel_data():
    """Create a sample panel dataset with some time-invariant and some time-varying countries."""
    data = {
        'country_code': ['USA'] * 5 + ['CAN'] * 5 + ['MEX'] * 5,
        'year': list(range(2000, 2005)) * 3,
        'regime_type': [1, 1, 1, 1, 1] +  # USA: Time invariant (constant 1)
                       [0, 1, 0, 1, 0] +  # CAN: Time varying
                       [0, 0, 0, 0, 0],   # MEX: Time invariant (constant 0)
        'land_use_change': np.random.rand(15),
        'gdp_per_capita': np.random.rand(15) * 10000,
        'population_density': np.random.rand(15) * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_detect_time_invariant_varying_countries(sample_panel_data):
    """Test that countries with varying regime_type are NOT flagged."""
    flagged = detect_time_invariant_countries(sample_panel_data)
    # CAN should not be in the list
    assert 'CAN' not in flagged
    # USA and MEX should be in the list
    assert 'USA' in flagged
    assert 'MEX' in flagged

def test_detect_time_invariant_constant_countries(sample_panel_data):
    """Test that countries with constant regime_type ARE flagged."""
    flagged = detect_time_invariant_countries(sample_panel_data)
    assert 'USA' in flagged
    assert 'MEX' in flagged

def test_save_time_invariant_report(sample_panel_data, temp_data_dir):
    """Test that the report is saved correctly as JSON."""
    flagged = detect_time_invariant_countries(sample_panel_data)
    output_path = temp_data_dir / "time_invariant_countries.json"
    
    save_time_invariant_report(flagged, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'time_invariant_countries' in data
    assert data['count'] == len(flagged)
    assert set(data['time_invariant_countries']) == {'USA', 'MEX'}

def test_filter_time_invariant_countries(sample_panel_data):
    """Test that filtering removes time-invariant countries."""
    flagged = detect_time_invariant_countries(sample_panel_data)
    filtered_df = filter_time_invariant_countries(sample_panel_data, flagged)
    
    # Should only contain CAN rows
    assert len(filtered_df) == 5
    assert all(filtered_df['country_code'] == 'CAN')

def test_detect_time_invariant_missing_columns(sample_panel_data):
    """Test behavior when required columns are missing."""
    df_missing = sample_panel_data.drop(columns=['regime_type'])
    with pytest.raises(ValueError):
        detect_time_invariant_countries(df_missing)

def test_detect_time_invariant_all_nan():
    """Test behavior when all regime_type values are NaN."""
    data = {
        'country_code': ['USA'] * 5,
        'year': list(range(2000, 2005)),
        'regime_type': [np.nan] * 5
    }
    df = pd.DataFrame(data)
    flagged = detect_time_invariant_countries(df)
    assert len(flagged) == 0

def test_filter_time_invariant_empty_list(sample_panel_data):
    """Test filtering with an empty list of flagged countries."""
    filtered_df = filter_time_invariant_countries(sample_panel_data, [])
    assert len(filtered_df) == len(sample_panel_data)
    assert list(filtered_df.columns) == list(sample_panel_data.columns)