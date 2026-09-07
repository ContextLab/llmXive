"""
Unit tests for the aggregate_satellites function in data/ingestion.py.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import sys

# Add code directory to path if not already present
code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code')
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from data.ingestion import aggregate_satellites, NormalPoint, DataIngestionError, validate_config

@pytest.fixture
def mock_config():
    """Mock config to return a fake verified_datasets path."""
    mock_cfg = MagicMock()
    mock_cfg.paths = {'verified_datasets': '/tmp/verified_datasets.yaml', 'data_raw': '/tmp/data'}
    return mock_cfg

@pytest.fixture
def mock_verified_yaml(tmp_path):
    """Create a temporary verified_datasets.yaml file."""
    yaml_path = tmp_path / "verified_datasets.yaml"
    yaml_path.write_text("LAGEOS: http://example.com/lageos.txt\nSTARLETTE: http://example.com/starlette.txt\n")
    return str(yaml_path)

@patch('data.ingestion.get_config')
@patch('data.ingestion.requests.get')
@patch('data.ingestion.validate_config')
def test_aggregate_satellites_success(
    mock_validate, 
    mock_get, 
    mock_config, 
    mock_verified_yaml,
    tmp_path
):
    """Test successful aggregation of two satellites."""
    # Setup mocks
    mock_config.return_value.paths = {'verified_datasets': mock_verified_yaml, 'data_raw': str(tmp_path)}
    mock_validate.return_value = {'verified_datasets_path': mock_verified_yaml}
    
    # Mock response for LAGEOS
    lageos_content = b"2023-01-01 12:00:00 100.0 0.05 1\n2023-01-01 12:01:00 100.1 0.04 1\n"
    mock_lageos_resp = MagicMock()
    mock_lageos_resp.status_code = 200
    mock_lageos_resp.content = lageos_content
    
    # Mock response for STARLETTE
    starlette_content = b"2023-01-01 12:00:00 200.0 0.06 1\n"
    mock_starlette_resp = MagicMock()
    mock_starlette_resp.status_code = 200
    mock_starlette_resp.content = starlette_content
    
    # Configure side_effect to return different responses based on URL
    def get_side_effect(url, **kwargs):
        if 'lageos' in url:
            return mock_lageos_resp
        elif 'starlette' in url:
            return mock_starlette_resp
        else:
            raise ValueError(f"Unexpected URL: {url}")
    
    mock_get.side_effect = get_side_effect
    
    # Run function
    result = aggregate_satellites(['LAGEOS', 'STARLETTE'])
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert set(result['satellite_id'].unique()) == {'LAGEOS', 'STARLETTE'}
    assert 'timestamp' in result.columns
    assert 'range_m' in result.columns
    assert 'residual_m' in result.columns
    assert result['satellite_id'].tolist().count('LAGEOS') == 2
    assert result['satellite_id'].tolist().count('STARLETTE') == 1

@patch('data.ingestion.get_config')
@patch('data.ingestion.requests.get')
@patch('data.ingestion.validate_config')
def test_aggregate_satellites_missing_file(
    mock_validate, 
    mock_get, 
    mock_config,
    tmp_path
):
    """Test that aggregate_satellites raises DataIngestionError if config file is missing."""
    mock_config.return_value.paths = {'verified_datasets': '/nonexistent.yaml', 'data_raw': str(tmp_path)}
    mock_validate.side_effect = DataIngestionError("Config file missing")
    
    with pytest.raises(DataIngestionError):
        aggregate_satellites(['LAGEOS'])

@patch('data.ingestion.get_config')
@patch('data.ingestion.requests.get')
@patch('data.ingestion.validate_config')
def test_aggregate_satellites_fetch_failure(
    mock_validate, 
    mock_get, 
    mock_config, 
    mock_verified_yaml,
    tmp_path
):
    """Test handling of fetch failure (403 or timeout)."""
    mock_config.return_value.paths = {'verified_datasets': mock_verified_yaml, 'data_raw': str(tmp_path)}
    mock_validate.return_value = {'verified_datasets_path': mock_verified_yaml}
    
    # Mock a 403 response
    mock_fail_resp = MagicMock()
    mock_fail_resp.status_code = 403
    mock_get.return_value = mock_fail_resp
    
    with pytest.raises(DataIngestionError):
        aggregate_satellites(['LAGEOS'])

@patch('data.ingestion.get_config')
@patch('data.ingestion.requests.get')
@patch('data.ingestion.validate_config')
def test_aggregate_satellites_empty_result(
    mock_validate, 
    mock_get, 
    mock_config, 
    mock_verified_yaml,
    tmp_path
):
    """Test handling of empty data file."""
    mock_config.return_value.paths = {'verified_datasets': mock_verified_yaml, 'data_raw': str(tmp_path)}
    mock_validate.return_value = {'verified_datasets_path': mock_verified_yaml}
    
    # Mock empty content
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"" # Empty file
    mock_get.return_value = mock_resp
    
    with pytest.raises(DataIngestionError, match="No data points were aggregated"):
        aggregate_satellites(['LAGEOS'])