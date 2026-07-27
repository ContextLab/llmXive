"""
Unit tests for the training module (models/train.py).
Tests stratified split logic and model training functions.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold

# Import functions to test
from models.train import (
    extract_alloy_system,
    stratify_by_alloy_system,
    prepare_data,
    train_model,
    evaluate_model
)

# Sample data for testing
SAMPLE_COMPOSITIONS = [
    "Zr50Cu40Al10",
    "Zr60Cu30Al10",
    "Cu50Zr50",
    "Al80Cu20",
    "Zr40Cu40Al20",
    "Cu60Zr40",
    "Al90Cu10",
    "Zr70Cu20Al10"
]

SAMPLE_PHASES = ['amorphous', 'amorphous', 'crystalline', 'crystalline', 'amorphous', 'crystalline', 'crystalline', 'amorphous']

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    df = pd.DataFrame({
        'composition': SAMPLE_COMPOSITIONS,
        'phase_label': SAMPLE_PHASES,
        'atomic_radius': np.random.rand(8),
        'electronegativity': np.random.rand(8),
        'valence_electron_concentration': np.random.rand(8),
        'atomic_size_mismatch': np.random.rand(8),
        'mixing_enthalpy': np.random.rand(8),
        'atomic_size_difference': np.random.rand(8),
        'valence_electron_size_mismatch': np.random.rand(8),
        'electron_atom_ratio': np.random.rand(8),
        'miedema_heat_of_formation': np.random.rand(8),
        'atomic_packing_factor': np.random.rand(8)
    })
    return df

def test_extract_alloy_system():
    """Test extraction of primary base element from composition strings."""
    assert extract_alloy_system("Zr50Cu40Al10") == "Zr"
    assert extract_alloy_system("Cu50Zr50") == "Cu"
    assert extract_alloy_system("Al80Cu20") == "Al"
    assert extract_alloy_system("Zr60Cu30Al10") == "Zr"
    assert extract_alloy_system("Invalid") == "Unknown"
    assert extract_alloy_system(None) == "Unknown"
    assert extract_alloy_system("") == "Unknown"

def test_stratify_by_alloy_system(sample_df):
    """Test stratification label generation."""
    strat_labels = stratify_by_alloy_system(sample_df)
    expected = pd.Series(['Zr', 'Zr', 'Cu', 'Al', 'Zr', 'Cu', 'Al', 'Zr'], name='alloy_system')
    pd.testing.assert_series_equal(strat_labels, expected)

def test_prepare_data_stratified(sample_df):
    """Test data preparation with stratified split by alloy system."""
    X_train, X_test, y_train, y_test, metadata = prepare_data(
        sample_df, test_size=0.25, random_state=42
    )

    # Check splits
    assert len(X_train) + len(X_test) == len(sample_df)
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)

    # Check stratification method
    assert metadata['stratification_method'] == 'stratified_by_alloy_system'
    assert metadata['train_samples'] == 6
    assert metadata['test_samples'] == 2

def test_prepare_data_simple_split(sample_df):
    """Test data preparation with simple random split (fallback)."""
    # Create a DataFrame with insufficient samples per system
    small_df = sample_df.iloc[:3].copy()  # Only 3 samples, some systems have 1
    X_train, X_test, y_train, y_test, metadata = prepare_data(
        small_df, test_size=0.33, random_state=42
    )

    assert metadata['stratification_method'] == 'simple_random'
    assert len(X_train) + len(X_test) == len(small_df)

def test_train_model_random_forest(sample_df):
    """Test Random Forest model training."""
    X_train, X_test, y_train, y_test, _ = prepare_data(sample_df, test_size=0.25, random_state=42)
    model, cv_metrics = train_model(
        X_train, y_train, model_name='random_forest', n_folds=3, random_state=42
    )

    assert model is not None
    assert 'balanced_accuracy' in cv_metrics
    assert 'precision' in cv_metrics
    assert 'recall' in cv_metrics
    assert 'f1' in cv_metrics

def test_train_model_xgboost(sample_df):
    """Test XGBoost model training."""
    X_train, X_test, y_train, y_test, _ = prepare_data(sample_df, test_size=0.25, random_state=42)
    model, cv_metrics = train_model(
        X_train, y_train, model_name='xgboost', n_folds=3, random_state=42
    )

    assert model is not None
    assert 'balanced_accuracy' in cv_metrics

def test_train_model_logistic_regression(sample_df):
    """Test Logistic Regression model training."""
    X_train, X_test, y_train, y_test, _ = prepare_data(sample_df, test_size=0.25, random_state=42)
    model, cv_metrics = train_model(
        X_train, y_train, model_name='logistic_regression', n_folds=3, random_state=42
    )

    assert model is not None
    assert 'balanced_accuracy' in cv_metrics

def test_evaluate_model(sample_df):
    """Test model evaluation."""
    X_train, X_test, y_train, y_test, _ = prepare_data(sample_df, test_size=0.25, random_state=42)
    model, _ = train_model(X_train, y_train, model_name='random_forest', n_folds=3, random_state=42)
    metrics = evaluate_model(model, X_test, y_test, 'random_forest')

    assert 'accuracy' in metrics
    assert 'balanced_accuracy' in metrics
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics
    assert all(0 <= v <= 1 for v in metrics.values())