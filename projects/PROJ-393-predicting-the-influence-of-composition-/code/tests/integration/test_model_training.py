"""
Integration test for the Model Training Pipeline (T035).
Tests 5-fold cross-validation and GridSearchCV execution end-to-end.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import sys
import json

# Add code/src to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from src.models.training_pipeline import (
    load_features_data,
    prepare_data,
    run_cross_validation,
    tune_and_train_linear,
    tune_and_train_rf,
    run_training_pipeline
)

@pytest.fixture
def sample_features_df():
    """Create a small synthetic dataset for testing the pipeline logic."""
    # Generate realistic-looking data for Heusler alloys
    n_samples = 100
    np.random.seed(42)
    
    data = {
        "composition": [f"Co2Mn{elem}" for elem in np.random.choice(["Ga", "Al", "In"], n_samples)],
        "avg_electronegativity": np.random.uniform(1.5, 2.5, n_samples),
        "valence_electron_concentration": np.random.uniform(18.0, 20.0, n_samples),
        "atomic_radii_variance": np.random.uniform(0.0, 0.1, n_samples),
        "avg_d_electrons": np.random.uniform(5.0, 7.0, n_samples),
        "atomic_size_mismatch": np.random.uniform(0.0, 0.05, n_samples),
        "coercivity_oersted": np.random.uniform(10.0, 100.0, n_samples), # Target
        "source_type": ["Experimental"] * n_samples
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_features_file(sample_features_df):
    """Save sample dataframe to a temp CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_features_df.to_csv(f.name, index=False)
        yield Path(f.name)
    os.unlink(f.name)

def test_prepare_data(temp_features_file):
    """Test data preparation logic."""
    df = pd.read_csv(temp_features_file)
    X, y, feature_names = prepare_data(df, target_col="coercivity_oersted")
    
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.shape[0] == y.shape[0]
    assert X.shape[1] == 5 # Expected number of features
    assert "coercivity_oersted" not in feature_names

def test_run_cross_validation(temp_features_file):
    """Test that cross-validation runs and returns expected metrics."""
    from sklearn.linear_model import Ridge
    
    df = pd.read_csv(temp_features_file)
    X, y, _ = prepare_data(df, target_col="coercivity_oersted")
    
    model = Ridge(alpha=1.0)
    scores = run_cross_validation(model, X, y, cv=5)
    
    assert "r2_mean" in scores
    assert "r2_std" in scores
    assert "mae_mean" in scores
    assert "mae_std" in scores
    assert isinstance(scores["r2_mean"], float)

def test_tune_and_train_linear(temp_features_file):
    """Test Linear/Ridge tuning and training."""
    df = pd.read_csv(temp_features_file)
    X, y, feature_names = prepare_data(df, target_col="coercivity_oersted")
    
    model, metrics = tune_and_train_linear(X, y, feature_names)
    
    assert model is not None
    assert "best_params" in metrics
    assert "cv_results" in metrics
    assert "r2_mean" in metrics["cv_results"]

def test_tune_and_train_rf(temp_features_file):
    """Test Random Forest tuning and training."""
    df = pd.read_csv(temp_features_file)
    X, y, feature_names = prepare_data(df, target_col="coercivity_oersted")
    
    model, metrics = tune_and_train_rf(X, y, feature_names)
    
    assert model is not None
    assert "best_params" in metrics
    assert "cv_results" in metrics
    # RF should have more parameters tuned
    assert "n_estimators" in metrics["best_params"]

def test_run_training_pipeline_integration(temp_features_file, tmp_path):
    """
    Full integration test: Run the pipeline end-to-end.
    Verifies that models are saved and metrics are generated.
    """
    # Temporarily override global paths for the test
    import src.models.training_pipeline as pipeline_module
    original_model_dir = pipeline_module.MODEL_DIR
    original_metrics_file = pipeline_module.METRICS_FILE
    
    try:
        # Set temporary directories
        pipeline_module.MODEL_DIR = tmp_path / "models"
        pipeline_module.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        pipeline_module.METRICS_FILE = tmp_path / "metrics.json"
        
        # Run the pipeline
        results = run_training_pipeline(
            input_path=temp_features_file,
            target_col="coercivity_oersted",
            enable_linear=True,
            enable_rf=True
        )
        
        # Assertions
        assert "linear" in results
        assert "random_forest" in results
        assert results["linear"]["path"].endswith(".pkl")
        assert results["random_forest"]["path"].endswith(".pkl")
        
        # Check metrics file
        assert pipeline_module.METRICS_FILE.exists()
        with open(pipeline_module.METRICS_FILE, 'r') as f:
            metrics_data = json.load(f)
        
        assert "linear_model" in metrics_data
        assert "random_forest_model" in metrics_data
        
    finally:
        # Restore original paths
        pipeline_module.MODEL_DIR = original_model_dir
        pipeline_module.METRICS_FILE = original_metrics_file