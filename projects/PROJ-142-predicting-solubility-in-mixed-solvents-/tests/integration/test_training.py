import os
import sys
import json
import pickle
import pytest
from pathlib import Path

# Ensure project root is in path for imports if running via pytest directly
# Adjust based on how the project is structured (usually parent of 'tests')
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.constants import DATA_DIR

def test_training_sample():
    """
    Integration test for the training pipeline (T020).
    
    Validates that the training script (T021) produces the expected artifacts
    with the correct structure and metrics.
    
    Input: data/processed/solubility_features.csv (produced by T018)
    Expected Artifact: data/artifacts/trained_models.pkl
    Expected Metrics: data/artifacts/evaluation_metrics.json
    """
    artifacts_dir = DATA_DIR / "artifacts"
    processed_dir = DATA_DIR / "processed"
    
    # 1. Verify Input Data Exists (Dependency T018)
    # Note: T018 was flagged as needing redo, so we verify the file exists before proceeding.
    features_path = processed_dir / "solubility_features.csv"
    assert features_path.exists(), f"Input data file {features_path} not found. T018 must be completed successfully."
    
    # 2. Verify Trained Models Artifact Exists (Output of T021)
    models_path = artifacts_dir / "trained_models.pkl"
    assert models_path.exists(), f"Trained models artifact {models_path} not found. T021 must be completed."
    
    # 3. Load and Validate Models Artifact Structure
    with open(models_path, "rb") as f:
        models_data = pickle.load(f)
    
    required_keys = ["xgboost_model", "rf_model", "abraham_model", "metrics"]
    for key in required_keys:
        assert key in models_data, f"Missing required key '{key}' in {models_path}"
    
    # 4. Verify Evaluation Metrics Artifact (Output of T023)
    metrics_path = artifacts_dir / "evaluation_metrics.json"
    assert metrics_path.exists(), f"Evaluation metrics file {metrics_path} not found. T023 must be completed."
    
    with open(metrics_path, "r") as f:
        metrics_data = json.load(f)
    
    # 5. Validate Metrics Schema
    # The task requires verification of 'rmse' and 'r2' in the metrics.
    # We expect these to be present, likely at the top level or within a specific model's results.
    # Based on T023 description: "Write metrics to data/artifacts/evaluation_metrics.json"
    # and T024 description: "Compare ['abs_error_xgboost', 'abs_error_abraham'] from evaluation_metrics.json"
    # We check for the presence of RMSE and R2 keys.
    
    found_rmse = False
    found_r2 = False
    
    def check_metrics_recursive(d):
        nonlocal found_rmse, found_r2
        if isinstance(d, dict):
            if "rmse" in d: found_rmse = True
            if "r2" in d: found_r2 = True
            for v in d.values():
                check_metrics_recursive(v)
        elif isinstance(d, list):
            for item in d:
                check_metrics_recursive(item)
    
    check_metrics_recursive(metrics_data)
    
    assert found_rmse, "Evaluation metrics must contain 'rmse' values."
    assert found_r2, "Evaluation metrics must contain 'r2' values."
    
    # 6. Optional: Verify models are not None/empty (basic sanity check)
    assert models_data["xgboost_model"] is not None, "XGBoost model is None"
    assert models_data["rf_model"] is not None, "Random Forest model is None"
    assert models_data["abraham_model"] is not None, "Abraham model is None"
    
    # If we reach here, the integration test passes
    assert True