import numpy as np
import pytest
import json
from pathlib import Path
from code.fdr_correction import apply_benjamini_hochberg, apply_fdr_to_model_results
from code.logger import get_logger

logger = get_logger(__name__)

class TestBenjaminiHochberg:
    """Unit tests for the Benjamini-Hochberg FDR correction implementation."""

    def test_basic_rejection(self):
        """Test basic rejection logic with known p-values."""
        # Known p-values: [0.01, 0.04, 0.03, 0.005, 0.001]
        # Sorted: [0.001, 0.01, 0.03, 0.04, 0.005] -> actually [0.001, 0.01, 0.03, 0.04, 0.005]
        # Wait, let's sort properly: [0.001, 0.005, 0.01, 0.03, 0.04]
        # Ranks: 1, 2, 3, 4, 5
        # Critical values (alpha=0.05, n=5): [0.01, 0.02, 0.03, 0.04, 0.05]
        # Comparison: 
        # 0.001 <= 0.01 (True)
        # 0.005 <= 0.02 (True)
        # 0.01 <= 0.03 (True)
        # 0.03 <= 0.04 (True)
        # 0.04 <= 0.05 (True)
        # All should be rejected
        p_vals = np.array([0.01, 0.04, 0.03, 0.005, 0.001])
        rejected = apply_benjamini_hochberg(p_vals, alpha=0.05)
        
        assert np.all(rejected), "All p-values should be rejected in this case"
        assert len(rejected) == 5

    def test_no_rejection(self):
        """Test case where no p-values are significant."""
        p_vals = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        rejected = apply_benjamini_hochberg(p_vals, alpha=0.05)
        
        assert not np.any(rejected), "No p-values should be rejected"
        assert len(rejected) == 5

    def test_partial_rejection(self):
        """Test case with mixed results."""
        # p-values: [0.001, 0.01, 0.05, 0.1, 0.2]
        # Sorted: same
        # Critical: [0.01, 0.02, 0.03, 0.04, 0.05]
        # 0.001 <= 0.01 (True)
        # 0.01 <= 0.02 (True)
        # 0.05 <= 0.03 (False) -> stop here, k=2
        # So first two should be rejected
        p_vals = np.array([0.001, 0.01, 0.05, 0.1, 0.2])
        rejected = apply_benjamini_hochberg(p_vals, alpha=0.05)
        
        # First two should be True, rest False
        expected = np.array([True, True, False, False, False])
        assert np.array_equal(rejected, expected), f"Expected {expected}, got {rejected}"

    def test_empty_array(self):
        """Test with empty array."""
        p_vals = np.array([])
        rejected = apply_benjamini_hochberg(p_vals)
        assert len(rejected) == 0

    def test_single_value_significant(self):
        """Test with a single significant p-value."""
        p_vals = np.array([0.01])
        rejected = apply_benjamini_hochberg(p_vals, alpha=0.05)
        assert rejected[0] == True

    def test_single_value_not_significant(self):
        """Test with a single non-significant p-value."""
        p_vals = np.array([0.1])
        rejected = apply_benjamini_hochberg(p_vals, alpha=0.05)
        assert rejected[0] == False

class TestApplyFDRToModelResults:
    """Integration tests for applying FDR to model results structure."""

    def test_basic_fdr_application(self):
        """Test FDR application on a simple model result structure."""
        model_results = {
            'OLS': {
                'traffic_volume': {'coef': 0.5, 'robust_p_value': 0.001},
                'population_density': {'coef': 0.3, 'robust_p_value': 0.04},
                'land_use_residential': {'coef': -0.2, 'robust_p_value': 0.2}
            }
        }
        
        primary_covariates = ['traffic_volume', 'population_density', 'land_use_residential']
        corrected = apply_fdr_to_model_results(model_results, primary_covariates, alpha=0.05)
        
        # Check that FDR fields were added
        assert 'fdr_rejected' in corrected['OLS']['traffic_volume']
        assert 'fdr_adjusted_p' in corrected['OLS']['traffic_volume']
        
        # traffic_volume (0.001) and population_density (0.04) should likely be rejected
        # land_use_residential (0.2) should not
        assert corrected['OLS']['traffic_volume']['fdr_rejected'] == True
        assert corrected['OLS']['population_density']['fdr_rejected'] == True
        assert corrected['OLS']['land_use_residential']['fdr_rejected'] == False

    def test_missing_robust_p_value(self):
        """Test handling of missing robust_p_value."""
        model_results = {
            'OLS': {
                'traffic_volume': {'coef': 0.5, 'robust_p_value': 0.001},
                'population_density': {'coef': 0.3}  # Missing robust_p_value
            }
        }
        
        primary_covariates = ['traffic_volume', 'population_density']
        
        # Should not raise an error, just skip the missing one
        corrected = apply_fdr_to_model_results(model_results, primary_covariates, alpha=0.05)
        
        # traffic_volume should have FDR fields
        assert 'fdr_rejected' in corrected['OLS']['traffic_volume']
        # population_density should not (skipped)
        assert 'fdr_rejected' not in corrected['OLS']['population_density']

    def test_empty_primary_covariates(self):
        """Test with empty primary covariates list."""
        model_results = {
            'OLS': {
                'traffic_volume': {'coef': 0.5, 'robust_p_value': 0.001}
            }
        }
        
        corrected = apply_fdr_to_model_results(model_results, [], alpha=0.05)
        
        # No changes should be made
        assert 'fdr_rejected' not in corrected['OLS']['traffic_volume']

    def test_multiple_models(self):
        """Test FDR application across multiple model types."""
        model_results = {
            'OLS': {
                'traffic_volume': {'coef': 0.5, 'robust_p_value': 0.001}
            },
            'Spatial_Lag': {
                'traffic_volume': {'coef': 0.45, 'robust_p_value': 0.002}
            }
        }
        
        primary_covariates = ['traffic_volume']
        corrected = apply_fdr_to_model_results(model_results, primary_covariates, alpha=0.05)
        
        # Both models should have FDR applied
        assert 'fdr_rejected' in corrected['OLS']['traffic_volume']
        assert 'fdr_rejected' in corrected['Spatial_Lag']['traffic_volume']