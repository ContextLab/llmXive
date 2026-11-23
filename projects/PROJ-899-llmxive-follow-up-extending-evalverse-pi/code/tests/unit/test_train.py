import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

@pytest.fixture
def sample_data():
    data = {
        'clip_id': ['c1', 'c2', 'c3'],
        'human_score': [0.9, 0.8, 0.7],
        'optical_flow_mean': [10.0, 12.0, 8.0],
        'optical_flow_var': [1.0, 1.2, 0.8],
        'audio_spectral': [100.0, 110.0, 90.0],
        'audio_zcr': [0.1, 0.12, 0.08]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_data(sample_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "features.csv")
        sample_data.to_csv(path, index=False)
        yield path

def test_prepare_data(sample_data):
    from src.models.train import prepare_data
    X, y, cols = prepare_data(sample_data)
    assert X.shape[0] == 3
    assert len(y) == 3
    assert 'human_score' not in cols

def test_train_ridge(sample_data):
    from src.models.train import train_ridge, prepare_data
    X, y, _ = prepare_data(sample_data)
    model = train_ridge(X, y)
    assert hasattr(model, 'coef_')

def test_train_lasso(sample_data):
    from src.models.train import train_lasso, prepare_data
    X, y, _ = prepare_data(sample_data)
    model = train_lasso(X, y)
    assert hasattr(model, 'coef_')

def test_train_xgboost(sample_data):
    from src.models.train import train_xgboost, prepare_data
    X, y, _ = prepare_data(sample_data)
    model = train_xgboost(X, y)
    assert hasattr(model, 'get_booster')
