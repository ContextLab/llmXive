import os
import sys
import tempfile
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation import (
    load_models,
    load_test_data,
    evaluate_model,
    generate_report,
    calculate_performance_degradation,
    calculate_cohen_d,
    power_analysis_z_test,
    run_power_analysis,
    main
)

@pytest.fixture
def temp_model_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        models_dir = Path(tmpdir) / "results" / "models"
        test_data_dir = Path(tmpdir) / "results" / "test_data"
        
        models_dir.mkdir(parents=True, exist_ok=True)
        test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1.0, 2.0, 3.0])
        
        # Save mock model
        model_path = models_dir / "test_prop_rf.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(mock_model, f)
        
        # Create mock test data
        X_test = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6]
        })
        y_test = pd.Series([1.5, 2.5, 3.5])
        
        test_path = test_data_dir / "test_prop_test.parquet"
        test_df = pd.concat([X_test, y_test], axis=1)
        test_df.to_parquet(test_path)
        
        yield Path(tmpdir)

@patch('evaluation.PROJECT_ROOT')
@patch('evaluation.MODELS_DIR')
def test_load_models_success(mock_models_dir, mock_project_root, temp_model_dir):
    """Test successful model loading."""
    mock_models_dir.__truediv__.return_value = temp_model_dir / "results" / "models"
    mock_project_root.__truediv__.return_value = temp_model_dir / "results"
    
    model = load_models("test_prop", "rf")
    
    assert model is not None
    mock_models_dir.__truediv__.assert_called_with("test_prop_rf.pkl")

@patch('evaluation.PROJECT_ROOT')
@patch('evaluation.MODELS_DIR')
def test_load_models_not_found(mock_models_dir, mock_project_root, temp_model_dir):
    """Test model loading when file doesn't exist."""
    mock_models_dir.__truediv__.return_value = temp_model_dir / "results" / "models"
    mock_project_root.__truediv__.return_value = temp_model_dir / "results"
    
    with pytest.raises(FileNotFoundError):
        load_models("nonexistent", "rf")

@patch('evaluation.PROJECT_ROOT')
@patch('evaluation.RESULTS_DIR')
def test_load_test_data_success(mock_results_dir, mock_project_root, temp_model_dir):
    """Test successful test data loading."""
    mock_results_dir.__truediv__.return_value = temp_model_dir / "results" / "test_data"
    mock_project_root.__truediv__.return_value = temp_model_dir / "results"
    
    X, y = load_test_data("test_prop")
    
    assert len(X) == 3
    assert len(y) == 3
    assert list(X.columns) == ['feature1', 'feature2']

def test_evaluate_model():
    """Test model evaluation metrics calculation."""
    # Create mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1.0, 2.0, 3.0])
    
    X = pd.DataFrame({'f1': [1, 2, 3]})
    y = pd.Series([1.5, 2.5, 3.5])
    
    metrics = evaluate_model(mock_model, X, y, "test_prop", "rf")
    
    assert metrics['property'] == "test_prop"
    assert metrics['model_type'] == "rf"
    assert 'MAE' in metrics
    assert 'RMSE' in metrics
    assert 'R2' in metrics
    assert metrics['MAE'] > 0

def test_calculate_performance_degradation():
    """Test performance degradation calculation."""
    skewed = pd.DataFrame({
        'property': ['prop1', 'prop1'],
        'model_type': ['rf', 'gb'],
        'MAE': [1.0, 1.5],
        'RMSE': [2.0, 2.5],
        'R2': [0.9, 0.8]
    })
    
    balanced = pd.DataFrame({
        'property': ['prop1', 'prop1'],
        'model_type': ['rf', 'gb'],
        'MAE': [0.8, 1.2],
        'RMSE': [1.8, 2.2],
        'R2': [0.95, 0.85]
    })
    
    degradation = calculate_performance_degradation(skewed, balanced)
    
    assert len(degradation) == 2
    assert 'MAE_degradation' in degradation.columns
    assert degradation['MAE_degradation'].iloc[0] == 0.2

def test_calculate_cohen_d():
    """Test Cohen's d calculation."""
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([2, 3, 4, 5, 6])
    
    d = calculate_cohen_d(group1, group2)
    
    # Expected: mean difference = 1, pooled std ≈ 1
    assert -1 < d < 1  # Should be a reasonable effect size

def test_power_analysis_z_test():
    """Test power analysis calculation."""
    n = power_analysis_z_test(effect_size=0.5, power=0.8, alpha=0.05)
    
    assert n > 0
    # For effect_size=0.5, power=0.8, alpha=0.05, n should be around 64 per group
    assert 50 < n < 100

def test_run_power_analysis():
    """Test power analysis runner."""
    result = run_power_analysis()
    
    assert 'required_seed_count' in result
    assert result['effect_size'] == 0.5
    assert result['power'] == 0.8
    assert result['alpha'] == 0.05
    assert isinstance(result['required_seed_count'], int)

@patch('evaluation.PROJECT_ROOT')
@patch('evaluation.MODELS_DIR')
@patch('evaluation.RESULTS_DIR')
def test_generate_report(mock_results_dir, mock_models_dir, mock_project_root, temp_model_dir):
    """Test baseline report generation."""
    mock_models_dir.__truediv__.return_value = temp_model_dir / "results" / "models"
    mock_results_dir.__truediv__.return_value = temp_model_dir / "results"
    mock_project_root.__truediv__.return_value = temp_model_dir / "results"
    
    report = generate_report(properties=["test_prop"], model_types=["rf"])
    
    assert len(report) == 1
    assert list(report.columns) == ['property', 'model_type', 'MAE', 'RMSE', 'R2']
    assert report['property'].iloc[0] == 'test_prop'
    assert report['model_type'].iloc[0] == 'rf'

def test_main_integration(temp_model_dir):
    """Test main function integration."""
    # Temporarily override paths
    with patch('evaluation.PROJECT_ROOT', temp_model_dir), \
         patch('evaluation.MODELS_DIR', temp_model_dir / "results" / "models"), \
         patch('evaluation.RESULTS_DIR', temp_model_dir / "results"):
        
        report = main()
        
        assert report is not None
        assert len(report) > 0
        
        # Check if file was created
        output_path = temp_model_dir / "results" / "baseline_report.csv"
        assert output_path.exists()