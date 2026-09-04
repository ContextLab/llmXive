import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from train import train_model, evaluate_model, split_data

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for unit testing."""
    np.random.seed(42)
    n = 100
    data = {
        'cold_work': np.random.uniform(0, 100, n),
        'Mn_content': np.random.uniform(0, 1, n),
        'Mg_content': np.random.uniform(0, 1, n),
        'Si_content': np.random.uniform(0, 1, n),
        'Cu_content': np.random.uniform(0, 1, n),
        'temperature': np.random.uniform(200, 500, n),
        'time_to_peak_minutes': np.random.uniform(10, 1000, n)
    }
    return pd.DataFrame(data)

def test_train_model_creates_fitted_object(sample_data):
    """Test that train_model returns a fitted RandomForestRegressor."""
    target_col = 'time_to_peak_minutes'
    X = sample_data.drop(columns=[target_col])
    y = sample_data[target_col]
    
    # Split manually to ensure deterministic input
    X_train, X_test, y_train, y_test = split_data(sample_data)
    
    model = train_model(X_train, y_train)
    
    assert isinstance(model, RandomForestRegressor)
    assert model.estimators_ is not None
    assert len(model.estimators_) == 100

def test_evaluate_model_returns_metrics(sample_data):
    """Test that evaluate_model returns a dictionary with MAE and R2."""
    target_col = 'time_to_peak_minutes'
    X = sample_data.drop(columns=[target_col])
    y = sample_data[target_col]
    
    X_train, X_test, y_train, y_test = split_data(sample_data)
    model = train_model(X_train, y_train)
    
    metrics = evaluate_model(model, X_test, y_test)
    
    assert isinstance(metrics, dict)
    assert 'mae' in metrics
    assert 'r2' in metrics
    assert isinstance(metrics['mae'], float)
    assert isinstance(metrics['r2'], float)
    assert metrics['mae'] >= 0
    assert -np.inf < metrics['r2'] <= 1.0

def test_split_data_proportions(sample_data):
    """Test that split_data respects the 80/20 split ratio."""
    X_train, X_test, y_train, y_test = split_data(sample_data)
    
    total = len(X_train) + len(X_test)
    train_ratio = len(X_train) / total
    
    # Allow small tolerance for integer rounding
    assert 0.75 < train_ratio < 0.85