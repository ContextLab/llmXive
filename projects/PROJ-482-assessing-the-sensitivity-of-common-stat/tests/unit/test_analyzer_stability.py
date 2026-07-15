"""
Unit tests for stability trend analysis functionality in analyzer.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from scipy import stats

# Mock the analyzer functions for testing if needed, or test directly
# Since we need to test the logic, we will create temporary files.

from analyzer import analyze_stability_trend, aggregate_results, load_simulation_results

@pytest.fixture
def sample_raw_data():
    """Generate a sample raw p-values DataFrame simulating T021b output."""
    np.random.seed(42)
    n_samples = 100
    data = []
    
    # Simulate scenarios: n=10, 50, 100, 500
    # Distributions: normal, uniform
    # Tests: t-test, anova
    # Hypothesis: H0_true (for Type I error)
    
    sample_sizes = [10, 50, 100, 500]
    distributions = ['normal', 'uniform']
    tests = ['t-test', 'anova']
    
    for n in sample_sizes:
        for dist in distributions:
            for test in tests:
                # Generate random p-values
                # For H0, p-values should be uniform [0, 1]
                p_vals = np.random.uniform(0, 1, size=1000)
                rejected = (p_vals < 0.05).astype(int)
                
                for p, r in zip(p_vals, rejected):
                    data.append({
                        'n': n,
                        'distribution': dist,
                        'test_type': test,
                        'p_value': p,
                        'rejected': r,
                        'hypothesis_type': 'H0_true'
                    })
    
    return pd.DataFrame(data)

def test_analyze_stability_trend_integration(sample_raw_data):
    """Integration test for the full stability trend analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'raw_pvalues.csv')
        csv_out_path = os.path.join(tmpdir, 'stability_trend.csv')
        plot_out_path = os.path.join(tmpdir, 'plots', 'stability_trend.png')
        
        # Save input data
        sample_raw_data.to_csv(input_path, index=False)
        
        # Run analysis
        result_df = analyze_stability_trend(
            raw_input_path=input_path,
            csv_output_path=csv_out_path,
            plot_output_path=plot_out_path
        )
        
        # Assertions
        assert not result_df.empty, "Result DataFrame should not be empty"
        assert os.path.exists(csv_out_path), "CSV output file should exist"
        # Check plot files (might be named differently based on group)
        # The function saves plots with group names appended
        plot_files = [f for f in os.listdir(os.path.dirname(plot_out_path)) if f.endswith('.png')]
        assert len(plot_files) > 0, "Plot files should be generated"
        
        # Check columns in result
        expected_cols = ['distribution', 'test_type', 'slope', 'intercept', 'r_squared', 'p_value_trend', 'std_err', 'n_points']
        assert all(col in result_df.columns for col in expected_cols), "Result should have expected columns"
        
        # Check that we have results for each combination
        assert len(result_df) == len(sample_raw_data['distribution'].unique()) * len(sample_raw_data['test_type'].unique())
        
        # Verify regression logic: for H0, error rate should be ~0.05, slope should be near 0 (or slightly negative due to discreteness)
        # We just check that the regression ran without error and produced reasonable R^2
        assert all(result_df['r_squared'] >= 0), "R^2 should be non-negative"
        assert all(result_df['n_points'] > 0), "Should have at least one point per group"