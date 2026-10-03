import os
import json
import pytest
from pathlib import Path

def test_metrics_schema_compliance():
    """
    Contract test for reports/metrics/model_performance.json.
    Validates the structure and data types of the model performance metrics.
    """
    file_path = Path("reports/metrics/model_performance.json")
    
    # 1. File existence
    assert file_path.exists(), f"File {file_path} does not exist."
    
    # 2. Load JSON
    with open(file_path, 'r') as f:
        metrics = json.load(f)
    
    # 3. Validate top-level keys
    required_keys = ['traditional', 'topological', 'combined', 'feature_importance']
    for key in required_keys:
        assert key in metrics, f"Missing required top-level key '{key}'."
    
    # 4. Validate structure of each model type
    for model_type in ['traditional', 'topological', 'combined']:
        model_data = metrics[model_type]
        
        # Check required keys for each model
        assert 'r2_per_fold' in model_data, f"Missing 'r2_per_fold' for {model_type}."
        assert 'rmse_per_fold' in model_data, f"Missing 'rmse_per_fold' for {model_type}."
        assert 'r2_mean' in model_data, f"Missing 'r2_mean' for {model_type}."
        assert 'rmse_mean' in model_data, f"Missing 'rmse_mean' for {model_type}."
        
        # Validate types
        assert isinstance(model_data['r2_per_fold'], list), f"'r2_per_fold' must be a list for {model_type}."
        assert isinstance(model_data['rmse_per_fold'], list), f"'rmse_per_fold' must be a list for {model_type}."
        assert isinstance(model_data['r2_mean'], (int, float)), f"'r2_mean' must be numeric for {model_type}."
        assert isinstance(model_data['rmse_mean'], (int, float)), f"'rmse_mean' must be numeric for {model_type}."
        
        # Validate list contents
        for val in model_data['r2_per_fold']:
            assert isinstance(val, (int, float)), f"R2 per fold values must be numeric for {model_type}."
        for val in model_data['rmse_per_fold']:
            assert isinstance(val, (int, float)), f"RMSE per fold values must be numeric for {model_type}."
    
    # 5. Validate feature_importance structure
    feature_importance = metrics['feature_importance']
    assert 'traditional' in feature_importance, "Missing 'traditional' in feature_importance."
    assert 'topological' in feature_importance, "Missing 'topological' in feature_importance."
    
    # Both should be lists
    assert isinstance(feature_importance['traditional'], list), "'traditional' feature importance must be a list."
    assert isinstance(feature_importance['topological'], list), "'topological' feature importance must be a list."
