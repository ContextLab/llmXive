"""
Integration test for the Model Training Pipeline (T030).
Verifies k-fold cross-validation, model training, and metric generation for Linear and RF models.
Ensures `data/processed/model_metrics.json` is produced with valid R² and MAE values.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import json
from pathlib import Path
import sys
import shutil

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

from src.models.training_pipeline import (
    load_features_data,
    prepare_data,
    run_cross_validation,
    tune_and_train_linear,
    tune_and_train_rf,
    run_training_pipeline
)
from src.features.descriptor_calculator import calculate_all_descriptors
from src.preprocessing.preprocess_pipeline import run_preprocessing_pipeline
from src.ingestion.manual_curator import load_manual_curated_data

@pytest.fixture
def sample_features_df():
    """Create a small synthetic dataset for testing the pipeline logic."""
    n_samples = 100
    np.random.seed(42)
    
    data = {
        "composition": [f"Co2Mn{elem}" for elem in np.random.choice(["Ga", "Al", "In"], n_samples)],
        "avg_electronegativity": np.random.uniform(1.5, 2.5, n_samples),
        "valence_electron_concentration": np.random.uniform(18.0, 20.0, n_samples),
        "atomic_radii_variance": np.random.uniform(0.0, 0.1, n_samples),
        "avg_d_electrons": np.random.uniform(5.0, 7.0, n_samples),
        "atomic_size_mismatch": np.random.uniform(0.0, 0.05, n_samples),
        "coercivity_oersted": np.random.uniform(10.0, 100.0, n_samples),
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
    assert X.shape[1] == 5
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
    assert "n_estimators" in metrics["best_params"]

def test_run_training_pipeline_integration(temp_features_file, tmp_path):
    """
    Full integration test: Run the pipeline end-to-end.
    Verifies that models are saved and metrics are generated.
    """
    import src.models.training_pipeline as pipeline_module
    original_model_dir = pipeline_module.MODEL_DIR
    original_metrics_file = pipeline_module.METRICS_FILE
    
    try:
        pipeline_module.MODEL_DIR = tmp_path / "models"
        pipeline_module.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        pipeline_module.METRICS_FILE = tmp_path / "metrics.json"
        
        results = run_training_pipeline(
            input_path=temp_features_file,
            target_col="coercivity_oersted",
            enable_linear=True,
            enable_rf=True
        )
        
        assert "linear" in results
        assert "random_forest" in results
        assert results["linear"]["path"].endswith(".pkl")
        assert results["random_forest"]["path"].endswith(".pkl")
        
        assert pipeline_module.METRICS_FILE.exists()
        with open(pipeline_module.METRICS_FILE, 'r') as f:
            metrics_data = json.load(f)
        
        assert "linear_model" in metrics_data
        assert "random_forest_model" in metrics_data
        
    finally:
        pipeline_module.MODEL_DIR = original_model_dir
        pipeline_module.METRICS_FILE = original_metrics_file

def test_end_to_end_metrics_generation(tmp_path):
    """
    Integration test verifying the full flow produces data/processed/model_metrics.json
    with valid R2 and MAE values for both models.
    """
    # Create a temporary features file with realistic data
    n_samples = 50
    np.random.seed(42)
    data = {
        "composition": [f"Co2Mn{elem}" for elem in np.random.choice(["Ga", "Al", "In"], n_samples)],
        "avg_electronegativity": np.random.uniform(1.5, 2.5, n_samples),
        "valence_electron_concentration": np.random.uniform(18.0, 20.0, n_samples),
        "atomic_radii_variance": np.random.uniform(0.0, 0.1, n_samples),
        "avg_d_electrons": np.random.uniform(5.0, 7.0, n_samples),
        "atomic_size_mismatch": np.random.uniform(0.0, 0.05, n_samples),
        "coercivity_oersted": np.random.uniform(10.0, 100.0, n_samples),
        "source_type": ["Experimental"] * n_samples
    }
    df = pd.DataFrame(data)
    
    features_file = tmp_path / "test_features.csv"
    df.to_csv(features_file, index=False)
    
    # Temporarily override paths
    import src.models.training_pipeline as pipeline_module
    original_metrics_file = pipeline_module.METRICS_FILE
    
    try:
        test_metrics_file = tmp_path / "model_metrics.json"
        pipeline_module.METRICS_FILE = test_metrics_file
        
        # Run pipeline
        run_training_pipeline(
            input_path=features_file,
            target_col="coercivity_oersted",
            enable_linear=True,
            enable_rf=True
        )
        
        # Verify output file exists
        assert test_metrics_file.exists(), "model_metrics.json was not created"
        
        # Load and validate content
        with open(test_metrics_file, 'r') as f:
            metrics = json.load(f)
        
        # Check structure
        assert "linear_model" in metrics, "Missing linear_model in metrics"
        assert "random_forest_model" in metrics, "Missing random_forest_model in metrics"
        
        # Validate Linear Model metrics
        linear_metrics = metrics["linear_model"]
        assert "r2" in linear_metrics, "Missing r2 in linear_model metrics"
        assert "mae" in linear_metrics, "Missing mae in linear_model metrics"
        assert isinstance(linear_metrics["r2"], (int, float)), "r2 must be numeric"
        assert isinstance(linear_metrics["mae"], (int, float)), "mae must be numeric"
        
        # Validate RF Model metrics
        rf_metrics = metrics["random_forest_model"]
        assert "r2" in rf_metrics, "Missing r2 in random_forest_model metrics"
        assert "mae" in rf_metrics, "Missing mae in random_forest_model metrics"
        assert isinstance(rf_metrics["r2"], (int, float)), "r2 must be numeric"
        assert isinstance(rf_metrics["mae"], (int, float)), "mae must be numeric"
        
        # Basic sanity checks (R2 should be <= 1.0, MAE >= 0)
        assert linear_metrics["r2"] <= 1.0, "R2 cannot be greater than 1.0"
        assert rf_metrics["r2"] <= 1.0, "R2 cannot be greater than 1.0"
        assert linear_metrics["mae"] >= 0, "MAE cannot be negative"
        assert rf_metrics["mae"] >= 0, "MAE cannot be negative"
        
    finally:
        pipeline_module.METRICS_FILE = original_metrics_file