import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch

# Import the function to test
# Assuming the test runs from the project root or code/ is in path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from analyzer import analyze_log_pvalue_regression

@pytest.fixture
def mock_raw_pvalues_csv(tmp_path):
    """Create a mock raw_pvalues.csv file for testing."""
    data = {
        'sample_size': [10, 10, 20, 20, 50, 50, 100, 100] * 10,
        'distribution_type': ['normal', 'uniform'] * 40,
        'test_type': ['t_test', 't_test'] * 40,
        'p_value': np.random.uniform(0.001, 0.999, 80),
        'hypothesis_type': ['Null'] * 80
    }
    # Add some edge cases for 0 and 1
    data['p_value'][0] = 0.0
    data['p_value'][1] = 1.0
    
    df = pd.DataFrame(data)
    file_path = os.path.join(tmp_path, 'raw_pvalues.csv')
    df.to_csv(file_path, index=False)
    return file_path

def test_analyze_log_pvalue_regression_file_not_found():
    """Test that FileNotFoundError is raised if input file is missing."""
    with pytest.raises(FileNotFoundError):
        analyze_log_pvalue_regression("non_existent_file.csv", "output_dir")

def test_analyze_log_pvalue_regression_missing_columns(mock_raw_pvalues_csv, tmp_path):
    """Test that ValueError is raised if required columns are missing."""
    # Create a file with missing column
    data = {
        'sample_size': [10, 20],
        'p_value': [0.5, 0.6]
        # Missing distribution_type, test_type, hypothesis_type
    }
    df = pd.DataFrame(data)
    bad_path = os.path.join(tmp_path, 'bad_raw_pvalues.csv')
    df.to_csv(bad_path, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_log_pvalue_regression(bad_path, str(tmp_path))

def test_analyze_log_pvalue_regression_success(mock_raw_pvalues_csv, tmp_path):
    """Test successful execution and output generation."""
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    
    results = analyze_log_pvalue_regression(mock_raw_pvalues_csv, output_dir)
    
    # Check return type
    assert isinstance(results, dict)
    assert 'coefficients' in results
    assert 'p_values' in results
    assert 'rsquared' in results
    assert 'num_obs' in results
    
    # Check output files exist
    csv_path = os.path.join(output_dir, "log_pvalue_regression_results.csv")
    summary_path = os.path.join(output_dir, "log_pvalue_regression_summary.txt")
    
    assert os.path.exists(csv_path), "Results CSV not created"
    assert os.path.exists(summary_path), "Summary TXT not created"
    
    # Verify CSV content
    df_results = pd.read_csv(csv_path)
    assert 'term' in df_results.columns
    assert 'beta' in df_results.columns
    assert 'p_value' in df_results.columns
    
    # Verify that log_p was calculated (implicitly via model fit)
    # If we got here without error, the log transform worked.
    assert results['num_obs'] > 0

def test_analyze_log_pvalue_regression_edge_cases(mock_raw_pvalues_csv, tmp_path):
    """Test handling of p=0 and p=1 (clipping/epsilon)."""
    # The fixture already includes 0.0 and 1.0
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    
    # Should not raise an error even with 0 and 1
    results = analyze_log_pvalue_regression(mock_raw_pvalues_csv, output_dir)
    
    assert results['num_obs'] > 0
    # Check that the model fitted (no infinite coefficients)
    for beta in results['coefficients'].values():
        assert np.isfinite(beta), f"Infinite coefficient found: {beta}"
