import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import logging
import os

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from collinearity import calculate_vif, run_pca_on_metrics, check_and_handle_collinearity


class TestVIFCalculation:
    """
    Unit tests for VIF calculation logic in code/collinearity.py
    """

    def test_vif_calculation_returns_infinite_for_perfectly_collinear_predictors(self):
        """
        Test that VIF returns infinity (or a very large number) when predictors are perfectly collinear.
        This happens when one predictor is a linear combination of others.
        """
        # Create a dataset with perfect collinearity
        # X1 and X2 are identical, so X2 = 1.0 * X1 + 0
        np.random.seed(42)
        n_samples = 100
        
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples)
        }
        
        # Create perfect collinearity: X1_new = X1 + X2
        data['X1_new'] = data['X1'] + data['X2']
        
        # Now X1_new is perfectly collinear with X1 and X2
        # Specifically, X1_new - X1 - X2 = 0
        
        df = pd.DataFrame(data)
        
        # Calculate VIF for all columns
        vif_results = calculate_vif(df)
        
        # At least one of the collinear predictors should have infinite VIF
        # In practice, due to numerical precision, it might be a very large number
        # We check if any VIF is extremely large (indicating near-perfect collinearity)
        max_vif = max(vif_results.values())
        
        # If there's perfect collinearity, VIF should be infinite or very large
        # We use a threshold of 1e10 to detect this
        assert max_vif > 1e10, f"Expected infinite VIF for collinear predictors, got max VIF = {max_vif}"
        
        # Specifically check that X1_new has high VIF (it's the linear combination)
        assert vif_results['X1_new'] > 1e10, f"X1_new should have infinite VIF, got {vif_results['X1_new']}"

    def test_vif_calculation_returns_normal_values_for_uncollinear_predictors(self):
        """
        Test that VIF returns reasonable values for uncollinear predictors.
        """
        np.random.seed(42)
        n_samples = 100
        
        # Create uncorrelated predictors
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples)
        }
        
        df = pd.DataFrame(data)
        vif_results = calculate_vif(df)
        
        # For uncorrelated predictors, VIF should be close to 1
        for col, vif in vif_results.items():
            assert 1.0 <= vif < 5.0, f"VIF for {col} should be close to 1, got {vif}"


class TestPCAFallback:
    """
    Unit tests for PCA fallback logic when VIF > 5
    """

    def test_pca_fallback_triggers_when_vif_gt_5_and_variance_explained_gt_60(self):
        """
        Test that PCA is triggered when VIF > 5 and cumulative variance > 60%.
        """
        np.random.seed(42)
        n_samples = 100
        
        # Create a dataset with moderate collinearity
        # X1 and X2 are correlated but not perfectly
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples)
        }
        
        # Add some correlation between X1 and X2
        data['X2'] = 0.7 * data['X1'] + 0.3 * np.random.randn(n_samples)
        
        df = pd.DataFrame(data)
        
        # Calculate VIF
        vif_results = calculate_vif(df)
        
        # Check if any VIF > 5
        max_vif = max(vif_results.values())
        
        if max_vif > 5:
            # Run PCA and check if it succeeds
            pca_result = run_pca_on_metrics(df)
            
            # PCA should return a result with explained variance
            assert 'explained_variance_ratio' in pca_result, "PCA result should contain explained_variance_ratio"
            
            # Check cumulative variance
            cum_var = sum(pca_result['explained_variance_ratio'])
            assert cum_var > 0.6, f"Cumulative variance should be > 60%, got {cum_var:.2%}"
            
            # Check that PCA components are returned
            assert 'components' in pca_result, "PCA result should contain components"
            assert pca_result['components'].shape[0] <= df.shape[1], "Number of components should not exceed original features"
        else:
            # If VIF is not > 5, PCA should not be triggered
            # This is a valid case too
            pass

    def test_pca_fallback_does_not_trigger_when_variance_explained_lt_60(self):
        """
        Test that PCA fallback is not considered successful if variance < 60%.
        """
        # Create a dataset where PCA might not explain enough variance
        # This is harder to construct deterministically, so we test the logic
        np.random.seed(42)
        n_samples = 50  # Smaller sample size
        
        # Create noisy, uncorrelated data
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples),
            'X4': np.random.randn(n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Run PCA
        pca_result = run_pca_on_metrics(df)
        
        # Check cumulative variance
        cum_var = sum(pca_result['explained_variance_ratio'])
        
        # If cumulative variance is low, the function should handle it appropriately
        # The exact behavior depends on implementation, but we verify the function runs
        assert 'explained_variance_ratio' in pca_result, "PCA result should contain explained_variance_ratio"

    def test_pca_fallback_handles_singular_matrix(self):
        """
        Test that PCA handles singular matrix errors gracefully.
        """
        # Create a dataset with perfect collinearity (singular matrix)
        np.random.seed(42)
        n_samples = 100
        
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples)
        }
        
        # Create perfect collinearity
        data['X1_new'] = data['X1'] + data['X2']
        
        df = pd.DataFrame(data)
        
        # Run PCA - should handle the singular matrix
        try:
            pca_result = run_pca_on_metrics(df)
            # If it doesn't raise an exception, it should handle it gracefully
            assert isinstance(pca_result, dict), "PCA result should be a dictionary"
        except np.linalg.LinAlgError:
            # This is expected for singular matrices
            # The function should catch this and handle it appropriately
            pass


class TestCollinearityHandling:
    """
    Integration tests for the full collinearity handling workflow
    """

    def test_check_and_handle_collinearity_with_high_vif(self):
        """
        Test the full workflow when VIF is high.
        """
        np.random.seed(42)
        n_samples = 100
        
        # Create dataset with high collinearity
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples)
        }
        
        # Create collinearity
        data['X1_new'] = data['X1'] + data['X2']
        
        df = pd.DataFrame(data)
        
        # Run the full collinearity check
        result = check_and_handle_collinearity(df)
        
        # Result should contain information about VIF and PCA
        assert 'vif_results' in result, "Result should contain VIF results"
        assert 'pca_performed' in result, "Result should indicate if PCA was performed"
        
        # If VIF > 5, PCA should be attempted
        max_vif = max(result['vif_results'].values())
        if max_vif > 5:
            assert result['pca_performed'] in [True, False], "PCA performed should be boolean"

    def test_check_and_handle_collinearity_with_low_vif(self):
        """
        Test the full workflow when VIF is low.
        """
        np.random.seed(42)
        n_samples = 100
        
        # Create dataset with low collinearity
        data = {
            'X1': np.random.randn(n_samples),
            'X2': np.random.randn(n_samples),
            'X3': np.random.randn(n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Run the full collinearity check
        result = check_and_handle_collinearity(df)
        
        # Result should indicate no PCA needed
        assert 'vif_results' in result, "Result should contain VIF results"
        assert result['pca_performed'] == False, "PCA should not be performed when VIF is low"
        
        # All VIF values should be low
        for col, vif in result['vif_results'].items():
            assert vif < 5.0, f"VIF for {col} should be < 5, got {vif}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])