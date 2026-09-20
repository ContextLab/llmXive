"""
Tests for the training module (T014).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.linear_model import LogisticRegression

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
    """Generate sample feature matrix."""
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    X = np.random.randn(n_samples, n_features)
    
    # Add some correlation to make VIF meaningful
    X[:, 1] = X[:, 0] * 0.9 + np.random.randn(n_samples) * 0.1
    X[:, 2] = X[:, 0] * 0.8 + np.random.randn(n_samples) * 0.2
    
    return X


@pytest.fixture
def sample_labels():
    """Generate sample binary labels."""
    np.random.seed(42)
    return np.random.randint(0, 2, 100)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_calculate_vif_basic(sample_features):
    """Test basic VIF calculation."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    vif_df = calculate_vif(sample_features, feature_names)
    
    assert isinstance(vif_df, pd.DataFrame)
    assert 'feature' in vif_df.columns
    assert 'vif' in vif_df.columns
    assert len(vif_df) == len(feature_names)
    
    # All VIF values should be non-negative
    assert all(vif_df['vif'] >= 0)


def test_run_vif_selection_reduces_features(sample_features, sample_labels):
    """Test that VIF selection reduces features when threshold is exceeded."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    
    # Use a low threshold to force removal
    X_reduced, names_reduced, vif_history = run_vif_selection(
        sample_features, sample_labels, feature_names, vif_threshold=2.0
    )
    
    assert len(names_reduced) <= len(feature_names)
    assert X_reduced.shape[1] == len(names_reduced)
    
    # All remaining features should have VIF < threshold
    final_vif = calculate_vif(X_reduced, names_reduced)
    assert all(final_vif['vif'] < 2.0) or len(final_vif) == 0


def test_run_vif_selection_empty_threshold(sample_features, sample_labels):
    """Test VIF selection with threshold=0 removes all correlated features."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    
    # With threshold=0, any feature with VIF > 0 will be removed
    # This might remove many features
    X_reduced, names_reduced, vif_history = run_vif_selection(
        sample_features, sample_labels, feature_names, vif_threshold=0.0
    )
    
    # Should at least return some features or handle gracefully
    assert X_reduced.shape[0] == sample_features.shape[0]


def test_train_l1_logistic_regression_basic(sample_features, sample_labels, temp_output_dir):
    """Test basic L1 logistic regression training."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    
    model, selected_features, vif_history = train_l1_logistic_regression(
        sample_features, sample_labels, feature_names,
        vif_threshold=10.0,  # High threshold to keep most features
        C=1.0,
        random_state=42
    )
    
    assert isinstance(model, LogisticRegression)
    assert len(selected_features) > 0
    assert len(selected_features) <= len(feature_names)
    assert isinstance(vif_history, pd.DataFrame)
    
    # Check that model has been fitted
    assert hasattr(model, 'coef_')
    assert model.coef_.shape[1] == len(selected_features)


def test_train_l1_logistic_regression_no_features_left(sample_features, sample_labels):
    """Test handling when VIF removes all features."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    
    # Use an extremely low threshold that might remove all features
    with pytest.raises(ValueError, match="No features remaining"):
        train_l1_logistic_regression(
            sample_features, sample_labels, feature_names,
            vif_threshold=0.0,  # This should remove everything
            C=1.0,
            random_state=42
        )


def test_train_model_fold(sample_features, sample_labels, temp_output_dir):
    """Test training a single fold with metadata saving."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    
    model, selected_features, metadata = train_model_fold(
        sample_features, sample_labels, feature_names,
        fold_idx=0,
        output_dir=temp_output_dir,
        vif_threshold=5.0,
        C=1.0,
        random_state=42
    )
    
    assert isinstance(model, LogisticRegression)
    assert len(selected_features) > 0
    assert 'fold' in metadata
    assert metadata['fold'] == 0
    assert 'initial_features' in metadata
    assert 'final_features' in metadata
    
    # Check that files were created
    vif_file = temp_output_dir / "vif_filtered_features_fold_0.csv"
    features_file = temp_output_dir / "selected_features_fold_0.csv"
    
    assert vif_file.exists()
    assert features_file.exists()


def test_save_and_load_model(sample_features, sample_labels, temp_output_dir):
    """Test saving and loading a model."""
    feature_names = [f'feature_{i}' for i in range(sample_features.shape[1])]
    
    # Train a model
    model, selected_features, _ = train_l1_logistic_regression(
        sample_features, sample_labels, feature_names,
        vif_threshold=10.0,
        random_state=42
    )
    
    # Save the model
    model_path = temp_output_dir / "test_model.pkl"
    save_model(model, selected_features, model_path)
    
    assert model_path.exists()
    
    # Load the model
    loaded_model, loaded_features, loaded_metadata = load_model(model_path)
    
    assert isinstance(loaded_model, LogisticRegression)
    assert loaded_features == selected_features
    assert loaded_model.coef_.shape == model.coef_.shape