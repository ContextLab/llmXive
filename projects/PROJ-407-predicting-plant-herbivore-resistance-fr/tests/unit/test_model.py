import os
import json
import tempfile
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from code.model import (
    train_random_forest,
    evaluate_model,
    extract_feature_importance,
    extract_feature_importance_with_data,
    save_model,
    save_metrics,
    save_feature_importance
)

def test_train_random_forest():
    """Test that the model trains without error."""
    X = pd.DataFrame({'feat1': [1, 2, 3, 4, 5], 'feat2': [5, 4, 3, 2, 1]})
    y = pd.Series([10, 20, 30, 40, 50])
    
    model = train_random_forest(X, y, random_seed=42)
    
    assert isinstance(model, RandomForestRegressor)
    assert model.n_estimators == 100

def test_evaluate_model():
    """Test that metrics are calculated correctly."""
    X = pd.DataFrame({'feat1': [1, 2, 3, 4, 5], 'feat2': [5, 4, 3, 2, 1]})
    y = pd.Series([10, 20, 30, 40, 50])
    
    model = train_random_forest(X, y, random_seed=42)
    metrics = evaluate_model(model, X, y)
    
    assert 'r2' in metrics
    assert 'mse' in metrics
    assert metrics['r2'] <= 1.0
    assert metrics['mse'] >= 0

def test_extract_feature_importance():
    """Test that feature importance is extracted and sorted."""
    X = pd.DataFrame({'feat1': [1, 2, 3, 4, 5], 'feat2': [5, 4, 3, 2, 1]})
    y = pd.Series([10, 20, 30, 40, 50])
    
    model = train_random_forest(X, y, random_seed=42)
    importance_df = extract_feature_importance(model, ['feat1', 'feat2'])
    
    assert 'metabolite_name' in importance_df.columns
    assert 'importance_score' in importance_df.columns
    assert len(importance_df) == 2
    
    # Check sorting (descending)
    scores = importance_df['importance_score'].values
    assert scores[0] >= scores[1]

def test_extract_feature_importance_with_data():
    """Test extraction of importance, correlation, and p-values."""
    X = pd.DataFrame({
        'metabolite_A': [1, 2, 3, 4, 5],
        'metabolite_B': [5, 4, 3, 2, 1]
    })
    y = pd.Series([10, 20, 30, 40, 50])
    
    model = train_random_forest(X, y, random_seed=42)
    df = extract_feature_importance_with_data(model, X, y, ['metabolite_A', 'metabolite_B'])
    
    assert 'metabolite_name' in df.columns
    assert 'importance_score' in df.columns
    assert 'correlation_coefficient' in df.columns
    assert 'unadjusted_p_value' in df.columns
    
    # Check that p-values are between 0 and 1
    assert all(0 <= p <= 1 for p in df['unadjusted_p_value'])
    
def test_save_model():
    """Test that model is saved to disk."""
    X = pd.DataFrame({'feat1': [1, 2, 3]})
    y = pd.Series([10, 20, 30])
    model = train_random_forest(X, y, random_seed=42)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test_model.pkl')
        save_model(model, path)
        assert os.path.exists(path)

def test_save_metrics():
    """Test that metrics are saved to disk."""
    metrics = {'r2': 0.9, 'mse': 0.1}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test_metrics.json')
        save_metrics(metrics, path)
        assert os.path.exists(path)
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == metrics

def test_save_feature_importance():
    """Test that feature importance is saved to disk."""
    df = pd.DataFrame({
        'metabolite_name': ['A', 'B'],
        'importance_score': [0.6, 0.4],
        'correlation_coefficient': [0.8, -0.5],
        'unadjusted_p_value': [0.01, 0.05]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test_importance.csv')
        save_feature_importance(df, path)
        assert os.path.exists(path)
        loaded_df = pd.read_csv(path)
        assert list(loaded_df.columns) == list(df.columns)