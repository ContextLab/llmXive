import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from models.fit_logistic import load_processed_data, load_final_predictors, prepare_features, fit_logistic_models, save_models_and_results

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a mock data directory structure."""
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    final_dir = data_dir / "final"
    processed_dir.mkdir(parents=True)
    final_dir.mkdir(parents=True)
    return data_dir

def test_prepare_features(mock_data_dir):
    # Create dummy dataframe
    df = pd.DataFrame({
        'log_co_occurrence': [1.0, 2.0, 3.0],
        'similarity_score': [0.5, 0.6, 0.7],
        'functional_role_tertile': [1, 2, 3],
        'compatibility_label': [0, 1, 1]
    })
    
    predictors = ['log_co_occurrence', 'similarity_score', 'functional_role_tertile']
    X, y = prepare_features(df, predictors)
    
    assert X.shape == (3, 3)
    assert y.shape == (3,)
    assert list(X.columns) == predictors

def test_fit_logistic_models(mock_data_dir):
    # Create dummy dataframe
    df = pd.DataFrame({
        'log_co_occurrence': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        'similarity_score': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'functional_role_tertile': [1, 2, 3, 1, 2, 3],
        'compatibility_label': [0, 0, 1, 1, 1, 1]
    })
    
    predictors = ['log_co_occurrence', 'similarity_score', 'functional_role_tertile']
    X, y = prepare_features(df, predictors)
    
    results = fit_logistic_models(X, y, predictors)
    
    assert results['null']['converged'] is True
    assert results['full']['converged'] is True
    assert 'auc' in results['null']
    assert 'auc' in results['full']
    assert results['lrt']['statistic'] is not None
    assert results['lrt']['p_value'] is not None

def test_save_models_and_results(mock_data_dir):
    # Create dummy results
    class MockResult:
        def __init__(self, params, pvalues, llf, aic, bic):
            self.params = pd.Series(params)
            self.pvalues = pd.Series(pvalues)
            self.llf = llf
            self.aic = aic
            self.bic = bic
            self.df_resid = 10

    class MockFullModel:
        def __init__(self):
            self.params = pd.Series({'const': -0.5, 'x1': 0.1})
            self.pvalues = pd.Series({'const': 0.01, 'x1': 0.05})
            self.llf = -10.0
            self.aic = 25.0
            self.bic = 30.0
            self.df_resid = 8
            self.model = type('obj', (object,), {'endog': np.array([0, 1, 1, 0, 1, 1])})()
    
    class MockNullModel:
        def __init__(self):
            self.params = pd.Series({'const': -0.5, 'x1': 0.1})
            self.pvalues = pd.Series({'const': 0.01, 'x1': 0.05})
            self.llf = -12.0
            self.aic = 28.0
            self.bic = 32.0
            self.df_resid = 9

    # Mock fit_results
    fit_results = {
        "null": {
            "converged": True,
            "result": MockNullModel(),
            "auc": 0.6
        },
        "full": {
            "converged": True,
            "result": MockFullModel(),
            "auc": 0.75,
            "log_loss": 0.6
        },
        "lrt": {
            "statistic": 4.0,
            "df": 1,
            "p_value": 0.05
        }
    }
    
    predictors = ['x1']
    output_path = save_models_and_results(fit_results, predictors)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'frequency_only' in data
    assert 'full' in data
    assert 'likelihood_ratio_test' in data
    assert data['full']['converged'] is True