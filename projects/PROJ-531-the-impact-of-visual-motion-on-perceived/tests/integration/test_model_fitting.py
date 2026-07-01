import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from modeling.model_fitting import fit_ols, fit_ridge, fit_random_forest, main
from utils.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_data():
    """Generate a small synthetic dataset for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'latency': np.random.normal(0.2, 0.05, n),
        'smoothness': np.random.normal(0.7, 0.1, n),
        'lead_time': np.random.normal(0.15, 0.03, n),
        'agency_score': np.random.normal(0.5, 0.1, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir(sample_data):
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    csv_path = data_dir / "cleaned_data.csv"
    sample_data.to_csv(csv_path, index=False)
    
    results_dir = Path(temp_dir) / "data" / "results"
    results_dir.mkdir(parents=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_fit_ols(sample_data):
    """Test OLS model fitting."""
    X = sample_data[['latency', 'smoothness', 'lead_time']]
    y = sample_data['agency_score']
    
    results = fit_ols(X, y)
    
    assert 'coefficients' in results
    assert 'pvalues' in results
    assert 'rsquared' in results
    assert len(results['coefficients']) == 3
    assert results['rsquared'] >= 0.0  # R² can be negative in some cases, but usually positive

def test_fit_ridge(sample_data):
    """Test Ridge model fitting."""
    X = sample_data[['latency', 'smoothness', 'lead_time']]
    y = sample_data['agency_score']
    
    results = fit_ridge(X, y)
    
    assert 'coefficients' in results
    assert 'best_alpha' in results
    assert 'cv_r2_mean' in results
    assert 'cv_r2_std' in results
    assert len(results['coefficients']) == 3
    assert results['cv_r2_mean'] is not None

def test_fit_random_forest(sample_data):
    """Test Random Forest model fitting (T022b)."""
    X = sample_data[['latency', 'smoothness', 'lead_time']]
    y = sample_data['agency_score']
    
    results = fit_random_forest(X, y)
    
    # Verify structure
    assert 'feature_importance' in results
    assert 'r2_mean' in results
    assert 'r2_std' in results
    assert 'rmse_mean' in results
    assert 'rmse_std' in results
    assert 'cv_folds' in results
    
    # Verify feature importance
    assert len(results['feature_importance']) == 3
    assert all(0.0 <= imp <= 1.0 for imp in results['feature_importance'].values())
    assert abs(sum(results['feature_importance'].values()) - 1.0) < 0.01  # Should sum to ~1
    
    # Verify metrics are reasonable
    assert results['cv_folds'] == 5
    assert results['r2_mean'] is not None
    assert results['rmse_mean'] is not None
    
    # Check that R² is not extremely poor (for synthetic data with some signal)
    # Note: This is a loose check as synthetic data might have low signal
    assert results['r2_mean'] > -1.0  # R² can be negative but shouldn't be absurdly so

def test_main_integration(temp_data_dir):
    """Test the main entry point integration."""
    # Temporarily change working directory to simulate project root
    original_cwd = os.getcwd()
    original_home = os.environ.get('HOME')
    
    try:
        # Mock the home directory to point to temp_dir
        os.environ['HOME'] = temp_data_dir
        os.chdir(temp_data_dir)
        
        # Run main
        results = main()
        
        # Verify output file exists
        output_path = Path(temp_data_dir) / "data" / "results" / "model_metrics.json"
        assert output_path.exists()
        
        # Verify content structure
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        assert 'ols' in saved_results
        assert 'ridge' in saved_results
        assert 'random_forest' in saved_results
        assert 'metadata' in saved_results
        
        # Verify Random Forest specific fields
        rf = saved_results['random_forest']
        assert 'feature_importance' in rf
        assert 'r2_mean' in rf
        assert 'rmse_mean' in rf
        
    finally:
        os.chdir(original_cwd)
        if original_home:
            os.environ['HOME'] = original_home
        else:
            os.environ.pop('HOME', None)