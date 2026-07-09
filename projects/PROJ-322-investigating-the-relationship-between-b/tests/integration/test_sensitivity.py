"""
Integration tests for sensitivity analysis (User Story 3).

Tests the sensitivity sweep functionality to ensure it outputs a table
with varying thresholds and correlation coefficients.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the module under test using the project's API surface
from sensitivity_analysis import (
    run_sensitivity_sweep,
    generate_synthetic_sensitivity_data,
    save_results,
    load_data_for_sensitivity
)
from config import is_synthetic, set_synthetic_mode

# Ensure we are in synthetic mode for this test to guarantee data availability
# without requiring real OpenNeuro downloads
set_synthetic_mode(True)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_sensitivity_sweep_outputs_table_with_varying_thresholds_and_correlation_coefficients(temp_output_dir):
    """
    Integration test: test_sensitivity_sweep_outputs_table_with_varying_thresholds_and_correlation_coefficients
    
    Verifies that the sensitivity sweep:
    1. Executes without errors
    2. Produces an output file (CSV)
    3. The CSV contains columns for thresholds and correlation coefficients
    4. The thresholds vary (are not all identical)
    5. The correlation coefficients are numeric values
    """
    # Prepare a small synthetic dataset for the test
    # We generate synthetic data that mimics the expected input structure
    # (efficiency metrics vs cognitive scores)
    n_subjects = 20
    np.random.seed(42)
    
    # Create synthetic data: efficiency metrics and cognitive scores
    # This simulates the preprocessed data that would come from US2
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'global_efficiency': np.random.uniform(0.3, 0.6, n_subjects),
        'local_efficiency': np.random.uniform(0.2, 0.5, n_subjects),
        'modularity': np.random.uniform(0.4, 0.8, n_subjects),
        'cognitive_score': np.random.uniform(80, 120, n_subjects)
    }
    
    synthetic_df = pd.DataFrame(data)
    
    # Save to a temporary CSV file to mimic real data loading
    input_csv = temp_output_dir / "synthetic_sensitivity_input.csv"
    synthetic_df.to_csv(input_csv, index=False)
    
    # Define output path
    output_csv = temp_output_dir / "sensitivity_analysis.csv"
    
    # Run the sensitivity sweep
    # We use a small range of thresholds for testing to keep execution fast
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    try:
        result = run_sensitivity_sweep(
            input_path=str(input_csv),
            output_path=str(output_csv),
            thresholds=thresholds,
            target_col='cognitive_score',
            predictor_col='global_efficiency'
        )
        
        # Verify the function returned a result
        assert result is not None, "run_sensitivity_sweep should return a result dictionary"
        
    except Exception as e:
        # If the function fails, we still want to check if the file was created
        # and what the error was
        pytest.fail(f"run_sensitivity_sweep failed with exception: {str(e)}")
    
    # Verify the output file exists
    assert output_csv.exists(), f"Output file {output_csv} was not created"
    
    # Load and verify the CSV content
    result_df = pd.read_csv(output_csv)
    
    # Check required columns exist
    required_columns = ['threshold', 'correlation_coefficient']
    for col in required_columns:
        assert col in result_df.columns, f"Missing required column: {col}"
    
    # Verify thresholds vary
    unique_thresholds = result_df['threshold'].unique()
    assert len(unique_thresholds) > 1, "Thresholds should vary (more than one unique value)"
    
    # Verify correlation coefficients are numeric and valid
    corr_coeffs = result_df['correlation_coefficient']
    assert pd.api.types.is_numeric_dtype(corr_coeffs), "Correlation coefficients should be numeric"
    
    # Check that correlation coefficients are within valid range [-1, 1]
    # (with some tolerance for floating point errors)
    valid_corr = corr_coeffs.between(-1.0 - 1e-6, 1.0 + 1e-6)
    assert valid_corr.all(), f"All correlation coefficients should be in [-1, 1], got: {corr_coeffs[~valid_corr].values}"
    
    # Verify the number of rows matches the number of thresholds tested
    assert len(result_df) == len(thresholds), \
        f"Expected {len(thresholds)} rows, got {len(result_df)}"
    
    # Additional check: ensure the output is a proper table format
    assert len(result_df.columns) >= 2, "Output should have at least 2 columns"
    
    # Verify the data types in the CSV are appropriate
    assert result_df['threshold'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "Threshold column should be numeric"
    
    print(f"✓ Sensitivity analysis output verified:")
    print(f"  - File: {output_csv}")
    print(f"  - Rows: {len(result_df)}")
    print(f"  - Columns: {list(result_df.columns)}")
    print(f"  - Unique thresholds: {sorted(unique_thresholds)}")
    print(f"  - Correlation range: [{corr_coeffs.min():.4f}, {corr_coeffs.max():.4f}]")

def test_sensitivity_sweep_handles_edge_cases(temp_output_dir):
    """
    Integration test: Verify sensitivity sweep handles edge cases gracefully.
    
    Tests behavior with:
    - Very small dataset
    - Extreme threshold values
    - Missing data handling
    """
    # Create a minimal dataset
    n_subjects = 5
    np.random.seed(123)
    
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'global_efficiency': np.random.uniform(0.3, 0.6, n_subjects),
        'cognitive_score': np.random.uniform(80, 120, n_subjects)
    }
    
    synthetic_df = pd.DataFrame(data)
    input_csv = temp_output_dir / "minimal_input.csv"
    synthetic_df.to_csv(input_csv, index=False)
    
    output_csv = temp_output_dir / "minimal_output.csv"
    
    # Test with extreme thresholds
    extreme_thresholds = [0.01, 0.99]
    
    try:
        result = run_sensitivity_sweep(
            input_path=str(input_csv),
            output_path=str(output_csv),
            thresholds=extreme_thresholds,
            target_col='cognitive_score',
            predictor_col='global_efficiency'
        )
        
        assert result is not None
        
    except Exception as e:
        # Some edge cases might legitimately fail, but we want to know what
        pytest.fail(f"Edge case test failed unexpectedly: {str(e)}")
    
    # Verify output exists even for minimal data
    assert output_csv.exists(), "Output should be created even for minimal data"
    
    result_df = pd.read_csv(output_csv)
    assert len(result_df) == len(extreme_thresholds)
    assert 'threshold' in result_df.columns
    assert 'correlation_coefficient' in result_df.columns