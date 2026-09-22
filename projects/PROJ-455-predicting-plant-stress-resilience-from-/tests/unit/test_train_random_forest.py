import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from models.train import train_random_forest, get_top_features

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    X = pd.DataFrame(np.random.rand(n_samples, n_features), columns=[f'feat_{i}' for i in range(n_features)])
    # Create a linear relationship for y
    y = X.iloc[:, 0] * 2 + X.iloc[:, 1] * 0.5 + np.random.normal(0, 0.1, n_samples)
    return X, y

def test_train_random_forest_returns_model_and_metrics(sample_data):
    X, y = sample_data
    model, metrics = train_random_forest(X, y, cv=3)

    assert isinstance(model, RandomForestRegressor)
    assert isinstance(metrics, dict)
    assert 'r2' in metrics
    assert 'rmse' in metrics
    assert 'mean_absolute_error' in metrics
    assert isinstance(metrics['r2'], float)
    assert isinstance(metrics['rmse'], float)
    assert isinstance(metrics['mean_absolute_error'], float)

def test_get_top_features(sample_data):
    X, y = sample_data
    model, _ = train_random_forest(X, y, cv=3)
    top_features = get_top_features(model, X.columns.tolist(), n=2)

    assert len(top_features) == 2
    assert all(isinstance(t, tuple) and len(t) == 2 for t in top_features)
    assert all(isinstance(t[0], str) and isinstance(t[1], float) for t in top_features)