import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from modeling import run_sensitivity_analysis_crosslinker_proxy, load_processed_data

@pytest.fixture
def mock_processed_data():
    """Create mock processed data."""
    data = {
        'adhesion_strength': [10.0, 12.0, 15.0, 18.0, 20.0],
        'comp_feature_1': [0.1, 0.2, 0.3, 0.4, 0.5],
        'comp_feature_2': [0.5, 0.4, 0.3, 0.2, 0.1],
        'roughness': [1.0, 1.5, 2.0, 2.5, 3.0],
        'skewness': [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    return pd.DataFrame(data)

@patch('modeling.load_processed_data')
@patch('modeling.train_gradient_boosting')
def test_run_sensitivity_analysis(mock_train_gb, mock_load_data, mock_processed_data):
    """Test sensitivity analysis generates report with correct columns."""
    # Setup mocks
    mock_load_data.return_value = mock_processed_data
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([10.5, 12.5, 15.5, 18.5, 20.5])
    mock_train_gb.return_value = (mock_model, 0.85)
    
    # Run function
    report = run_sensitivity_analysis_crosslinker_proxy()
    
    # Verify report structure
    assert report is not None
    assert 'definition' in report.columns
    assert 'model_r2' in report.columns
    assert 'model_rmse' in report.columns
    assert 'variance' in report.columns
    assert len(report) == 3  # 3 definitions

def test_load_processed_data_missing_file():
    """Test loading data when file doesn't exist."""
    with patch('os.path.exists', return_value=False):
        result = load_processed_data()
        assert result is None

@patch('modeling.load_processed_data')
@patch('modeling.train_gradient_boosting')
def test_sensitivity_report_file_created(mock_train_gb, mock_load_data, mock_processed_data, tmp_path):
    """Test that sensitivity report CSV is actually written to disk."""
    # Setup mocks
    mock_load_data.return_value = mock_processed_data
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([10.5, 12.5, 15.5, 18.5, 20.5])
    mock_train_gb.return_value = (mock_model, 0.85)
    
    # Temporarily change output directory for testing
    original_dir = "data/processed"
    test_dir = str(tmp_path / "data" / "processed")
    os.makedirs(test_dir, exist_ok=True)
    
    with patch('modeling.DATA_PROCESSED_DIR', test_dir):
        run_sensitivity_analysis_crosslinker_proxy()
        
        # Verify file exists
        report_path = os.path.join(test_dir, "crosslinker_sensitivity_report.csv")
        assert os.path.exists(report_path)
        
        # Verify content
        df = pd.read_csv(report_path)
        assert 'definition' in df.columns
        assert 'model_r2' in df.columns
        assert 'model_rmse' in df.columns
        assert 'variance' in df.columns
        assert len(df) == 3