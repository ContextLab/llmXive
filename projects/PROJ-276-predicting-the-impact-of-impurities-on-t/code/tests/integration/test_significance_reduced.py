"""
Integration test for T026a: Significance testing on reduced feature set.

This test verifies that the significance testing pipeline works correctly
on the output of T026 (reduced_feature_set.csv).
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path

from code.src.modeling.significance_test import run_significance_test_on_reduced_set


@pytest.fixture
def simulated_reduced_feature_set():
    """
    Simulate a reduced feature set that would be output by T026.
    
    This dataset has:
    - No collinear features (VIF < 5 for all)
    - Mix of significant and non-significant impurities
    - Realistic Tc values for MgB2
    """
    np.random.seed(42)
    n_samples = 200
    
    # Create features with low correlation
    data = {
        'Tc': np.random.normal(39, 8, n_samples),
        'impurity_Al': np.random.uniform(0, 3, n_samples),
        'impurity_C': np.random.uniform(0, 2, n_samples),
        'impurity_Si': np.random.uniform(0, 1, n_samples),
        'impurity_Fe': np.random.uniform(0, 0.5, n_samples),
        'impurity_Mn': np.random.uniform(0, 0.3, n_samples),
    }
    
    # Add some correlation with Tc for testing
    data['Tc'] = (
        39 
        - 2.5 * data['impurity_Al']  # Significant negative effect
        - 3.0 * data['impurity_C']   # Significant negative effect
        + 0.1 * data['impurity_Si']  # Non-significant
        - 5.0 * data['impurity_Fe']  # Significant negative effect
        + 0.05 * data['impurity_Mn'] # Non-significant
        + np.random.normal(0, 3, n_samples)  # Noise
    )
    
    return pd.DataFrame(data)


def test_full_significance_pipeline_on_reduced_set(simulated_reduced_feature_set):
    """
    Integration test: Run full significance testing pipeline on reduced feature set.
    
    Verifies:
    1. Pipeline executes without error
    2. Output file is created
    3. Results contain expected structure
    4. Significant features are correctly identified
    5. VIF verification shows low collinearity
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "reduced_feature_set.csv")
        output_path = os.path.join(tmpdir, "significance_results.json")
        
        # Save simulated data
        simulated_reduced_feature_set.to_csv(input_path, index=False)
        
        # Run significance test
        results = run_significance_test_on_reduced_set(
            input_path,
            output_path,
            target_col='Tc',
            vif_threshold=5.0,
            pvalue_threshold=0.05
        )
        
        # Verify output file exists
        assert os.path.exists(output_path), "Output file should be created"
        
        # Verify results structure
        assert 'total_features' in results
        assert 'significant_features' in results
        assert 'all_pvalues' in results
        assert 'significant_pvalues' in results
        assert 'vif_verification' in results
        
        # Verify significant features are identified
        assert results['significant_features'] > 0, "Should identify significant features"
        
        # Verify VIF is low on reduced set
        vif_values = [item['VIF'] for item in results['vif_verification']]
        assert all(v < 5.0 for v in vif_values), "All VIF should be < 5.0 on reduced set"
        
        # Verify p-values are in valid range
        for pval in results['all_pvalues']:
            assert 0 <= pval['p_value'] <= 1, f"P-value {pval['p_value']} out of range"
        
        # Verify significant p-values are indeed significant
        for pval in results['significant_pvalues']:
            assert pval['p_value'] < 0.05, f"Significant p-value {pval['p_value']} should be < 0.05"
        
        print(f"Integration test passed: {results['significant_features']} significant features found")
        print(f"VIF range: {min(vif_values):.2f} - {max(vif_values):.2f}")


def test_significance_pipeline_with_realistic_data():
    """
    Test with more realistic data distribution.
    
    Creates a dataset where:
    - Some impurities have strong effects
    - Some have weak/no effects
    - Features are intentionally non-collinear
    """
    np.random.seed(123)
    n_samples = 150
    
    data = {
        'Tc': np.zeros(n_samples),
        'impurity_Al': np.random.exponential(0.5, n_samples),
        'impurity_C': np.random.exponential(0.3, n_samples),
        'impurity_N': np.random.exponential(0.2, n_samples),
        'impurity_O': np.random.exponential(0.1, n_samples),
    }
    
    # Realistic Tc model
    data['Tc'] = (
        39.2
        - 1.8 * data['impurity_Al']
        - 2.2 * data['impurity_C']
        - 0.3 * data['impurity_N']  # Weak effect
        - 0.1 * data['impurity_O']  # Very weak effect
        + np.random.normal(0, 2.5, n_samples)
    )
    
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "reduced_feature_set.csv")
        output_path = os.path.join(tmpdir, "significance_results.json")
        
        df.to_csv(input_path, index=False)
        
        results = run_significance_test_on_reduced_set(
            input_path,
            output_path,
            target_col='Tc',
            pvalue_threshold=0.05
        )
        
        # Should find at least 2 significant features (Al and C)
        assert results['significant_features'] >= 2, \
            f"Expected at least 2 significant features, got {results['significant_features']}"
        
        # Verify the correct features are significant
        sig_features = [p['feature'] for p in results['significant_pvalues']]
        assert 'impurity_Al' in sig_features, "Al should be significant"
        assert 'impurity_C' in sig_features, "C should be significant"
        
        print(f"Realistic data test passed: {sig_features}")
