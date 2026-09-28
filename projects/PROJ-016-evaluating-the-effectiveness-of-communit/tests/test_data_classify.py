import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
import sys
import os

# Ensure code directory is in path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.classify import (
    validate_proxy_variance, 
    save_validation_results, 
    load_validation_results,
    load_metadata
)

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with varying and constant proxy values."""
    data = {
        'country_code': ['USA', 'USA', 'USA', 'CAN', 'CAN', 'CAN', 'MEX', 'MEX'],
        'year': [2000, 2005, 2010, 2000, 2005, 2010, 2000, 2005],
        'proxy_value': [0.5, 0.6, 0.55, 0.8, 0.8, 0.8, 0.1, 0.2] # USA varies, CAN constant, MEX varies
    }
    return pd.DataFrame(data)

class TestValidateProxyVariance:
    def test_identifies_zero_variance_countries(self, sample_dataframe):
        """Test that countries with constant proxy values are excluded."""
        result = validate_proxy_variance(sample_dataframe)
        
        assert 'excluded_countries' in result
        assert 'CAN' in result['excluded_countries']
        assert 'USA' not in result['excluded_countries']
        assert 'MEX' not in result['excluded_countries']
        assert result['total_excluded'] == 1

    def test_handles_insufficient_data_points(self):
        """Test handling of countries with < 2 data points."""
        data = {
            'country_code': ['A', 'A', 'B'],
            'year': [2000, 2001, 2000],
            'proxy_value': [0.5, 0.6, 0.5]
        }
        df = pd.DataFrame(data)
        result = validate_proxy_variance(df)
        
        # Country B has only 1 point, should be excluded
        assert 'B' in result['excluded_countries']
        assert "Insufficient data points" in result['reasons']['B']

    def test_handles_missing_columns(self, temp_data_dir):
        """Test that ValueError is raised if required columns are missing."""
        data = {
            'country_code': ['USA'],
            'year': [2000]
            # Missing 'proxy_value'
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="DataFrame must contain"):
            validate_proxy_variance(df)

    def test_saves_and_loads_validation_results(self, sample_dataframe, temp_data_dir):
        """Test saving and loading validation results to JSON."""
        output_path = temp_data_dir / "validation.json"
        
        # Run validation
        result = validate_proxy_variance(sample_dataframe)
        
        # Save
        save_validation_results(result, output_path)
        
        assert output_path.exists()
        
        # Load and verify
        loaded = load_validation_results(output_path)
        assert loaded['excluded_countries'] == result['excluded_countries']
        assert loaded['reasons'] == result['reasons']

    def test_loads_empty_if_file_missing(self, temp_data_dir):
        """Test load_validation_results returns empty dict if file missing."""
        non_existent = temp_data_dir / "missing.json"
        result = load_validation_results(non_existent)
        
        assert result == {"excluded_countries": [], "reasons": {}}

class TestLoadMetadata:
    def test_loads_metadata(self, temp_data_dir):
        """Test loading metadata from a valid JSON file."""
        metadata_path = temp_data_dir / "metadata.json"
        expected_data = {"indicator_code": "TEST", "threshold": 0.5}
        
        with open(metadata_path, 'w') as f:
            json.dump(expected_data, f)
        
        loaded = load_metadata(metadata_path)
        assert loaded == expected_data

    def test_raises_on_missing_metadata(self, temp_data_dir):
        """Test that FileNotFoundError is raised if metadata missing."""
        with pytest.raises(FileNotFoundError):
            load_metadata(temp_data_dir / "nonexistent.json")