import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.evaluator import calculate_internal_metrics, load_model_artifacts, load_heldout_data
from config import get_processed_dir, get_validation_dir

@pytest.fixture
def mock_model_artifacts():
    """Mock model artifacts as expected from T026."""
    return {
        "feature_names": ["homo", "lumo", "gap", "bond_length_1"],
        "model_params": {"n_estimators": 100},
        "predictions": [1.0, 2.0, 3.0, 4.0, 5.0]
    }

@pytest.fixture
def mock_heldout_data(mock_model_artifacts):
    """Mock held-out data DataFrame."""
    data = {
        "homo": [1.1, 2.1, 3.1, 4.1, 5.1],
        "lumo": [0.5, 1.5, 2.5, 3.5, 4.5],
        "gap": [0.6, 0.6, 0.6, 0.6, 0.6],
        "bond_length_1": [1.0, 1.1, 1.2, 1.3, 1.4],
        "E_decomp": [0.9, 1.9, 2.9, 3.9, 4.9]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary processed directory structure for testing."""
    # We need to mock the config or set the environment variables
    # Since config.py uses get_project_root, we assume the test runs in a context
    # where we can override or the temp_dir is set up correctly.
    # For this unit test, we test the logic functions directly with data,
    # avoiding file system dependencies unless necessary.
    return tmp_path

def test_calculate_internal_metrics_basic(mock_model_artifacts, mock_heldout_data):
    """Test basic calculation of MAE and R²."""
    result = calculate_internal_metrics(mock_model_artifacts, mock_heldout_data)
    
    assert "mae" in result
    assert "r2" in result
    assert result["metric_label"] == "Internal Consistency MAE"
    assert "deviation_note" in result
    
    # Check MAE is reasonable (predictions are close to targets)
    # Pred: [1, 2, 3, 4, 5], True: [0.9, 1.9, 2.9, 3.9, 4.9]
    # Errors: [0.1, 0.1, 0.1, 0.1, 0.1] -> MAE = 0.1
    assert abs(result["mae"] - 0.1) < 1e-6
    
    # Check R² is high (perfect linear relationship with small offset)
    assert result["r2"] > 0.99

def test_calculate_internal_metrics_missing_features(mock_model_artifacts, mock_heldout_data, caplog):
    """Test handling of missing features in heldout data."""
    # Remove a feature from the mock data
    del mock_heldout_data["bond_length_1"]
    
    # Should log a warning but still run with available features
    result = calculate_internal_metrics(mock_model_artifacts, mock_heldout_data)
    
    assert "mae" in result
    assert "r2" in result
    # The function should have logged a warning
    assert any("Missing features" in record.message for record in caplog.records)

def test_calculate_internal_metrics_length_mismatch(mock_model_artifacts, mock_heldout_data):
    """Test error handling for prediction/label length mismatch."""
    # Truncate predictions
    mock_model_artifacts["predictions"] = mock_model_artifacts["predictions"][:3]
    
    with pytest.raises(ValueError, match="Prediction length mismatch"):
        calculate_internal_metrics(mock_model_artifacts, mock_heldout_data)

def test_internal_validation_deviation_note(mock_model_artifacts, mock_heldout_data):
    """Verify the deviation note is present in the result."""
    result = calculate_internal_metrics(mock_model_artifacts, mock_heldout_data)
    
    assert "Experimental MAE" in result["deviation_note"]
    assert "data gap" in result["deviation_note"]

# Note: We do not test file I/O (load_model_artifacts, load_heldout_data) here
# because they depend on the project's directory structure which is managed by T026/T018.
# Integration tests in tests/integration/test_evaluator.py should cover file loading.
