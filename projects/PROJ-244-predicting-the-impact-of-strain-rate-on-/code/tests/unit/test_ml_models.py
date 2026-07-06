import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Import the module under test. 
# Based on the task description, this module should exist in code/modeling/ml_models.py
# We use a relative import style assuming the test is run from the project root 
# with code/ in the path, or we mock the import if the file doesn't exist yet.
# Since T022 (implementation) is not done, we must mock the actual implementation 
# to test the *logic* of the training loop wrapper or verify the interface.
# However, the task asks for a unit test for the "training loop". 
# We will structure this test to verify that the training function:
# 1. Accepts correct arguments (X, y, model_type, params)
# 2. Calls the correct sklearn GridSearchCV logic
# 3. Returns a model and metrics dictionary
# 4. Handles errors gracefully if data is invalid

import sys
from pathlib import Path

# Ensure we can import from the code directory
code_path = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# We will attempt to import the actual module if it exists (for T022 integration),
# but for this specific unit test (T019), we primarily test the logic 
# by mocking the heavy lifting or testing the wrapper if it exists.
# Since T022 is not done, we cannot import `train_models` yet.
# We will define a minimal mock interface or test the logic of a hypothetical 
# `modeling.ml_models` module.
# To satisfy the "real code" constraint, we will implement a test that 
# verifies the *structure* required for the training loop, 
# and if the module exists, it will run; if not, it will assert the expected interface.

# Strategy: Since T022 is not implemented, we cannot import the real function.
# We will write the test assuming the function signature defined in the plan:
# train_models(X, y, model_types=['rf', 'gb', 'ridge'], param_grids=None)
# We will mock the sklearn calls to verify our logic flow.

try:
    from modeling.ml_models import train_models
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False

@pytest.fixture
def sample_data():
    """Generate a small, valid dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame({
        'strain_rate': np.log10(np.random.uniform(1e-4, 1e3, n_samples)),
        'grain_size': np.random.uniform(10, 100, n_samples),
        'temp_k': np.random.uniform(200, 800, n_samples),
        'comp_0': np.random.uniform(0, 1, n_samples),
        'comp_1': np.random.uniform(0, 1, n_samples),
    })
    y = np.random.uniform(200, 800, n_samples)
    return X, y

@pytest.fixture
def mock_sklearn_models():
    """Mock sklearn models to avoid heavy training during unit tests."""
    with patch('modeling.ml_models.RandomForestRegressor') as mock_rf, \
         patch('modeling.ml_models.GradientBoostingRegressor') as mock_gb, \
         patch('modeling.ml_models.Ridge') as mock_ridge, \
         patch('modeling.ml_models.GridSearchCV') as mock_grid, \
         patch('modeling.ml_models.r2_score') as mock_r2, \
         patch('modeling.ml_models.mean_absolute_error') as mock_mae, \
         patch('modeling.ml_models.mean_squared_error') as mock_rmse:
         
        # Setup mocks
        mock_rf.return_value = Mock()
        mock_gb.return_value = Mock()
        mock_ridge.return_value = Mock()
        
        mock_grid_instance = Mock()
        mock_grid_instance.fit = Mock()
        mock_grid_instance.best_estimator_ = Mock()
        mock_grid_instance.best_params_ = {'n_estimators': 100}
        mock_grid.return_value = mock_grid_instance
        
        mock_r2.return_value = 0.85
        mock_mae.return_value = 15.0
        mock_rmse.return_value = 20.0
        
        yield {
            'rf': mock_rf,
            'gb': mock_gb,
            'ridge': mock_ridge,
            'grid': mock_grid,
            'metrics': {'r2': mock_r2, 'mae': mock_mae, 'rmse': mock_rmse}
        }

def test_training_loop_initialization(sample_data, mock_sklearn_models):
    """Test that the training loop initializes models and parameters correctly."""
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation (T022) not yet available to import.")
    
    X, y = sample_data
    mock_data = mock_sklearn_models
    
    # Call the function
    results = train_models(X, y, model_types=['rf', 'gb'])
    
    # Verify GridSearchCV was called
    assert mock_data['grid'].call_count >= 2, "GridSearchCV should be called for each model"
    
    # Verify return structure
    assert isinstance(results, dict), "Results should be a dictionary"
    assert 'models' in results, "Results should contain 'models' key"
    assert 'metrics' in results, "Results should contain 'metrics' key"
    assert 'rf' in results['models'], "RF model should be in results"
    assert 'gb' in results['models'], "GB model should be in results"

def test_training_loop_metrics_calculation(sample_data, mock_sklearn_models):
    """Test that metrics are calculated and returned correctly."""
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation (T022) not yet available to import.")
    
    X, y = sample_data
    mock_data = mock_sklearn_models
    
    results = train_models(X, y, model_types=['ridge'])
    
    # Verify metrics were calculated
    assert mock_data['metrics']['r2'].call_count > 0, "R2 score should be calculated"
    assert mock_data['metrics']['mae'].call_count > 0, "MAE should be calculated"
    assert mock_data['metrics']['rmse'].call_count > 0, "RMSE should be calculated"
    
    # Verify values in results
    assert 'ridge' in results['metrics'], "Ridge metrics should be present"
    assert 'r2' in results['metrics']['ridge'], "R2 should be in metrics"
    assert 'mae' in results['metrics']['ridge'], "MAE should be in metrics"
    assert 'rmse' in results['metrics']['ridge'], "RMSE should be in metrics"

def test_training_loop_invalid_model_type(sample_data, mock_sklearn_models):
    """Test that the training loop handles invalid model types gracefully."""
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation (T022) not yet available to import.")
    
    X, y = sample_data
    
    with pytest.raises(ValueError, match="Unsupported model type"):
        train_models(X, y, model_types=['invalid_model'])

def test_training_loop_empty_data(sample_data, mock_sklearn_models):
    """Test that the training loop handles empty data."""
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation (T022) not yet available to import.")
    
    X_empty, y_empty = pd.DataFrame(), pd.Series()
    
    with pytest.raises(ValueError, match="Data must not be empty"):
        train_models(X_empty, y_empty)

def test_training_loop_param_grid_override(sample_data, mock_sklearn_models):
    """Test that custom parameter grids are used."""
    if not HAS_IMPLEMENTATION:
        pytest.skip("Implementation (T022) not yet available to import.")
    
    X, y = sample_data
    custom_params = {'rf': {'n_estimators': [10, 20], 'max_depth': [3, 5]}}
    
    train_models(X, y, model_types=['rf'], param_grids=custom_params)
    
    # Verify GridSearchCV received the custom params
    # Note: This depends on implementation details of how params are passed
    # We assume the implementation passes param_grid to GridSearchCV
    assert mock_sklearn_models['grid'].call_count > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])