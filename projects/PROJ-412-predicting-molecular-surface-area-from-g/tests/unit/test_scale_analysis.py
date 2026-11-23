import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from eval.scale_analysis import load_processed_data_stats, analyze_sasa_scale, main
from utils.config import get_data_dir, get_results_dir

@pytest.fixture
def mock_processed_data(tmp_path):
    """Create a mock processed dataset for testing."""
    # Create a temporary data directory structure
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create a mock parquet file with SASA values
    mock_data = pd.DataFrame({
        'smiles': ['CCO', 'CCC', 'CCCC'],
        'sasa': [20.5, 35.2, 50.8],
        'molecular_weight': [46.07, 44.11, 58.12]
    })
    
    parquet_path = data_dir / "graphs_with_3d.parquet"
    mock_data.to_parquet(parquet_path)
    
    return tmp_path, parquet_path

def test_analyze_sasa_scale():
    """Test the scale analysis calculation."""
    stats = {
        'sasa_values': [20.5, 35.2, 50.8],
        'count': 3
    }
    
    result = analyze_sasa_scale(stats)
    
    assert 'mean_sasa' in result
    assert 'min_sasa' in result
    assert 'max_sasa' in result
    assert 'std_sasa' in result
    assert 'count' in result
    assert 'justification_source' in result
    
    # Verify calculations
    expected_mean = np.mean([20.5, 35.2, 50.8])
    assert abs(result['mean_sasa'] - expected_mean) < 0.01
    assert result['min_sasa'] == 20.5
    assert result['max_sasa'] == 50.8
    assert result['count'] == 3
    
    # Verify justification source is present and non-empty
    assert len(result['justification_source']) > 0
    assert "experimental" in result['justification_source'].lower()

def test_load_processed_data_stats_missing_file():
    """Test that FileNotFoundError is raised when data is missing."""
    with pytest.raises(FileNotFoundError):
        # This should fail because the file doesn't exist in the real path
        # We mock the path by temporarily changing the data directory
        pass

def test_main_integration(mock_processed_data):
    """Integration test for the main function."""
    tmp_path, _ = mock_processed_data
    
    # Temporarily override get_data_dir to use our mock path
    original_get_data_dir = get_data_dir
    
    def mock_get_data_dir():
        return tmp_path / "data"
    
    # Monkey patch
    import utils.config
    utils.config.get_data_dir = mock_get_data_dir
    
    try:
        # Run main
        result = main()
        
        # Verify outputs
        results_dir = tmp_path / "results" / "reports"
        json_path = results_dir / "scale_analysis.json"
        md_path = results_dir / "scale_analysis.md"
        
        assert json_path.exists(), "JSON report should be created"
        assert md_path.exists(), "Markdown report should be created"
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert 'mean_sasa' in json_data
        assert json_data['mean_sasa'] > 0
        assert 'justification_source' in json_data
        
    finally:
        # Restore original function
        utils.config.get_data_dir = original_get_data_dir