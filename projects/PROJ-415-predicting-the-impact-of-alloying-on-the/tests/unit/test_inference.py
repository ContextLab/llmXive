import os
import json
import tempfile
import pickle
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.models.inference import evaluate_model, run_inference

def test_evaluate_model():
    """Test the evaluate_model function with mock data."""
    # Create a simple mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1.0, 2.0, 3.0, 4.0])
    
    X_test = pd.DataFrame({'a': [1, 2, 3, 4], 'b': [5, 6, 7, 8]})
    y_test = pd.Series([1.1, 2.1, 2.9, 4.2])
    
    metrics = evaluate_model(mock_model, X_test, y_test)
    
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics
    assert isinstance(metrics["r2"], float)
    
    # Verify calculation manually for one value
    expected_r2 = r2_score(y_test, mock_model.predict.return_value)
    assert abs(metrics["r2"] - expected_r2) < 1e-5

def test_run_inference_file_structure(tmp_path):
    """
    Test that run_inference creates the expected output file structure
    when models and data are present.
    """
    # Setup temporary directories
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    data_dir = tmp_path / "data" / "curated"
    data_dir.mkdir(parents=True)
    
    # Create dummy curated data
    dummy_data = pd.DataFrame({
        'solute_symbol': ['Cu', 'Zn', 'Ni', 'Fe', 'Co', 'Ag', 'Au', 'Pd'],
        'host_symbol': ['Cu', 'Cu', 'Cu', 'Cu', 'Cu', 'Cu', 'Cu', 'Cu'],
        'activation_energy_eV': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
    })
    dummy_data.to_csv(data_dir / "filtered.csv", index=False)
    
    # Create dummy models
    rf_model = RandomForestRegressor(n_estimators=10, random_state=42)
    rf_model.fit(dummy_data[['solute_symbol', 'host_symbol']].astype(str), dummy_data['activation_energy_eV']) # dummy fit
    # Actually, we need numeric features for the real test, but for file creation test:
    # We will patch the prepare_test_data to return numeric data
    
    # Patch paths
    with patch('code.models.inference.MODELS_DIR', models_dir), \
         patch('code.models.inference.DATA_DIR', tmp_path / "data"), \
         patch('code.models.inference.RANDOM_SEED', 42):
         
         # Create a mock for prepare_test_data that returns numeric data
         mock_X_test = pd.DataFrame({'size_mismatch': [0.1, 0.2, 0.3], 'electronegativity_diff': [0.1, 0.2, 0.3]})
         mock_y_test = pd.Series([0.5, 0.6, 0.7])
         
         # Train a real model on dummy numeric data to save it
         real_X = pd.DataFrame({'size_mismatch': [0.1, 0.2, 0.3, 0.4, 0.5], 'electronegativity_diff': [0.1, 0.2, 0.3, 0.4, 0.5]})
         real_y = pd.Series([0.5, 0.6, 0.7, 0.8, 0.9])
         rf_model = RandomForestRegressor(n_estimators=5, random_state=42)
         rf_model.fit(real_X, real_y)
         
         gb_model = GradientBoostingRegressor(n_estimators=5, random_state=42)
         gb_model.fit(real_X, real_y)
         
         with open(models_dir / "final_rf.pkl", 'wb') as f:
             pickle.dump(rf_model, f)
         with open(models_dir / "final_gb.pkl", 'wb') as f:
             pickle.dump(gb_model, f)
         
         with patch('code.models.inference.prepare_test_data', return_value=(mock_X_test, mock_y_test)):
             run_inference()
         
         # Check output
         metrics_path = models_dir / "metrics.json"
         assert metrics_path.exists(), "metrics.json was not created"
         
         with open(metrics_path) as f:
             data = json.load(f)
         
         assert "random_forest" in data
         assert "gradient_boosting" in data
         assert "r2" in data["random_forest"]
         assert "rmse" in data["random_forest"]
         assert "mae" in data["random_forest"]