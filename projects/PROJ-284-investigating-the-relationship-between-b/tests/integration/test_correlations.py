"""
Integration tests for the correlation analysis module.
Tests T019: Integration test with synthetic data verifying r, p, q values.
Tests T024: Spearman/Pearson correlation with FD covariate.
Tests T025: FDR Correction.
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from scipy import stats

# Import the module under test
from code.analysis.correlations import (
    compute_and_save_correlation_matrix,
    apply_fdr_correction,
    partial_correlation,
    load_metrics_data
)

class TestCorrelationWithSyntheticData:
    """
    Integration test: test_correlation_with_synthetic_data.
    
    Verifies that:
    1. The correlation function runs without error on synthetic data.
    2. The output contains expected columns (metric_name, r, p, q, significant).
    3. The results match ground truth within tolerance for a known synthetic dataset.
    """
    
    def test_correlation_with_synthetic_data(self):
        """
        Generate synthetic data with a known correlation structure and verify
        that the computed r, p, and q values match expectations.
        
        NOTE: This is an integration test for the ANALYSIS LOGIC using synthetic
        INPUT data to establish ground truth. This is distinct from the main
        pipeline which must use real HCP data.
        """
        # Setup: Create synthetic data
        np.random.seed(42)
        n_subjects = 100
        
        # Create ground truth:
        # Metric A has a strong positive correlation with Motor Score (r ~ 0.5)
        # Metric B has no correlation (r ~ 0.0)
        # FD is correlated with Metric A (to test covariate effect)
        
        fd = np.random.normal(0.2, 0.1, n_subjects)
        motor_score = np.random.normal(50, 10, n_subjects)
        
        # Metric A: Correlated with Motor Score
        # motor = 0.5 * metric_a + noise
        metric_a = np.random.normal(0.5, 0.1, n_subjects)
        motor_score = 10 * metric_a + np.random.normal(0, 1, n_subjects)
        
        # Metric B: Independent
        metric_b = np.random.normal(0.5, 0.1, n_subjects)
        
        # FD: Correlated with Metric A (to create a confound)
        fd = 0.5 * metric_a + np.random.normal(0, 0.05, n_subjects)
        
        df = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
            'modularity': metric_a, # Using modularity as the correlated metric
            'global_efficiency': metric_b,
            'participation_coef': np.random.normal(0.5, 0.1, n_subjects),
            'within_module_degree': np.random.normal(0.5, 0.1, n_subjects),
            'mean_fd': fd,
            'motor_score': motor_score
        })
        
        # Create temp directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            
            # Run the correlation function
            results = compute_and_save_correlation_matrix(
                df, 
                motor_score_col='motor_score',
                output_dir=str(output_path)
            )
            
            # Assertions
            assert results is not None
            assert not results.empty
            
            # Check columns
            required_cols = ['metric_name', 'r', 'p', 'q', 'significant']
            for col in required_cols:
                assert col in results.columns, f"Missing column: {col}"
                
            # Check specific results
            # Modularity should be significant and have r > 0.3
            mod_row = results[results['metric_name'] == 'modularity']
            assert not mod_row.empty
            
            r_val = mod_row['r'].values[0]
            q_val = mod_row['q'].values[0]
            sig = mod_row['significant'].values[0]
            
            # Verify strong correlation (r > 0.3)
            assert r_val > 0.3, f"Expected r > 0.3, got {r_val}"
            
            # Verify significance after FDR
            assert sig, f"Expected modularity to be significant, but q={q_val}"
            
            # Global Efficiency should NOT be significant
            ge_row = results[results['metric_name'] == 'global_efficiency']
            if not ge_row.empty:
                ge_sig = ge_row['significant'].values[0]
                # It's okay if it's not significant
                assert not ge_sig or ge_row['q'].values[0] > 0.05, "Global efficiency should not be significant"
                
            # Verify file was written
            csv_path = output_path / "correlation_results.csv"
            assert csv_path.exists(), "Correlation results CSV was not written"
            
            # Re-load and verify
            reloaded = pd.read_csv(csv_path)
            assert len(reloaded) == len(results)
            
        print("Integration test passed: Correlation with synthetic data works correctly.")

def test_partial_correlation_manual():
    """
    Unit test for the partial_correlation helper function.
    """
    # Construct data where x and y are correlated, but z explains the correlation
    # x = z + noise
    # y = z + noise
    # x and y should have low partial correlation controlling for z
    
    np.random.seed(123)
    n = 50
    z = np.random.normal(0, 1, n)
    x = z + np.random.normal(0, 0.1, n)
    y = z + np.random.normal(0, 0.1, n)
    
    r, p = partial_correlation(x, y, z)
    
    # The partial correlation should be close to 0
    assert abs(r) < 0.2, f"Partial correlation should be near 0, got {r}"
    assert p > 0.05, f"Partial correlation p-value should be > 0.05, got {p}"
    
    # Now test without controlling for z (should be high)
    r_full, p_full = stats.pearsonr(x, y)
    assert r_full > 0.8, f"Full correlation should be high, got {r_full}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
