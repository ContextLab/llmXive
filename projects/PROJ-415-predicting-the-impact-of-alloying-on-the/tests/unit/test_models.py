import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from code.models.training import train_random_forest, train_gradient_boosting, train_linear_regression

def create_dummy_data(n=50):
    X = pd.DataFrame({'size_mismatch': np.random.randn(n)})
    y = pd.Series(np.random.randn(n))
    return X, y

def test_train_random_forest_cpu():
    X, y = create_dummy_data()
    model = train_random_forest(X, y)
    assert isinstance(model, RandomForestRegressor)
    # Ensure it doesn't require CUDA
    assert model.n_jobs == -1

def test_train_gradient_boosting_cpu():
    X, y = create_dummy_data()
    model = train_gradient_boosting(X, y)
    assert isinstance(model, GradientBoostingRegressor)

def test_train_linear_regression_cpu():
    X, y = create_dummy_data()
    model, coeffs = train_linear_regression(X, y)
    assert isinstance(model, LinearRegression)
    assert 'coef' in coeffs