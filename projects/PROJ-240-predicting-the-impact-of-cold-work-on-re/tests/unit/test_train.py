"""
Unit tests for the training pipeline, specifically focusing on T026 (held-out test evaluation).
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import sys
from pathlib import Path

# Add parent directory to path to import train module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from train import evaluate_model, split_data

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        "cold_work": np.random.uniform(0, 100, n_samples),
        "Mn_content": np.random.uniform(0, 2, n_samples),
        "Mg_content": np.random.uniform(0, 2, n_samples),
        "Si_content": np.random.uniform(0, 2, n_samples),
        "Cu_content": np.random.uniform(0, 2, n_samples),
        "annealing_temp": np.random.uniform(200, 500, n_samples),
        "time_to_peak": np.random.uniform(10, 100, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def train_test_split_data(sample_data):
    """Split sample data into train and test sets."""
    return split_data(sample_data)

def test_evaluate_model_calculates_mae_correctly(train_test_split_data):
    """Test that evaluate_model correctly calculates MAE."""
    X_train, X_test, y_train, y_test = train_test_split_data
    
    # Train a simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Verify MAE calculation
    y_pred = model.predict(X_test)
    expected_mae = mean_absolute_error(y_test, y_pred)
    
    assert "mae" in metrics
    assert isinstance(metrics["mae"], float)
    assert np.isclose(metrics["mae"], expected_mae)

def test_evaluate_model_calculates_r2_correctly(train_test_split_data):
    """Test that evaluate_model correctly calculates R² score."""
    X_train, X_test, y_train, y_test = train_test_split_data
    
    # Train a simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Verify R² calculation
    y_pred = model.predict(X_test)
    expected_r2 = r2_score(y_test, y_pred)
    
    assert "r2" in metrics
    assert isinstance(metrics["r2"], float)
    assert np.isclose(metrics["r2"], expected_r2)

def test_evaluate_model_returns_dict_with_required_keys(train_test_split_data):
    """Test that evaluate_model returns a dictionary with required keys."""
    X_train, X_test, y_train, y_test = train_test_split_data
    
    # Train a simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    assert isinstance(metrics, dict)
    assert "mae" in metrics
    assert "r2" in metrics

def test_evaluate_model_values_are_reasonable(train_test_split_data):
    """Test that the calculated metrics are within reasonable bounds."""
    X_train, X_test, y_train, y_test = train_test_split_data
    
    # Train a model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # MAE should be positive
    assert metrics["mae"] >= 0
    
    # R² should be between -inf and 1 (typically > -1 for reasonable models)
    assert metrics["r2"] <= 1.0
    
    # For a random forest on this data, R² should typically be positive
    # This is a soft check to ensure the model isn't completely broken
    assert metrics["r2"] > -1.0

def test_split_data_produces_correct_sizes(train_test_split_data):
    """Test that split_data produces the expected train/test split sizes."""
    X_train, X_test, y_train, y_test = train_test_split_data
    
    # Default test_size is 0.2, so test set should be ~20%
    total_samples = len(y_train) + len(y_test)
    test_ratio = len(y_test) / total_samples
    
    assert 0.18 <= test_ratio <= 0.22  # Allow small rounding differences
    
    # Verify train + test equals original
    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)
    assert len(X_train) + len(X_test) == 100  # Based on sample_data size