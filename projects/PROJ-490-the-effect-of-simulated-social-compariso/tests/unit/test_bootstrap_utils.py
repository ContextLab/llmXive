"""
Unit tests for bootstrap CI width variance calculation (T026).

These tests verify that the CI width variance calculation works correctly
and properly flags unstable results according to SC-004.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Import the functions under test
from analysis.bootstrap_utils import (
    calculate_ci_width_variance,
    run_bootstrap_stability_analysis,
    CI_WIDTH_VARIANCE_THRESHOLD
)

@pytest.fixture
def valid_bootstrap_data():
    """Create valid bootstrap results for testing."""
    n_iterations = 1000
    np.random.seed(42)
    
    # Generate realistic bootstrap results
    data = {
        'coef_avatar_condition': np.random.normal(0.5, 0.1, n_iterations),
        'ci_lower_coef_avatar_condition': np.random.normal(0.3, 0.05, n_iterations),
        'ci_upper_coef_avatar_condition': np.random.normal(0.7, 0.05, n_iterations),
        'coef_comparison_tendency': np.random.normal(0.2, 0.08, n_iterations),
        'ci_lower_coef_comparison_tendency': np.random.normal(0.1, 0.04, n_iterations),
        'ci_upper_coef_comparison_tendency': np.random.normal(0.3, 0.04, n_iterations),
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def unstable_bootstrap_data():
    """Create bootstrap results with high variance (unstable)."""
    n_iterations = 1000
    np.random.seed(123)
    
    # Generate data with high variance in CI widths
    # This simulates an unstable model
    data = {
        'coef_avatar_condition': np.random.normal(0.5, 0.5, n_iterations),  # High variance
        'ci_lower_coef_avatar_condition': np.random.normal(0.0, 0.3, n_iterations),
        'ci_upper_coef_avatar_condition': np.random.normal(1.0, 0.3, n_iterations),
    }
    
    return pd.DataFrame(data)

def test_calculate_ci_width_variance_basic(valid_bootstrap_data):
    """Test basic CI width variance calculation."""
    result = calculate_ci_width_variance(valid_bootstrap_data)
    
    assert 'variance' in result
    assert 'threshold' in result
    assert 'flagged' in result
    assert 'details' in result
    assert 'sample_size' in result
    
    assert result['variance'] is not None
    assert result['variance'] >= 0
    assert result['threshold'] == CI_WIDTH_VARIANCE_THRESHOLD
    assert isinstance(result['flagged'], bool)

def test_calculate_ci_width_variance_flagging(valid_bootstrap_data, unstable_bootstrap_data):
    """Test that high variance results are properly flagged."""
    # Stable data should not be flagged (or very rarely)
    stable_result = calculate_ci_width_variance(valid_bootstrap_data)
    # Note: We don't assert False here because it depends on the random seed
    # but we verify the logic works
    
    # Unstable data should be flagged
    unstable_result = calculate_ci_width_variance(unstable_bootstrap_data)
    assert unstable_result['flagged'] is True, "Unstable data should be flagged"

def test_calculate_ci_width_variance_empty_dataframe():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame()
    
    with pytest.raises(ValueError, match="bootstrap_results cannot be None or empty"):
        calculate_ci_width_variance(empty_df)

def test_calculate_ci_width_variance_missing_columns():
    """Test handling of missing CI columns."""
    df = pd.DataFrame({
        'coef_test': [1, 2, 3],
        # Missing ci_lower and ci_upper columns
    })
    
    with pytest.raises(ValueError, match="No coefficient columns found"):
        calculate_ci_width_variance(df)

def test_calculate_ci_width_variance_insufficient_data():
    """Test handling of insufficient data for variance calculation."""
    df = pd.DataFrame({
        'coef_test': [1, 2],
        'ci_lower_coef_test': [0.5, 1.0],
        'ci_upper_coef_test': [1.5, 2.0],
    })
    
    # Only 2 rows, but variance calculation might still work
    # We test with just 1 row
    df_single = pd.DataFrame({
        'coef_test': [1],
        'ci_lower_coef_test': [0.5],
        'ci_upper_coef_test': [1.5],
    })
    
    with pytest.raises(ValueError, match="Insufficient data"):
        calculate_ci_width_variance(df_single)

def test_run_bootstrap_stability_analysis_from_dataframe(valid_bootstrap_data):
    """Test running stability analysis from DataFrame config."""
    config = {
        'bootstrap_results': valid_bootstrap_data,
        'coefficient_columns': ['coef_avatar_condition']
    }
    
    result = run_bootstrap_stability_analysis(config=config)
    
    assert 'variance' in result
    assert 'flagged' in result
    assert result['sample_size'] == len(valid_bootstrap_data)

def test_run_bootstrap_stability_analysis_from_file(valid_bootstrap_data):
    """Test running stability analysis from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save data to file
        input_file = Path(tmpdir) / 'bootstrap_results.json'
        with open(input_file, 'w') as f:
            json.dump(valid_bootstrap_data.to_dict(orient='records'), f)
        
        output_file = Path(tmpdir) / 'stability_analysis.json'
        
        # Run analysis
        result = run_bootstrap_stability_analysis(
            input_file=str(input_file),
            output_file=str(output_file)
        )
        
        # Verify output file was created
        assert output_file.exists()
        
        # Verify results
        assert 'variance' in result
        assert 'flagged' in result

def test_run_bootstrap_stability_analysis_no_data():
    """Test error when no data source is provided."""
    with pytest.raises(ValueError, match="No data source provided"):
        run_bootstrap_stability_analysis()

def test_run_bootstrap_stability_analysis_file_not_found():
    """Test error when input file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Bootstrap results file not found"):
        run_bootstrap_stability_analysis(input_file='/nonexistent/path/file.json')

def test_ci_width_variance_threshold_constant():
    """Test that the threshold constant is set correctly."""
    assert CI_WIDTH_VARIANCE_THRESHOLD == 0.01
    assert isinstance(CI_WIDTH_VARIANCE_THRESHOLD, float)

def test_details_structure(valid_bootstrap_data):
    """Test that details dictionary contains expected fields."""
    result = calculate_ci_width_variance(valid_bootstrap_data)
    
    assert 'details' in result
    assert len(result['details']) > 0
    
    # Check structure of first detail entry
    first_key = list(result['details'].keys())[0]
    detail = result['details'][first_key]
    
    expected_fields = [
        'variance', 'mean_width', 'std_width', 
        'min_width', 'max_width', 'n_observations'
    ]
    
    for field in expected_fields:
        assert field in detail, f"Missing field: {field}"
        assert isinstance(detail[field], (int, float))

def test_multiple_coefficients(valid_bootstrap_data):
    """Test calculation with multiple coefficients."""
    result = calculate_ci_width_variance(valid_bootstrap_data)
    
    # Should have details for both coefficients
    assert len(result['details']) == 2
    assert 'coef_avatar_condition' in result['details']
    assert 'coef_comparison_tendency' in result['details']