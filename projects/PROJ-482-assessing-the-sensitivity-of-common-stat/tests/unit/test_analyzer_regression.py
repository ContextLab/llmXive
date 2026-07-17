import pytest
import pandas as pd
import numpy as np
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyzer import analyze_log_pvalue_regression, load_simulation_results, export_regression_results

# Mock config if not present in test env
import config
if not hasattr(config, 'SimulationConfig'):
    class MockConfig:
        alpha = 0.05
    config.SimulationConfig = MockConfig
if not hasattr(config, 'LOG_EPSILON'):
    config.LOG_EPSILON = 1e-15

@pytest.fixture
def mock_raw_data():
    """
    Generate a small mock dataset for regression testing.
    Mimics the structure of data/processed/raw_pvalues.csv
    """
    data = {
        'sample_size': [10, 10, 20, 20, 50, 50, 100, 100] * 10, # Replicates
        'distribution_type': ['normal', 'normal', 'normal', 'normal', 'uniform', 'uniform', 'log-normal', 'log-normal'] * 10,
        'test_type': ['t-test', 't-test', 't-test', 't-test', 't-test', 't-test', 't-test', 't-test'] * 10,
        'p_value': np.random.uniform(0, 1, 80),
        'hypothesis_type': ['null'] * 80
    }
    return pd.DataFrame(data)

def test_analyze_log_pvalue_regression(mock_raw_data):
    """
    Test that the regression function runs without error and returns a DataFrame.
    """
    # Run analysis
    result_df = analyze_log_pvalue_regression(mock_raw_data)
    
    # Assertions
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty
    assert 'predictor' in result_df.columns
    assert 'coefficient' in result_df.columns
    assert 'p_value' in result_df.columns
    
    # Check that we have the expected predictors
    predictors = result_df['predictor'].tolist()
    assert 'Intercept' in predictors
    assert 'log_sample_size' in predictors
    assert any('C(distribution_type)' in p for p in predictors)
    assert any('C(test_type)' in p for p in predictors)

def test_export_regression_results(tmp_path):
    """
    Test that results are exported correctly to CSV.
    """
    df = pd.DataFrame({
        'predictor': ['Intercept', 'log_sample_size'],
        'coefficient': [0.5, -0.1],
        'p_value': [0.01, 0.05]
    })
    
    output_file = tmp_path / "regression_test.csv"
    export_regression_results(df, str(output_file))
    
    assert os.path.exists(output_file)
    loaded_df = pd.read_csv(output_file)
    assert len(loaded_df) == 2
    assert 'predictor' in loaded_df.columns

def test_load_simulation_results_missing_file():
    """
    Test that load_simulation_results raises FileNotFoundError if file is missing.
    """
    # Temporarily rename the file if it exists, or ensure path is invalid
    original_path = os.path.join("data", "processed", "raw_pvalues.csv")
    backup_path = original_path + ".bak"
    
    if os.path.exists(original_path):
        os.rename(original_path, backup_path)
    
    with pytest.raises(FileNotFoundError):
        load_simulation_results()
    
    if os.path.exists(backup_path):
        os.rename(backup_path, original_path)