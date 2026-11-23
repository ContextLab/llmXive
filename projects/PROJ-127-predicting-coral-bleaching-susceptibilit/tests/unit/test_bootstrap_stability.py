import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from evaluate import run_bootstrap_stability, run_permutation_importance

@pytest.fixture
def mock_model():
    """Create a mock XGBoost model that returns deterministic predictions."""
    mock = MagicMock()
    mock.predict_proba.return_value = np.array([[0.9, 0.1], [0.1, 0.9]])
    return mock

@pytest.fixture
def mock_data():
    """Create mock feature matrix and target."""
    X = pd.DataFrame({
        'feature_a': np.random.randn(100),
        'feature_b': np.random.randn(100),
        'feature_c': np.random.randn(100),
        'feature_d': np.random.randn(100)
    })
    y = pd.Series([0] * 50 + [1] * 50)
    return X, y

def test_run_bootstrap_stability_structure(mock_model, mock_data):
    """Test that run_bootstrap_stability returns the expected structure."""
    X, y = mock_data
    
    # Mock the internal training and permutation to avoid heavy computation
    with patch('evaluate.xgb.XGBClassifier') as MockXGB:
        mock_instance = MagicMock()
        mock_instance.fit.return_value = None
        mock_instance.predict_proba.return_value = np.array([[0.9, 0.1]] * 100)
        MockXGB.return_value = mock_instance
        
        # Mock permutation_importance to return a static DataFrame
        with patch('evaluate.permutation_importance') as mock_perm:
            mock_perm.return_value = MagicMock(
                importances_mean=np.array([0.5, 0.4, 0.3, 0.2]),
                importances_std=np.array([0.1, 0.1, 0.1, 0.1])
            )
            
            result = run_bootstrap_stability(mock_model, X, y, n_bootstraps=5, random_state=42)
            
            assert 'n_bootstraps' in result
            assert result['n_bootstraps'] == 5
            assert 'top_3_features' in result
            assert 'stability_scores' in result
            assert 'rank_variance' in result
            
            # Check that stability scores are probabilities (0-1)
            for score in result['stability_scores'].values():
                assert 0.0 <= score <= 1.0

def test_bootstrap_stability_top_k(mock_model, mock_data):
    """Test that top_3_features contains exactly 3 items."""
    X, y = mock_data
    
    with patch('evaluate.xgb.XGBClassifier') as MockXGB:
        mock_instance = MagicMock()
        mock_instance.fit.return_value = None
        mock_instance.predict_proba.return_value = np.array([[0.9, 0.1]] * 100)
        MockXGB.return_value = mock_instance
        
        with patch('evaluate.permutation_importance') as mock_perm:
            mock_perm.return_value = MagicMock(
                importances_mean=np.array([0.5, 0.4, 0.3, 0.2]),
                importances_std=np.array([0.1, 0.1, 0.1, 0.1])
            )
            
            result = run_bootstrap_stability(mock_model, X, y, n_bootstraps=10, random_state=42)
            
            assert len(result['top_3_features']) == 3

def test_stability_scores_sum(mock_model, mock_data):
    """Test that stability scores logic is sound (sum of counts / n_bootstraps)."""
    X, y = mock_data
    n_bootstraps = 20
    
    # If a feature is always in top 3, score should be 1.0
    # If never, 0.0
    
    with patch('evaluate.xgb.XGBClassifier') as MockXGB:
        mock_instance = MagicMock()
        mock_instance.fit.return_value = None
        mock_instance.predict_proba.return_value = np.array([[0.9, 0.1]] * 100)
        MockXGB.return_value = mock_instance
        
        with patch('evaluate.permutation_importance') as mock_perm:
            # Force 'feature_a' to always be top
            mock_perm.return_value = MagicMock(
                importances_mean=np.array([0.9, 0.8, 0.7, 0.1]),
                importances_std=np.array([0.1, 0.1, 0.1, 0.1])
            )
            
            result = run_bootstrap_stability(mock_model, X, y, n_bootstraps=n_bootstraps, random_state=42)
            
            # feature_a should have the highest score, likely close to 1.0
            assert result['stability_scores']['feature_a'] > result['stability_scores']['feature_d']