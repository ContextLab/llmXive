"""
Unit tests for the EDA Report Generator.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock config to avoid needing real .env or path setup in unit tests
@pytest.fixture(autouse=True)
def mock_config():
    with patch('code.reports.eda_report_generator.get_path') as mock_get_path:
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Setup mock return values for expected paths
            def side_effect(*args):
                return tmp_path.joinpath(*args)
            
            mock_get_path.side_effect = side_effect
            yield tmp_path

def test_load_correlation_matrix_from_json(mock_config):
    """Test loading correlation matrix from JSON file."""
    from code.reports.eda_report_generator import load_correlation_matrix
    
    # Create a dummy JSON file
    json_path = mock_config / "data" / "results" / "correlation_matrix.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    dummy_data = {
        "building_density": {"temperature": 0.75},
        "tree_cover": {"temperature": -0.60}
    }
    
    with open(json_path, 'w') as f:
        json.dump(dummy_data, f)
    
    result = load_correlation_matrix()
    assert result is not None
    assert result["building_density"]["temperature"] == 0.75

def test_load_correlation_matrix_from_csv(mock_config):
    """Test loading correlation matrix from CSV file."""
    from code.reports.eda_report_generator import load_correlation_matrix
    
    # Create a dummy CSV file
    csv_path = mock_config / "data" / "results" / "correlation_matrix.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    dummy_csv = """variable,temperature,building_density
    building_density,0.75,1.0
    tree_cover,-0.60,0.2
    """
    
    with open(csv_path, 'w') as f:
        f.write(dummy_csv)
    
    result = load_correlation_matrix()
    assert result is not None
    # Check if the structure is parsed correctly (simplified check)
    assert "building_density" in result

def test_load_correlation_matrix_missing(mock_config):
    """Test behavior when correlation matrix file is missing."""
    from code.reports.eda_report_generator import load_correlation_matrix
    
    result = load_correlation_matrix()
    assert result is None

def test_load_spatial_stats(mock_config):
    """Test loading spatial stats."""
    from code.reports.eda_report_generator import load_spatial_stats
    
    json_path = mock_config / "data" / "results" / "spatial_stats.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    dummy_data = {
        "moran_i": {"statistic": 0.45, "p_value": 0.001},
        "variogram": {"nugget": 0.1, "sill": 1.0, "range": 500}
    }
    
    with open(json_path, 'w') as f:
        json.dump(dummy_data, f)
    
    result = load_spatial_stats()
    assert result is not None
    assert result["moran_i"]["statistic"] == 0.45

def test_check_socioeconomic_proxies_missing(mock_config):
    """Test proxy check when files are missing."""
    from code.reports.eda_report_generator import check_socioeconomic_proxies
    
    result = check_socioeconomic_proxies()
    assert result["worldpop"]["status"] == "missing"
    assert len(result["limitations"]) == 2

def test_check_socioeconomic_proxies_available(mock_config):
    """Test proxy check when files exist."""
    from code.reports.eda_report_generator import check_socioeconomic_proxies
    
    # Create dummy proxy files
    (mock_config / "data" / "processed" / "worldpop_density.tif").parent.mkdir(parents=True, exist_ok=True)
    (mock_config / "data" / "processed" / "worldpop_density.tif").touch()
    (mock_config / "data" / "processed" / "osm_building_height.tif").touch()
    
    result = check_socioeconomic_proxies()
    assert result["worldpop"]["status"] == "available"
    assert result["osm_height"]["status"] == "available"
    assert len(result["limitations"]) == 0

def test_generate_report_content(mock_config):
    """Test report content generation."""
    from code.reports.eda_report_generator import generate_report_content
    
    corr = {"building_density": {"temperature": 0.75}}
    spatial = {"moran_i": {"statistic": 0.5, "p_value": 0.01}, "variogram": {}}
    proxy = {"worldpop": {"status": "missing"}, "osm_height": {"status": "missing"}, "limitations": ["No data"]}
    
    content = generate_report_content(corr, spatial, proxy)
    
    assert "EDA Summary Report" in content
    assert "building_density" in content
    assert "0.75" in content
    assert "Moran's I" in content
    assert "No data" in content

def test_main_integration(mock_config):
    """Test the main function integration."""
    from code.reports.eda_report_generator import main
    
    # Setup dummy files for main to read
    (mock_config / "data" / "results").mkdir(parents=True, exist_ok=True)
    (mock_config / "data" / "results" / "correlation_matrix.json").write_text('{"var": {"temp": 0.5}}')
    (mock_config / "data" / "results" / "spatial_stats.json").write_text('{"moran_i": {"statistic": 0.1, "p_value": 0.5}}')
    
    output_path = main()
    
    assert output_path.exists()
    content = output_path.read_text()
    assert "EDA Summary Report" in content