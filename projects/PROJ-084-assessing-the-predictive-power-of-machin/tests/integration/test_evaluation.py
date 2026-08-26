"""
Integration test for the evaluation module (T026).

Verifies that evaluate.py can successfully load models and test data,
compute metrics, and write results to disk.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR

# Import the module under test
from modeling.evaluate import (
    run_evaluation,
    load_best_models,
    load_test_data,
    evaluate_model
)
from config import DATA_RESULTS_DIR

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        data_dir = tmp_path / "data" / "processed"
        results_dir = tmp_path / "data" / "results"
        models_dir = results_dir / "best_models"
        
        data_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)
        
        yield {
            "tmp": tmp_path,
            "data": data_dir,
            "results": results_dir,
            "models": models_dir
        }

def create_mock_models(models_dir: Path):
    """Create dummy model artifacts for testing."""
    # Create a dummy RF model
    rf_model = RandomForestRegressor(n_estimators=10, random_state=42)
    rf_path = models_dir / "random_forest_best.pkl"
    with open(rf_path, "wb") as f:
        import pickle
        pickle.dump(rf_model, f)
        
    # Create a dummy SVM model
    svm_model = SVR(kernel='rbf')
    svm_path = models_dir / "svm_best.pkl"
    with open(svm_path, "wb") as f:
        import pickle
        pickle.dump(svm_model, f)
        
    # Create hyperparameters file
    hp_path = models_dir / "best_hyperparameters.json"
    with open(hp_path, "w") as f:
        json.dump({
            "random_forest": {"n_estimators": 100, "max_depth": 10},
            "svm": {"C": 1.0, "kernel": "rbf"}
        }, f)

def create_mock_data(data_dir: Path):
    """Create dummy data files for testing."""
    # Create processed data with features and yield
    n_samples = 100
    n_features = 2048  # ECFP4 dimension
    
    data = {
        "index": list(range(n_samples)),
        "yield": np.random.uniform(0, 100, n_samples),
        "reaction_class": np.random.choice(["A", "B", "C"], n_samples)
    }
    
    # Add fingerprint columns (simulated)
    for i in range(n_features):
        data[f"fp_{i}"] = np.random.randint(0, 2, n_samples)
        
    df = pd.DataFrame(data)
    data_path = data_dir / "cleaned_reactions.parquet"
    df.to_parquet(data_path)
    
    # Create split indices
    split_data = {
        "index": list(range(n_samples)),
        "split": ["train"] * 70 + ["val"] * 15 + ["test"] * 15
    }
    split_df = pd.DataFrame(split_data)
    split_path = data_dir / "split_indices.parquet"
    split_df.to_parquet(split_path)

def test_load_best_models(temp_dirs):
    """Test loading of best models."""
    models_dir = temp_dirs["models"]
    create_mock_models(models_dir)
    
    rf_model, svm_model, hyperparams = load_best_models(models_dir)
    
    assert rf_model is not None
    assert svm_model is not None
    assert "random_forest" in hyperparams
    assert "svm" in hyperparams

def test_load_test_data(temp_dirs):
    """Test loading of test data."""
    data_dir = temp_dirs["data"]
    create_mock_data(data_dir)
    
    split_path = data_dir / "split_indices.parquet"
    processed_path = data_dir / "cleaned_reactions.parquet"
    
    test_df, X_test, y_test = load_test_data(split_path, processed_path)
    
    assert len(test_df) == 15  # 15% of 100
    assert X_test.shape[1] == 2048
    assert len(y_test) == 15

def test_evaluate_model(temp_dirs):
    """Test model evaluation function."""
    # Create a simple model
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    X = np.random.rand(50, 10)
    y = np.random.rand(50)
    model.fit(X, y)
    
    X_test = np.random.rand(10, 10)
    y_test = np.random.rand(10)
    
    metrics = evaluate_model(model, X_test, y_test, "Test Model")
    
    assert "r2" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics
    assert metrics["n_samples"] == 10
    assert metrics["r2"] <= 1.0  # R² cannot exceed 1

def test_run_evaluation_integration(temp_dirs):
    """Integration test for the full evaluation pipeline."""
    # Setup mock data and models
    data_dir = temp_dirs["data"]
    models_dir = temp_dirs["models"]
    results_dir = temp_dirs["results"]
    
    create_mock_data(data_dir)
    create_mock_models(models_dir)
    
    # Patch config paths to use temp directories
    with patch("modeling.evaluate.DATA_PROCESSED_DIR", data_dir), \
         patch("modeling.evaluate.DATA_RESULTS_DIR", results_dir):
        
        results = run_evaluation()
        
        # Verify results structure
        assert "test_set_size" in results
        assert "models" in results
        assert len(results["models"]) > 0
        
        # Check metrics are present
        if "random_forest" in results["models"]:
            rf_metrics = results["models"]["random_forest"]
            assert "r2" in rf_metrics
            assert "rmse" in rf_metrics
            assert "mae" in rf_metrics
            
        if "svm" in results["models"]:
            svm_metrics = results["models"]["svm"]
            assert "r2" in svm_metrics
            assert "rmse" in svm_metrics
            assert "mae" in svm_metrics
        
        # Verify output file was written
        output_path = results_dir / "evaluation_results.json"
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            saved_results = json.load(f)
        
        assert saved_results["test_set_size"] == results["test_set_size"]

def test_run_evaluation_no_models(temp_dirs):
    """Test that evaluation fails gracefully when no models exist."""
    data_dir = temp_dirs["data"]
    create_mock_data(data_dir)
    
    # Models directory exists but is empty
    models_dir = temp_dirs["models"]
    
    with patch("modeling.evaluate.DATA_PROCESSED_DIR", data_dir), \
         patch("modeling.evaluate.DATA_RESULTS_DIR", temp_dirs["results"]):
        
        with pytest.raises(FileNotFoundError, match="No models found"):
            run_evaluation()

def test_run_evaluation_no_test_data(temp_dirs):
    """Test that evaluation fails gracefully when no test data exists."""
    data_dir = temp_dirs["data"]
    models_dir = temp_dirs["models"]
    
    # Create models but no data
    create_mock_models(models_dir)
    
    # Create empty split file with no test set
    split_df = pd.DataFrame({
        "index": [1, 2, 3],
        "split": ["train", "train", "train"]
    })
    split_path = data_dir / "split_indices.parquet"
    split_df.to_parquet(split_path)
    
    # Create dummy processed file
    dummy_df = pd.DataFrame({"index": [1, 2, 3], "yield": [1, 2, 3]})
    processed_path = data_dir / "cleaned_reactions.parquet"
    dummy_df.to_parquet(processed_path)
    
    with patch("modeling.evaluate.DATA_PROCESSED_DIR", data_dir), \
         patch("modeling.evaluate.DATA_RESULTS_DIR", temp_dirs["results"]):
        
        with pytest.raises(ValueError, match="No test data found"):
            run_evaluation()