import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.refit_after_drop import (
    load_final_predictors, 
    load_training_data, 
    prepare_features, 
    fit_logistic_model, 
    main
)

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directory structure for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "final").mkdir()
    (data_dir / "processed").mkdir()
    return data_dir

@pytest.fixture
def setup_test_data(temp_dirs):
    """Create mock data files for testing."""
    # Create final_predictors.json
    predictors_data = {
        "predictors": ["frequency", "similarity", "role"],
        "dropped": ["role"]
    }
    with open(temp_dirs / "final" / "final_predictors.json", 'w') as f:
        json.dump(predictors_data, f)
    
    # Create train_set.parquet
    df = pd.DataFrame({
        "frequency": np.random.rand(100),
        "similarity": np.random.rand(100),
        "role": np.random.rand(100),
        "compatibility_label": np.random.randint(0, 2, 100)
    })
    df.to_parquet(temp_dirs / "processed" / "train_set.parquet")
    
    return temp_dirs

def test_load_final_predictors(setup_test_data):
    """Test loading final predictors from JSON."""
    predictors, dropped = load_final_predictors()
    assert "frequency" in predictors
    assert "similarity" in predictors
    assert "role" in dropped

def test_prepare_features(setup_test_data):
    """Test feature preparation."""
    df = load_training_data()
    predictors = ["frequency", "similarity"]
    X, y, used_preds = prepare_features(df, predictors)
    
    assert X.shape[0] == df.shape[0]
    assert list(X.columns) == predictors
    assert len(y) == df.shape[0]

def test_fit_logistic_model(setup_test_data):
    """Test logistic regression fitting."""
    df = load_training_data()
    predictors = ["frequency", "similarity"]
    X, y, used_preds = prepare_features(df, predictors)
    
    results = fit_logistic_model(X, y, used_preds)
    
    assert "coefficients" in results
    assert "metrics" in results
    assert "auc" in results["metrics"]
    assert 0 <= results["metrics"]["auc"] <= 1

def test_main_with_drop(setup_test_data, tmp_path, monkeypatch):
    """Test main execution when a predictor is dropped."""
    # Change working directory to temp to find files
    monkeypatch.chdir(tmp_path)
    
    # We need to mock the Path objects to point to our temp dirs
    # Since the functions use hardcoded paths relative to cwd, we just ensure cwd is correct
    # and files exist there.
    
    # The setup_test_data fixture already created files in temp_dirs (which is tmp_path/data)
    # But the code expects files at data/final_predictors.json relative to cwd.
    # So we need to move files or adjust the test.
    # Let's adjust the test to create files in the expected relative locations from tmp_path.
    
    # Re-create structure relative to tmp_path (cwd)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "final").mkdir()
    (tmp_path / "data" / "processed").mkdir()
    
    # Write predictors
    with open(tmp_path / "data" / "final" / "final_predictors.json", 'w') as f:
        json.dump({"predictors": ["freq", "sim"], "dropped": ["role"]}, f)
    
    # Write data
    df = pd.DataFrame({
        "freq": np.random.rand(50),
        "sim": np.random.rand(50),
        "compatibility_label": np.random.randint(0, 2, 50)
    })
    df.to_parquet(tmp_path / "data" / "processed" / "train_set.parquet")
    
    # Run main
    main()
    
    # Check output
    output_path = tmp_path / "data" / "final" / "logistic_results_refit.json"
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        results = json.load(f)
    
    assert "coefficients" in results
    assert "dropped_predictors" in results
    assert results["dropped_predictors"] == ["role"]

def test_main_no_drop(tmp_path, monkeypatch):
    """Test main execution when no predictor is dropped."""
    monkeypatch.chdir(tmp_path)
    
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "final").mkdir()
    (tmp_path / "data" / "processed").mkdir()
    
    # Write predictors with empty dropped list
    with open(tmp_path / "data" / "final" / "final_predictors.json", 'w') as f:
        json.dump({"predictors": ["freq", "sim"], "dropped": []}, f)
    
    # Write original results
    original_results = {"coefficients": {"freq": 0.5}, "metrics": {"auc": 0.8}}
    with open(tmp_path / "data" / "final" / "logistic_results.json", 'w') as f:
        json.dump(original_results, f)
    
    main()
    
    output_path = tmp_path / "data" / "final" / "logistic_results_refit.json"
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        results = json.load(f)
    
    assert results["coefficients"] == original_results["coefficients"]
    assert "note" in results
    assert "No predictors dropped" in results["note"]
