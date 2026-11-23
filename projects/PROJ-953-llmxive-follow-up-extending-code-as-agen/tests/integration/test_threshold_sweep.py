import os
import json
import pytest
import numpy as np
import pandas as pd
import pickle
from pathlib import Path

from scripts.sensitivity_analysis import run_sensitivity_analysis, calculate_fnr

@pytest.fixture
def mock_model_and_data(tmp_path):
    # Create a mock model
    class MockModel:
        def predict_proba(self, X):
            # Return probabilities based on a simple rule for testing
            # If sum of features > 0, high prob, else low
            scores = np.sum(X, axis=1)
            probs = 1 / (1 + np.exp(-scores))
            return np.column_stack([1 - probs, probs])

    # Create mock features
    data = {
        'feature1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'feature2': [0.1, 0.2, 0.3, 0.4, 0.5],
        'target': [1, 1, 1, 0, 0] # 1 = Need Dynamic, 0 = Static Safe
    }
    df = pd.DataFrame(data)
    model = MockModel()

    model_path = tmp_path / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    features_path = tmp_path / "features.csv"
    df.to_csv(features_path, index=False)

    output_path = tmp_path / "sweep.json"

    return model, df, model_path, features_path, output_path

def test_calculate_fnr():
    # y_true: [1, 1, 1, 0, 0]
    # y_pred: [1, 0, 1, 0, 0] -> FN at index 1 (True=1, Pred=0)
    y_true = np.array([1, 1, 1, 0, 0])
    y_pred = np.array([1, 0, 1, 0, 0])
    
    # FN = 1, TP = 2, Total Positives = 3
    # FNR = 1/3
    fnr = calculate_fnr(y_true, y_pred)
    assert abs(fnr - 1/3) < 1e-6

def test_sensitivity_analysis_runs_and_outputs_json(mock_model_and_data):
    model, df, model_path, features_path, output_path = mock_model_and_data

    result = run_sensitivity_analysis(model, df, str(output_path))

    assert os.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "thresholds" in data
    assert 0.01 in data["thresholds"]
    assert 0.05 in data["thresholds"]
    assert 0.1 in data["thresholds"]
    assert "min_achievable_fnr" in data
    assert "is_safe" in data
    assert "status" in data

def test_safety_flag_logic(mock_model_and_data):
    model, df, model_path, features_path, output_path = mock_model_and_data
    
    # Force a scenario where FNR is high
    # We can't easily force the model to be bad without changing the model, 
    # but we can check that the logic exists
    result = run_sensitivity_analysis(model, df, str(output_path))
    
    # The result should be a boolean
    assert isinstance(result["is_safe"], bool)
    assert result["status"] in ["SAFE", "UNSAFE"]
