"""
Tests for the Collinearity Analysis module (T023).
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import sys

# Mock the config to avoid dependency on actual file structure in tests
from unittest.mock import patch, MagicMock

# Import the function to test
# We need to import from the module, but since it's in code/models, we add path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))

from models.collinearity_analysis import (
    load_final_dataset,
    calculate_vif_for_features,
    generate_collinearity_report,
    VIF_THRESHOLD
)

@pytest.fixture
def mock_dataframe():
    """Create a mock dataframe with some collinearity."""
    data = {
        'rdf_peak_pos': [1.0, 2.0, 3.0, 4.0, 5.0],
        'rdf_peak_width': [0.1, 0.2, 0.3, 0.4, 0.5],
        'bond_angle_variance': [10.0, 20.0, 30.0, 40.0, 50.0],
        'coordination_numbers': [4, 5, 6, 7, 8],
        'Tg_exp': [300, 310, 320, 330, 340]
    }
    # Add a highly correlated feature to test flagging
    # rdf_peak_pos * 2 + noise
    data['highly_correlated_feature'] = [2.0, 4.0, 6.0, 8.0, 10.0]
    
    df = pd.DataFrame(data)
    return df

def test_calculate_vif_for_features_basic(mock_dataframe):
    """Test basic VIF calculation."""
    features = ['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance']
    results = calculate_vif_for_features(mock_dataframe, features)
    
    assert len(results) == 3
    for res in results:
        assert 'feature' in res
        assert 'vif' in res
        assert 'flagged' in res
        assert isinstance(res['vif'], float)
        assert res['vif'] >= 1.0  # VIF is always >= 1

def test_calculate_vif_for_features_collinearity(mock_dataframe):
    """Test that collinearity is detected."""
    # Include the highly correlated feature
    features = ['rdf_peak_pos', 'highly_correlated_feature']
    results = calculate_vif_for_features(mock_dataframe, features)
    
    # One of these should have a very high VIF (theoretically infinite for perfect collinearity)
    # In practice, with 5 points, it might be large but finite
    max_vif = max(r['vif'] for r in results)
    assert max_vif > 5.0, f"Expected high VIF for collinear features, got {max_vif}"

def test_generate_collinearity_report(mock_dataframe, tmp_path):
    """Test report generation and file creation."""
    output_path = tmp_path / "test_report.json"
    report = generate_collinearity_report(mock_dataframe, output_path)
    
    # Check file exists
    assert output_path.exists()
    
    # Check report structure
    assert 'analysis_params' in report
    assert 'summary' in report
    assert 'results' in report
    assert report['analysis_params']['vif_threshold'] == VIF_THRESHOLD
    assert len(report['results']) == len(mock_dataframe.columns) - 1 # Exclude Tg_exp if not in list, but we pass specific list in main
    
    # Check JSON validity
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == report

def test_vif_threshold_logic(mock_dataframe, tmp_path):
    """Test that the flagged boolean is correctly set based on threshold."""
    # Create data with known VIF
    # We can't easily force a specific VIF without complex math, 
    # but we can check the logic: if vif > threshold, flagged=True
    features = ['rdf_peak_pos', 'rdf_peak_width']
    results = calculate_vif_for_features(mock_dataframe, features)
    
    for res in results:
        if res['vif'] > VIF_THRESHOLD:
            assert res['flagged'] is True
        else:
            assert res['flagged'] is False

def test_empty_dataframe_handling():
    """Test handling of empty dataframe."""
    empty_df = pd.DataFrame(columns=['A', 'B'])
    with pytest.raises(ValueError, match="No valid data"):
        calculate_vif_for_features(empty_df, ['A', 'B'])

def test_nan_handling():
    """Test that NaN values are handled (dropped)."""
    data = {
        'A': [1.0, 2.0, np.nan, 4.0],
        'B': [1.0, 2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    # Should not raise, but drop the NaN row
    results = calculate_vif_for_features(df, ['A', 'B'])
    assert len(results) == 2
    # Check that calculation succeeded on remaining rows
    for res in results:
        assert not np.isnan(res['vif'])
