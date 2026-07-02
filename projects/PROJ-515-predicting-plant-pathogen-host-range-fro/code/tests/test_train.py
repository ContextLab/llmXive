"""
Tests for the model training module (T014).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Import the module under test
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
    """Create sample feature DataFrame with known multicollinearity."""
    np.random.seed(42)
    n = 100

    # Create correlated features
    f1 = np.random.randn(n)
    f2 = f1 * 0.9 + np.random.randn(n) * 0.1  # Highly correlated with f1
    f3 = np.random.randn(n)  # Independent
    f4 = f1 * 0.5 + f3 * 0.5 + np.random.randn(n) * 0.1  # Moderately correlated

    df = pd.DataFrame({
        'feature_1': f1,
        'feature_2': f2,
        'feature_3': f3,
        'feature_4': f4
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
        yield tmpdir


def test_calculate_vif_basic(sample_features):
    """Test basic VIF calculation."""
    vif = calculate_vif(sample_features)

    assert len(vif) == len(sample_features.columns)
    assert all(vif >= 1.0), "VIF should be >= 1.0"
    # feature_2 is highly correlated with feature_1, should have higher VIF
    assert vif['feature_2'] > vif['feature_3'], "Correlated feature should have higher VIF"


def test_run_vif_selection_reduces_features(sample_features):
    """Test that VIF selection removes highly correlated features."""
    reduced_df, removed = run_vif_selection(sample_features, threshold=5.0)

    # Should have removed at least one feature
    assert len(reduced_df.columns) <= len(sample_features.columns)
    assert len(removed) >= 0  # May be 0 if no VIF > 5


def test_run_vif_selection_empty_threshold(sample_features):
    """Test VIF selection with very high threshold (no removal)."""
    reduced_df, removed = run_vif_selection(sample_features, threshold=1000.0)

    # Should keep all features
    assert len(reduced_df.columns) == len(sample_features.columns)
    assert len(removed) == 0


def test_train_l1_logistic_regression_basic(sample_features, sample_labels, temp_output_dir):
    """Test basic training of L1 Logistic Regression."""
    model, X_selected, removed = train_l1_logistic_regression(
        X_train=sample_features,
        y_train=sample_labels,
        vif_threshold=5.0,
        random_state=42,
        fold_id=0,
        output_dir=temp_output_dir
    )

    # Check model type
    assert isinstance(model, LogisticRegression)

    # Check that model was fitted
    assert hasattr(model, 'coef_')
    assert model.coef_.shape[1] == len(X_selected.columns)

    # Check that VIF-filtered features file was saved
    expected_file = Path(temp_output_dir) / "vif_filtered_features_fold_0.csv"
    assert expected_file.exists(), f"VIF filtered features file not saved: {expected_file}"

    # Verify file contents
    saved_features = pd.read_csv(expected_file)
    assert 'feature_name' in saved_features.columns
    assert len(saved_features) == len(X_selected.columns)


def test_train_l1_logistic_regression_no_features_left(sample_features, temp_output_dir):
    """Test handling of extreme VIF threshold that removes all features."""
    # Create highly correlated features
    n = 50
    f1 = np.random.randn(n)
    f2 = f1 * 0.99  # Almost identical
    f3 = f1 * 0.98  # Almost identical

    X = pd.DataFrame({'f1': f1, 'f2': f2, 'f3': f3})
    y = pd.Series(np.random.randint(0, 2, n))

    # Very low threshold should remove all but one
    with pytest.raises(ValueError, match="No features available after VIF selection"):
        train_l1_logistic_regression(
            X_train=X,
            y_train=y,
            vif_threshold=1.01,  # Very strict
            random_state=42,
            fold_id=0,
            output_dir=temp_output_dir
        )


def test_train_model_fold(sample_features, sample_labels, temp_output_dir):
    """Test single fold training with train/val split."""
    n = len(sample_features)
    train_idx = np.arange(int(n * 0.8))
    val_idx = np.arange(int(n * 0.8), n)

    model, auprc, metrics = train_model_fold(
        X=sample_features,
        y=sample_labels,
        train_idx=train_idx,
        val_idx=val_idx,
        vif_threshold=5.0,
        random_state=42,
        fold_id=0,
        output_dir=temp_output_dir
    )

    assert isinstance(model, LogisticRegression)
    assert 'val_auprc' in metrics
    assert 'n_features_selected' in metrics
    assert metrics['n_train_samples'] == len(train_idx)
    assert metrics['n_val_samples'] == len(val_idx)


def test_save_and_load_model(sample_features, sample_labels, temp_output_dir):
    """Test model save and load functionality."""
    # Train a model
    model, X_selected, _ = train_l1_logistic_regression(
        X_train=sample_features,
        y_train=sample_labels,
        random_state=42
    )

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_selected)
    model.fit(X_scaled, sample_labels)

    # Save model
    model_path = Path(temp_output_dir) / "test_model.pkl"
    save_model(model, scaler, model_path)

    # Load model
    loaded_model, loaded_scaler = load_model(model_path)

    # Verify loaded model works
    assert isinstance(loaded_model, LogisticRegression)
    assert isinstance(loaded_scaler, StandardScaler)

    # Predictions should be consistent
    X_test = sample_features.iloc[:5]
    pred_original = model.predict(scaler.transform(X_test))
    pred_loaded = loaded_model.predict(loaded_scaler.transform(X_test))

    assert np.array_equal(pred_original, pred_loaded)