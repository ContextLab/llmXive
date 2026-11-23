"""
Contract test for significance testing output (T026a).

Verifies that the significance testing module produces output
that satisfies the contract defined in the specification.
"""
import pytest
import pandas as pd
import json
import tempfile
import os

from code.src.modeling.significance_test import run_significance_test_on_reduced_set


def test_significance_output_schema():
    """
    Contract test: Verify output JSON has required schema.
    
    Required fields per spec:
    - total_features: int
    - significant_features: int
    - pvalue_threshold: float
    - vif_threshold: float
    - all_pvalues: list of {feature, p_value}
    - significant_pvalues: list of {feature, p_value}
    - vif_verification: list of {feature, VIF}
    """
    # Create minimal valid input
    data = pd.DataFrame({
        'Tc': [39, 38, 37, 36, 35],
        'impurity_Al': [0.1, 0.2, 0.3, 0.4, 0.5],
        'impurity_C': [0.05, 0.1, 0.15, 0.2, 0.25]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "reduced_feature_set.csv")
        output_path = os.path.join(tmpdir, "significance_results.json")
        
        data.to_csv(input_path, index=False)
        
        results = run_significance_test_on_reduced_set(input_path, output_path)
        
        # Verify schema
        assert isinstance(results['total_features'], int)
        assert isinstance(results['significant_features'], int)
        assert isinstance(results['pvalue_threshold'], float)
        assert isinstance(results['vif_threshold'], float)
        assert isinstance(results['all_pvalues'], list)
        assert isinstance(results['significant_pvalues'], list)
        assert isinstance(results['vif_verification'], list)
        
        # Verify all_pvalues structure
        for item in results['all_pvalues']:
            assert 'feature' in item
            assert 'p_value' in item
            assert isinstance(item['p_value'], float)
            assert 0 <= item['p_value'] <= 1
        
        # Verify vif_verification structure
        for item in results['vif_verification']:
            assert 'feature' in item
            assert 'VIF' in item
            assert isinstance(item['VIF'], (int, float))
            assert item['VIF'] >= 1  # VIF is always >= 1


def test_significance_consistency_with_input():
    """
    Contract test: Verify results are consistent with input data.
    
    - Number of features in results matches input
    - All input features appear in p-value results
    """
    data = pd.DataFrame({
        'Tc': list(range(39, 29, -1)),
        'impurity_A': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'impurity_B': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
        'impurity_C': [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "reduced_feature_set.csv")
        output_path = os.path.join(tmpdir, "significance_results.json")
        
        data.to_csv(input_path, index=False)
        
        results = run_significance_test_on_reduced_set(input_path, output_path)
        
        # Count features (excluding Tc)
        expected_features = 3
        
        assert results['total_features'] == expected_features
        assert len(results['all_pvalues']) == expected_features
        assert len(results['vif_verification']) == expected_features
        
        # Verify all features are present
        feature_names = [item['feature'] for item in results['all_pvalues']]
        assert 'impurity_A' in feature_names
        assert 'impurity_B' in feature_names
        assert 'impurity_C' in feature_names
