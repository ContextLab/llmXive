"""
Unit tests for the grid search functionality in train.py.
Verifies that grid search runs without leakage and produces valid outputs.
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from train import (
    run_grid_search_cv,
    prepare_features_targets,
    create_preprocessor,
    TrainingResult
)
from seed import set_seed

def test_grid_search_runs():
    """Test that grid search runs and produces a result object."""
    set_seed(42)
    
    # Create synthetic test data
    n_samples = 200
    data = {
        'power': np.random.rand(n_samples) * 100,
        'scanning_speed': np.random.rand(n_samples) * 50,
        'pattern_geometry': np.random.choice(['grid', 'dot', 'line'], n_samples),
        'wear_coefficient': np.random.rand(n_samples) * 10
    }
    df = pd.DataFrame(data)
    
    X, y, feature_cols = prepare_features_targets(df)
    
    # Run grid search
    result = run_grid_search_cv(X, y, feature_cols)
    
    # Assertions
    assert isinstance(result, TrainingResult)
    assert result.best_model_name is not None
    assert result.best_score is not None
    assert len(result.cv_results) > 0
    assert result.best_score <= 1.0  # R2 cannot be > 1

def test_grid_search_prevents_leakage():
    """
    Verify that grid search is performed on a training split, not the full data.
    This is checked by ensuring the function internally splits data.
    """
    set_seed(42)
    
    # Create small dataset
    n_samples = 100
    data = {
        'power': np.random.rand(n_samples),
        'scanning_speed': np.random.rand(n_samples),
        'pattern_geometry': np.random.choice(['A', 'B'], n_samples),
        'wear_coefficient': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    
    X, y, feature_cols = prepare_features_targets(df)
    
    # Mock train_test_split to verify it is called
    with patch('train.train_test_split') as mock_split:
        mock_split.return_value = (X[:80], X[80:], y[:80], y[80:])
        
        result = run_grid_search_cv(X, y, feature_cols)
        
        # Verify train_test_split was called
        assert mock_split.called
        
def test_grid_search_saves_model():
    """Test that the best model is saved to disk."""
    set_seed(42)
    
    # Create test data
    n_samples = 100
    data = {
        'power': np.random.rand(n_samples),
        'scanning_speed': np.random.rand(n_samples),
        'pattern_geometry': np.random.choice(['A', 'B'], n_samples),
        'wear_coefficient': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    
    X, y, feature_cols = prepare_features_targets(df)
    
    # Ensure models directory exists
    Path("models").mkdir(exist_ok=True)
    
    result = run_grid_search_cv(X, y, feature_cols)
    
    # Check if model file exists
    model_path = Path("models/best_model.joblib")
    assert model_path.exists(), "Best model was not saved to models/best_model.joblib"

def test_grid_search_combinations():
    """Verify that at least 10 distinct hyperparameter combinations are tested."""
    set_seed(42)
    
    n_samples = 100
    data = {
        'power': np.random.rand(n_samples),
        'scanning_speed': np.random.rand(n_samples),
        'pattern_geometry': np.random.choice(['A', 'B'], n_samples),
        'wear_coefficient': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    
    X, y, feature_cols = prepare_features_targets(df)
    
    result = run_grid_search_cv(X, y, feature_cols)
    
    # Check number of combinations
    assert len(result.cv_results) >= 10, f"Expected at least 10 combinations, got {len(result.cv_results)}"

if __name__ == "__main__":
    test_grid_search_runs()
    test_grid_search_prevents_leakage()
    test_grid_search_saves_model()
    test_grid_search_combinations()
    print("All tests passed.")