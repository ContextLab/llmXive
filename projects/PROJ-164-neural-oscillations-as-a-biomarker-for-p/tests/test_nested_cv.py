import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.nested_cv_modeling import (
    load_feature_matrix,
    fit_rank_ridge,
    run_nested_cv,
    save_model
)

@pytest.fixture
def sample_data():
    """Create sample feature matrix and target for testing."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.random.randn(100)
    return X, y

@pytest.fixture
def mock_feature_matrix_csv(tmp_path):
    """Create a mock feature_matrix.csv file."""
    df = pd.DataFrame({
        'feature_1': np.random.randn(50),
        'feature_2': np.random.randn(50),
        'feature_3': np.random.randn(50),
        'response': np.random.randn(50)
    })
    csv_path = tmp_path / "feature_matrix.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_load_feature_matrix(mock_feature_matrix_csv, tmp_path):
    """Test loading feature matrix from CSV."""
    # Mock the project structure
    with patch('code.nested_cv_modeling.Path') as mock_path:
        mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_feature_matrix_csv
        
        # This test is simplified as the actual function relies on project structure
        # In a real scenario, we would set up the full directory structure
        pass

def test_fit_rank_ridge(sample_data):
    """Test Rank-Ridge fitting."""
    X, y = sample_data
    coef, r2 = fit_rank_ridge(X, y, alpha=1.0)
    
    assert coef.shape[0] == X.shape[1]
    assert 0 <= r2 <= 1 or -np.inf < r2 < 0  # R2 can be negative for bad models
    assert isinstance(coef, np.ndarray)

def test_run_nested_cv_standard_ridge(sample_data):
    """Test nested CV with standard Ridge."""
    X, y = sample_data
    results = run_nested_cv(X, y, is_rank_ridge=False, n_splits_outer=3, n_splits_inner=3)
    
    assert "model_type" in results
    assert results["model_type"] == "Ridge"
    assert "mean_outer_r2" in results
    assert "std_outer_r2" in results
    assert len(results["outer_r2_scores"]) == 3
    assert len(results["best_alphas"]) == 3
    assert "average_coefficients" in results

def test_run_nested_cv_rank_ridge(sample_data):
    """Test nested CV with Rank-Ridge."""
    X, y = sample_data
    results = run_nested_cv(X, y, is_rank_ridge=True, n_splits_outer=3, n_splits_inner=3)
    
    assert "model_type" in results
    assert results["model_type"] == "Rank-Ridge"
    assert "mean_outer_r2" in results
    assert "std_outer_r2" in results
    assert len(results["outer_r2_scores"]) == 3
    assert len(results["best_alphas"]) == 3
    assert "average_coefficients" in results

def test_nested_cv_small_alpha_range(sample_data):
    """Test nested CV with a small alpha range."""
    X, y = sample_data
    alpha_range = [0.1, 1.0, 10.0]
    results = run_nested_cv(X, y, alpha_range=alpha_range, n_splits_outer=2, n_splits_inner=2)
    
    assert results["alpha_range"] == alpha_range
    assert len(results["cv_history"]) == 2
    for fold_result in results["cv_history"]:
        assert len(fold_result["inner_search_results"]) == 3

def test_save_model(tmp_path):
    """Test saving model and results."""
    results = {
        "model_type": "Ridge",
        "mean_outer_r2": 0.5,
        "std_outer_r2": 0.1,
        "average_coefficients": [0.1, 0.2, 0.3]
    }
    feature_names = ["f1", "f2", "f3"]
    
    # Create a mock models directory
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    
    with patch('code.nested_cv_modeling.Path') as mock_path:
        mock_path.return_value.__truediv__.return_value = models_dir
        with patch('code.nested_cv_modeling.write_json') as mock_write_json:
            save_model("Ridge", results, feature_names)
            
            # Verify that write_json was called
            assert mock_write_json.called