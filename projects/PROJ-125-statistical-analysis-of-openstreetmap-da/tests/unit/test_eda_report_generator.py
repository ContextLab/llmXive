"""
Unit tests for the EDA Report Generator.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Mock config to avoid needing real project setup for unit tests
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from reports.eda_report_generator import (
    load_correlation_matrix,
    load_spatial_stats,
    check_socioeconomic_proxies,
    generate_report_content,
    main
)
from utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    results_dir = tmp_path / "data" / "results"
    results_dir.mkdir(parents=True)
    
    # Create mock correlation matrix
    corr_df = pd.DataFrame({
        'variable': ['building_density', 'tree_cover', 'road_density'],
        'correlation': [0.65, -0.42, 0.15]
    })
    corr_file = results_dir / "correlation_matrix.csv"
    corr_df.to_csv(corr_file, index=False)

    # Create mock spatial stats
    spatial_data = {
        'moran_i': 0.45,
        'p_value': 0.001,
        'variogram': {
            'sill': 2.5,
            'range': 1200.0,
            'nugget': 0.5
        }
    }
    spatial_file = results_dir / "spatial_stats.json"
    with open(spatial_file, 'w') as f:
        json.dump(spatial_data, f)

    return tmp_path / "data"

@patch('reports.eda_report_generator.get_path')
def test_load_correlation_matrix(mock_get_path, temp_results_dir):
    """Test loading correlation matrix from CSV."""
    mock_get_path.side_effect = lambda p: str(temp_results_dir / p.split("/")[-1])
    
    result = load_correlation_matrix()
    assert result is not None
    assert len(result) == 3
    assert result[0]['variable'] == 'building_density'
    assert abs(result[0]['correlation'] - 0.65) < 0.001

@patch('reports.eda_report_generator.get_path')
def test_load_spatial_stats(mock_get_path, temp_results_dir):
    """Test loading spatial stats from JSON."""
    mock_get_path.side_effect = lambda p: str(temp_results_dir / p.split("/")[-1])
    
    result = load_spatial_stats()
    assert result is not None
    assert result['moran_i'] == 0.45
    assert 'variogram' in result

@patch('reports.eda_report_generator.get_path')
def test_check_socioeconomic_proxies_missing(mock_get_path, temp_results_dir):
    """Test proxy check when data is missing."""
    mock_get_path.return_value = str(temp_results_dir / "non_existent_path")
    
    result = check_socioeconomic_proxies()
    assert result['found'] is False
    assert "No socioeconomic proxy data" in result['details']

def test_generate_report_content():
    """Test report generation with valid data."""
    corr_data = [{'variable': 'test_var', 'correlation': 0.5}]
    spatial_data = {'moran_i': 0.3, 'p_value': 0.05, 'variogram': {}}
    proxy_data = {'found': False, 'details': 'Missing', 'source': None}
    
    report = generate_report_content(corr_data, spatial_data, proxy_data)
    
    assert "Exploratory Data Analysis (EDA) Report" in report
    assert "Socioeconomic Proxy Data Availability" in report
    assert "Missing" in report
    assert "Correlation Analysis" in report
    assert "test_var" in report
    assert "Spatial Autocorrelation" in report

@patch('reports.eda_report_generator.get_path')
@patch('builtins.open')
@patch('reports.eda_report_generator.get_logger')
def test_main(mock_logger, mock_open, mock_get_path, temp_results_dir):
    """Test the main function execution."""
    mock_logger.return_value = logger
    mock_get_path.side_effect = lambda p: str(temp_results_dir / p.split("/")[-1])
    
    # Mock the open context manager
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    main()
    
    # Verify that open was called with the correct path
    assert mock_open.called
    # Verify content was written
    assert mock_file.write.called

@patch('reports.eda_report_generator.get_path')
def test_load_correlation_matrix_missing(mock_get_path):
    """Test handling of missing correlation file."""
    mock_get_path.return_value = "/non/existent/path.csv"
    
    result = load_correlation_matrix()
    assert result is None

@patch('reports.eda_report_generator.get_path')
def test_load_spatial_stats_missing(mock_get_path):
    """Test handling of missing spatial stats file."""
    mock_get_path.return_value = "/non/existent/path.json"
    
    result = load_spatial_stats()
    assert result is None