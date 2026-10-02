import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import tempfile
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.regression import detect_time_invariant_countries, save_time_invariant_report, filter_time_invariant_countries

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_panel_data():
    """
    Create a sample panel dataframe with varying and constant regime types.
    """
    data = {
        'country_code': ['USA'] * 5 + ['BRA'] * 5 + ['CHN'] * 5,
        'year': [2000, 2001, 2002, 2003, 2004] * 3,
        'regime_type': [1, 1, 1, 1, 1] + [0, 1, 0, 1, 0] + [0, 0, 0, 0, 0],
        'land_use_change': [0.1, 0.2, 0.3, 0.4, 0.5] * 3,
        'gdp_per_capita': [10000] * 15,
        'population_density': [50] * 15
    }
    return pd.DataFrame(data)

class TestTimeInvariance:
    def test_detect_time_invariant_varying_countries(self, sample_panel_data):
        """Test that varying countries are NOT flagged."""
        # USA (all 1), CHN (all 0) should be flagged. BRA (0,1,0,1,0) should NOT.
        result = detect_time_invariant_countries(sample_panel_data)
        assert 'USA' in result
        assert 'CHN' in result
        assert 'BRA' not in result
        assert len(result) == 2

    def test_detect_time_invariant_constant_countries(self, temp_data_dir):
        """Test detection when all countries are constant."""
        data = pd.DataFrame({
            'country_code': ['A'] * 3 + ['B'] * 3,
            'year': [2000, 2001, 2002] * 2,
            'regime_type': [1, 1, 1, 0, 0, 0],
            'land_use_change': [1, 2, 3, 4, 5, 6]
        })
        result = detect_time_invariant_countries(data)
        assert len(result) == 2
        assert set(result) == {'A', 'B'}

    def test_save_time_invariant_report(self, temp_data_dir, sample_panel_data):
        """Test saving the report to JSON."""
        output_path = temp_data_dir / "time_invariant_countries.json"
        invariant = detect_time_invariant_countries(sample_panel_data)
        save_time_invariant_report(invariant, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            report = json.load(f)
        
        assert 'time_invariant_countries' in report
        assert 'count' in report
        assert report['count'] == len(invariant)

    def test_filter_time_invariant_countries(self, sample_panel_data):
        """Test filtering out the flagged countries."""
        invariant = ['USA', 'CHN']
        filtered = filter_time_invariant_countries(sample_panel_data, invariant)
        
        assert len(filtered) == 5 # Only BRA rows remain
        assert all(filtered['country_code'] == 'BRA')

    def test_detect_time_invariant_missing_columns(self, temp_data_dir):
        """Test behavior when columns are missing."""
        data = pd.DataFrame({
            'country_code': ['A', 'B'],
            'year': [2000, 2001]
        })
        result = detect_time_invariant_countries(data)
        assert result == []

    def test_detect_time_invariant_all_nan(self, temp_data_dir):
        """Test behavior when regime_type is all NaN."""
        data = pd.DataFrame({
            'country_code': ['A'] * 3,
            'year': [2000, 2001, 2002],
            'regime_type': [np.nan, np.nan, np.nan]
        })
        result = detect_time_invariant_countries(data)
        # NaN std is treated as invariant (or nunique=1 effectively)
        assert 'A' in result