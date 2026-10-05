import os
import sys
import json
import pickle
import numpy as np
import pytest
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_model_metadata_schema():
    """
    Contract test: Verify model metadata JSON schema.
    Expected fields: model_type, hyperparameters, random_seed, nested_cv_r2_mean, 
    nested_cv_r2_std, top_taxa, vif_data, feature_names, timestamp.
    """
    # Locate the metadata file (assumes latest or specific naming pattern)
    # For testing, we check if the file exists and has valid structure
    model_dir = Path("data/models")
    if not model_dir.exists():
        pytest.skip("Data models directory not found. Run modeling pipeline first.")
    
    meta_files = list(model_dir.glob("model_metadata_seed_*.json"))
    if not meta_files:
        pytest.skip("No model metadata files found.")
    
    # Use the latest file
    latest_meta = sorted(meta_files, key=lambda x: x.stat().st_mtime)[-1]
    
    with open(latest_meta, 'r') as f:
        data = json.load(f)
    
    # Check required keys
    required_keys = [
        "model_type", "hyperparameters", "random_seed", 
        "nested_cv_r2_mean", "nested_cv_r2_std", "top_taxa", 
        "vif_data", "feature_names", "timestamp"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Validate types
    assert isinstance(data["model_type"], str)
    assert isinstance(data["hyperparameters"], dict)
    assert isinstance(data["random_seed"], int)
    assert isinstance(data["nested_cv_r2_mean"], (int, float))
    assert isinstance(data["nested_cv_r2_std"], (int, float))
    assert isinstance(data["top_taxa"], list)
    assert isinstance(data["vif_data"], list)
    assert isinstance(data["feature_names"], list)
    assert isinstance(data["timestamp"], str)
    
    # Validate VIF structure
    if data["vif_data"]:
        assert "Feature" in data["vif_data"][0]
        assert "VIF" in data["vif_data"][0]

def test_model_pickle_loadable():
    """
    Contract test: Verify saved model can be loaded and used for prediction.
    """
    model_dir = Path("data/models")
    if not model_dir.exists():
        pytest.skip("Data models directory not found.")
    
    model_files = list(model_dir.glob("rf_model_seed_*.pkl"))
    if not model_files:
        pytest.skip("No model pickle files found.")
    
    latest_model = sorted(model_files, key=lambda x: x.stat().st_mtime)[-1]
    
    with open(latest_model, 'rb') as f:
        model = pickle.load(f)
    
    assert model is not None
    assert hasattr(model, 'predict')
    assert hasattr(model, 'feature_importances_')

def test_shap_values_shape():
    """
    Contract test: Verify SHAP values numpy file exists and has correct shape.
    Shape should match (n_samples, n_features).
    """
    model_dir = Path("data/models")
    if not model_dir.exists():
        pytest.skip("Data models directory not found.")
    
    shap_files = list(model_dir.glob("shap_values_seed_*.npy"))
    if not shap_files:
        pytest.skip("No SHAP values files found.")
    
    latest_shap = sorted(shap_files, key=lambda x: x.stat().st_mtime)[-1]
    
    shap_data = np.load(latest_shap, allow_pickle=True)
    
    assert shap_data is not None
    assert len(shap_data.shape) == 2, f"Expected 2D array, got shape {shap_data.shape}"
    
    # If metadata exists, cross-check dimensions
    meta_files = list(model_dir.glob("model_metadata_seed_*.json"))
    if meta_files:
        latest_meta = sorted(meta_files, key=lambda x: x.stat().st_mtime)[-1]
        with open(latest_meta, 'r') as f:
            meta = json.load(f)
        
        n_features = len(meta["feature_names"])
        assert shap_data.shape[1] == n_features, \
            f"SHAP feature dim {shap_data.shape[1]} != metadata feature count {n_features}"