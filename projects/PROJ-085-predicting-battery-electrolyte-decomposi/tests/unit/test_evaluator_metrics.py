import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.evaluator import calculate_internal_metrics, load_model_artifacts, load_heldout_data

@pytest.fixture
def mock_model_artifacts():
    return {
        "model_type": "RandomForestRegressor",
        "params": {
            "n_estimators": 10,
            "max_depth": 5,
            "random_state": 42
        },
        "cv_score": 0.85
    }

@pytest.fixture
def mock_heldout_data():
    # Create a small synthetic dataset for testing the calculation logic
    # Note: This is for unit testing the metric calculation function, not the data source.
    # The function itself is expected to load REAL data in production.
    data = {
        "molecule_id": ["M1", "M2", "M3", "M4", "M5"],
        "feature_a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feature_b": [5.0, 4.0, 3.0, 2.0, 1.0],
        "target": [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_full_features(tmp_path):
    # Create a mock full features file to allow re-splitting
    data = {
        "molecule_id": [f"M{i}" for i in range(1, 11)],
        "feature_a": list(range(1, 11)),
        "feature_b": list(range(10, 0, -1)),
        "target": [i * 10 for i in range(1, 11)],
        "split": ["train"] * 8 + ["test"] * 2 # Last 2 are test
    }
    df = pd.DataFrame(data)
    path = tmp_path / "electrolyte_features.csv"
    df.to_csv(path, index=False)
    return path

def test_calculate_internal_metrics(mock_model_artifacts, mock_heldout_data, mock_full_features, tmp_path):
    """
    Test that the metric calculation function correctly:
    1. Loads the model parameters.
    2. Reconstructs the training set (by filtering heldout IDs or using split column).
    3. Trains the model.
    4. Predicts on heldout.
    5. Returns MAE and R2.
    """
    # Mock the config to point to our temp directory
    import config
    original_processed_dir = config.get_processed_dir()
    
    # We need to temporarily change the processed dir to our temp path
    # But the function loads from config. Let's mock the config functions or the file system.
    # Easier: Create the files in the temp path and patch the config or pass paths?
    # The function uses global config. We will patch the get_processed_dir function.
    
    # Actually, let's just test the calculation logic directly with the data passed in,
    # assuming the file loading parts are mocked or the paths are correct.
    # Since we can't easily patch the global config in the imported module without side effects,
    # we will rely on the fact that the function loads files.
    
    # Setup: Create the full features file in the temp path
    # The function expects data/processed/electrolyte_features.csv
    # We will create a temporary directory structure that mimics the project
    
    # To avoid complex mocking of config, we will assume the test environment
    # has the files set up, or we patch the function.
    # Let's patch the file reading inside the function? No, too invasive.
    
    # Better approach for this unit test:
    # We assume the files exist in the expected location for the test to run.
    # But since we are providing a self-contained test, we will mock the file existence.
    
    # Let's just test the logic of the calculation assuming we have the data.
    # We will create a version of the function that accepts data paths or mock the config.
    
    # For the purpose of this task, we verify the function signature and basic execution
    # by ensuring it doesn't crash with valid inputs if we were to inject them.
    # However, the requirement is to test the REAL implementation.
    
    # Let's create the necessary files in a temporary directory and update the config.
    # But config is imported at the top.
    
    # Alternative: We test the logic by creating a mock of the file system.
    from unittest.mock import patch, MagicMock
    
    # Create a mock for the full data
    full_data = pd.read_csv(mock_full_features)
    heldout_data = mock_heldout_data
    
    # We need to simulate the file paths
    with patch('models.evaluator.get_processed_dir') as mock_get_dir:
        mock_dir = MagicMock()
        mock_dir.__truediv__ = lambda self, name: Path(tmp_path) / name
        mock_get_dir.return_value = mock_dir
        
        # Also need to patch the file reading to return our mock data
        # The function reads 'electrolyte_features.csv' and 'electrolyte_heldout.csv'
        # We already have heldout_data, but the function loads it.
        # We will patch pd.read_csv
        
        def mock_read_csv(path, *args, **kwargs):
            if 'electrolyte_heldout.csv' in str(path):
                return heldout_data
            elif 'electrolyte_features.csv' in str(path):
                return full_data
            else:
                return pd.read_csv(path, *args, **kwargs)
        
        with patch('models.evaluator.pd.read_csv', side_effect=mock_read_csv):
            # Also need to mock the model artifact loading
            with patch('models.evaluator.load_model_artifacts', return_value=mock_model_artifacts):
                try:
                    result = calculate_internal_metrics(mock_model_artifacts, heldout_data)
                    
                    # Assertions
                    assert "mae" in result
                    assert "r2" in result
                    assert "deviation_note" in result
                    assert "Internal Consistency" in result["metric_type"]
                    assert "Experimental MAE" in result["deviation_note"]
                    
                    # Check that MAE and R2 are numbers
                    assert isinstance(result["mae"], float)
                    assert isinstance(result["r2"], float)
                    
                    print(f"Test passed. MAE: {result['mae']}, R2: {result['r2']}")
                except Exception as e:
                    pytest.fail(f"Metric calculation failed: {e}")

def test_load_model_artifacts_missing_file(tmp_path):
    """Test that FileNotFoundError is raised if model_run.json is missing."""
    # Create a temporary directory with no model_run.json
    with patch('models.evaluator.get_processed_dir') as mock_get_dir:
        mock_dir = MagicMock()
        mock_dir.__truediv__ = lambda self, name: Path(tmp_path) / name
        mock_get_dir.return_value = mock_dir
        
        with pytest.raises(FileNotFoundError, match="Model artifacts not found"):
            load_model_artifacts()
