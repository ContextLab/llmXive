"""
Tests for the model training module (train.py).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.linear_model import LogisticRegression

# Import functions to test
from src.models.train import (
    calculate_vif,
    run_vif_selection,
    train_l1_logistic_regression,
    train_model_fold,
    save_model,
    load_model
)

@pytest.fixture
def sample_features():
    """Create a sample feature DataFrame with some collinearity."""
    np.random.seed(42)
    n = 100
    # Feature A
    A = np.random.normal(0, 1, n)
    # Feature B (highly correlated with A)
    B = A * 0.9 + np.random.normal(0, 0.1, n)
    # Feature C (uncorrelated)
    C = np.random.normal(0, 1, n)
    # Feature D (uncorrelated)
    D = np.random.normal(0, 1, n)
    
    df = pd.DataFrame({
        'feature_A': A,
        'feature_B': B,
        'feature_C': C,
        'feature_D': D
    })
    return df

@pytest.fixture
def sample_labels():
    """Create sample binary labels."""
    np.random.seed(42)
    return pd.Series(np.random.randint(0, 2, 100))

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_vif_basic(sample_features):
    """Test basic VIF calculation."""
    vif_series = calculate_vif(sample_features)
    
    assert len(vif_series) == 4
    assert 'feature_A' in vif_series.index
    assert 'feature_B' in vif_series.index
    
    # feature_B is highly correlated with feature_A, so it should have a high VIF
    assert vif_series['feature_B'] > 1.0
    assert vif_series['feature_C'] < 2.0 # Uncorrelated features should have low VIF
    assert vif_series['feature_D'] < 2.0

def test_run_vif_selection_reduces_features(sample_features, sample_labels, temp_output_dir):
    """Test that VIF selection removes high VIF features."""
    # Set a low threshold to force removal
    output_path = temp_output_dir / "test_vif.csv"
    reduced_X, kept_features = run_vif_selection(
        X=sample_features,
        y=sample_labels,
        threshold=2.0, # Low threshold to trigger removal
        output_path=output_path
    )
    
    # Check that output file was created
    assert output_path.exists()
    
    # Check that features were removed (feature_B should be gone due to correlation)
    assert len(kept_features) < len(sample_features.columns)
    assert 'feature_B' not in kept_features # Likely removed due to high VIF
    assert 'feature_A' in kept_features or 'feature_B' in kept_features # One of the correlated pair remains

def test_run_vif_selection_empty_threshold(sample_features, sample_labels, temp_output_dir):
    """Test VIF selection with a very high threshold (no removal)."""
    output_path = temp_output_dir / "test_vif_no_remove.csv"
    reduced_X, kept_features = run_vif_selection(
        X=sample_features,
        y=sample_labels,
        threshold=1000.0, # Very high threshold
        output_path=output_path
    )
    
    assert len(kept_features) == len(sample_features.columns)
    assert set(kept_features) == set(sample_features.columns)

def test_train_l1_logistic_regression_basic(sample_features, sample_labels):
    """Test basic L1 Logistic Regression training."""
    model = train_l1_logistic_regression(
        X_train=sample_features,
        y_train=sample_labels,
        C=1.0,
        random_state=42
    )
    
    assert isinstance(model, LogisticRegression)
    assert model.penalty == 'l1'
    assert model.solver == 'liblinear'
    assert model.coef_.shape[1] == len(sample_features.columns)

def test_train_l1_logistic_regression_no_features_left(sample_features, sample_labels):
    """Test training with empty features (should raise error)."""
    empty_X = pd.DataFrame()
    with pytest.raises(ValueError, match="empty feature matrix"):
        train_l1_logistic_regression(
            X_train=empty_X,
            y_train=sample_labels
        )

def test_train_model_fold(sample_features, sample_labels, temp_output_dir):
    """Test the full fold training pipeline."""
    model, features = train_model_fold(
        X_train=sample_features,
        y_train=sample_labels,
        fold_id=1,
        vif_threshold=5.0,
        output_dir=temp_output_dir,
        model_C=1.0,
        random_state=42
    )
    
    assert isinstance(model, LogisticRegression)
    assert isinstance(features, list)
    assert len(features) > 0
    
    # Check if the VIF file was created
    vif_file = temp_output_dir / "vif_filtered_features_fold_1.csv"
    assert vif_file.exists()

def test_save_and_load_model(sample_features, sample_labels, temp_output_dir):
    """Test saving and loading a model."""
    model = train_l1_logistic_regression(sample_features, sample_labels)
    features = list(sample_features.columns)
    
    model_path = temp_output_dir / "test_model.pkl"
    save_model(model, features, model_path)
    
    assert model_path.exists()
    assert model_path.with_suffix('.features.json').exists()
    
    loaded_model, loaded_features = load_model(model_path)
    
    assert isinstance(loaded_model, LogisticRegression)
    assert loaded_features == features