"""
Tests for Model Training Module (T015).
Verifies LOCO CV logic, model training, and artifact generation.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# We need to mock the environment and data loading to avoid requiring real data files
# which might not exist in the test environment yet.
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor

# Mock imports for project config
@pytest.fixture
def mock_env_vars():
    """Mock environment variables for data paths."""
    with patch.dict(os.environ, {
        "PROJECT_ROOT": tempfile.gettempdir(),
        "DATA_ROOT": tempfile.gettempdir()
    }):
        yield

@pytest.fixture
def mock_preprocessed_data():
    """Generate mock preprocessed data for testing."""
    n_cycles = 3
    n_per_cycle = 50
    data = []
    for c in range(1, n_cycles + 1):
        gsn_vals = np.random.uniform(0, 100, n_per_cycle)
        # TSI roughly correlates with GSN + noise
        tsi_vals = 1361.0 + (gsn_vals * 0.01) + np.random.normal(0, 0.1, n_per_cycle)
        for i in range(n_per_cycle):
            data.append({
                "date": f"2000-{c:02d}-01",
                "gsn": gsn_vals[i],
                "tsi": tsi_vals[i],
                "cycle_id": c
            })
    return pd.DataFrame(data)

def test_loco_cv_logic(mock_env_vars, mock_preprocessed_data):
    """
    Test that LOCO CV correctly holds out one cycle at a time.
    We patch the training functions to count calls and verify splits.
    """
    from code.models.train import run_loco_cv, prepare_features

    X, y = prepare_features(mock_preprocessed_data)
    unique_cycles = sorted(X['cycle_id'].unique())
    
    # Run the logic
    # We expect the function to iterate over unique_cycles
    # Since we can't easily mock the internal training calls without breaking the flow,
    # we verify the structure of the output.
    
    # Note: run_loco_cv calls real sklearn models. For a pure unit test, we might mock train_random_forest.
    # But for integration-style test of logic, we let it run on small mock data.
    
    # Patching the training functions to return dummy models to speed up and verify logic
    with patch('code.models.train.train_random_forest') as mock_rf, \
         patch('code.models.train.train_gaussian_process') as mock_gp:
        
        mock_rf.return_value.predict.return_value = np.ones(len(X)) # Dummy prediction
        mock_gp.return_value.predict.return_value = np.ones(len(X))
        
        report, winner = run_loco_cv(X, y)
        
        # Verify report structure
        assert "per_cycle_metrics" in report
        assert len(report["per_cycle_metrics"]) == len(unique_cycles)
        assert "model_comparison" in report
        assert "random_forest" in report["model_comparison"]
        assert "gaussian_process" in report["model_comparison"]
        assert "selection_rationale" in report
        
        # Verify each cycle was held out
        held_out_ids = [m['cycle_id'] for m in report["per_cycle_metrics"]]
        assert set(held_out_ids) == set(unique_cycles)

def test_save_report(mock_env_vars):
    """Test that the report is saved to the correct JSON path."""
    from code.models.train import save_report
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override get_data_path to use temp dir
        with patch('code.models.train.get_data_path', return_value=tmpdir):
            test_report = {"test": "data", "cycles": 3}
            output_path = "data/processed/cv_report.json"
            
            save_report(test_report, output_path)
            
            expected_file = Path(tmpdir) / output_path
            assert expected_file.exists()
            
            with open(expected_file) as f:
                loaded = json.load(f)
            assert loaded == test_report

def test_prepare_features_validation(mock_env_vars):
    """Test that prepare_features raises error on missing columns."""
    from code.models.train import prepare_features
    
    df_missing = pd.DataFrame({"gsn": [1, 2], "tsi": [3, 4]}) # Missing cycle_id
    
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_features(df_missing)

def test_model_training_functions(mock_env_vars, mock_preprocessed_data):
    """Test that model training functions return correct model types."""
    from code.models.train import train_random_forest, train_gaussian_process, prepare_features
    
    X, y = prepare_features(mock_preprocessed_data)
    
    rf_model = train_random_forest(X, y)
    assert isinstance(rf_model, RandomForestRegressor)
    assert rf_model.n_estimators == 100
    assert rf_model.max_depth == 10
    
    gp_model = train_gaussian_process(X, y)
    assert isinstance(gp_model, GaussianProcessRegressor)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])