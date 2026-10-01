"""
Tests for T028a: Derive Demographics
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from derive_demographics import fetch_world_bank_indicator, merge_demographics_to_data, log_gap

@pytest.fixture
def sample_demographics_df():
    """Create a mock demographics DataFrame."""
    data = {
        'country_code': ['USA', 'GBR', 'DEU'],
        'SP.POP.TOTL_2018': [327000000, 66000000, 83000000],
        'SP.URB.TOTL.IN.ZS_2018': [82.3, 83.4, 77.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_moral_data(tmp_path):
    """Create a mock moral data parquet file."""
    data = {
        'country': ['USA', 'GBR', 'FRA', 'USA'],
        'response_time': [1000, 2000, 1500, 1200],
        'temperature': [20.0, 15.0, 18.0, 22.0]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "merged_dataset.parquet"
    df.to_parquet(path)
    return str(path)

@pytest.fixture
def sample_output_path(tmp_path):
    return str(tmp_path / "covariates.csv")

def test_fetch_world_bank_indicator_success():
    """Test fetching from World Bank API (mocked)."""
    mock_data = [
        {"page": 1, "pages": 1, "per_page": 300, "total": 2},
        [
            {"countryiso3code": "USA", "date": "2018", "value": 327000000},
            {"countryiso3code": "USA", "date": "2017", "value": 325000000}
        ]
    ]
    
    with patch('derive_demographics.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        logger = MagicMock()
        result = fetch_world_bank_indicator("SP.POP.TOTL", logger)

        assert result is not None
        assert 'country_code' in result.columns
        assert 'USA' in result['country_code'].values

def test_merge_demographics_to_data(sample_moral_data, sample_demographics_df, sample_output_path):
    """Test merging demographics into moral data."""
    logger = MagicMock()
    
    merge_demographics_to_data(sample_moral_data, sample_demographics_df, sample_output_path, logger)
    
    # Verify output file exists
    assert os.path.exists(sample_output_path)
    
    # Verify content
    result_df = pd.read_csv(sample_output_path)
    assert 'SP.POP.TOTL_2018' in result_df.columns
    assert 'SP.URB.TOTL.IN.ZS_2018' in result_df.columns
    
    # Check that USA rows got values
    usa_rows = result_df[result_df['country'] == 'USA']
    assert len(usa_rows) == 2
    assert usa_rows['SP.POP.TOTL_2018'].iloc[0] == 327000000
    
    # Check that FRA (missing in demographics) got NaN
    fra_rows = result_df[result_df['country'] == 'FRA']
    assert fra_rows['SP.POP.TOTL_2018'].iloc[0] != fra_rows['SP.POP.TOTL_2018'].iloc[0] # NaN check

def test_log_gap(sample_demographics_df, sample_moral_data):
    """Test logging the gap in coverage."""
    moral_df = pd.read_parquet(sample_moral_data)
    logger = MagicMock()
    
    log_gap(moral_df, sample_demographics_df, logger)
    
    # Verify log calls happened
    assert logger.info.call_count >= 3