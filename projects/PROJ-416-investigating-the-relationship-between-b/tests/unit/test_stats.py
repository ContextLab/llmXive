"""
Unit tests for code/analysis/stats.py.
Verifies FDR correction logic and VIF calculation as per T026.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.stats import calculate_vif, apply_fdr_correction, CollinearityUnresolvableError


class TestCalculateVIF:
    """Tests for the calculate_vif function."""

    def test_vif_perfect_collinearity(self):
        """Test that VIF returns high value for perfect collinearity."""
        # Create a dataframe with two perfectly correlated columns
        data = {
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_b': [2.0, 4.0, 6.0, 8.0, 10.0]  # Exactly 2 * feature_a
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif(df)
        
        # Both features should have very high VIF
        assert 'feature_a' in vif_results
        assert 'feature_b' in vif_results
        assert vif_results['feature_a'] > 1000  # Threshold for perfect collinearity
        assert vif_results['feature_b'] > 1000

    def test_vif_no_collinearity(self):
        """Test that VIF returns ~1 for independent features."""
        # Create a dataframe with independent features
        np.random.seed(42)
        data = {
            'feature_a': np.random.randn(100),
            'feature_b': np.random.randn(100),
            'feature_c': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif(df)
        
        # VIF should be close to 1 for independent features
        for feature, vif_val in vif_results.items():
            assert 0.9 < vif_val < 1.5, f"VIF for {feature} is {vif_val}, expected ~1"

    def test_vif_empty_dataframe(self):
        """Test that VIF handles empty dataframe gracefully."""
        df = pd.DataFrame()
        vif_results = calculate_vif(df)
        assert vif_results == {}

    def test_vif_single_feature(self):
        """Test that VIF handles single feature (VIF=1 by definition)."""
        data = {
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        vif_results = calculate_vif(df)
        
        assert 'feature_a' in vif_results
        # VIF for a single feature is 1 (no other features to correlate with)
        assert vif_results['feature_a'] == 1.0


class TestApplyFDRCorrection:
    """Tests for the apply_fdr_correction function."""

    def test_fdr_correction_basic(self):
        """Test basic FDR correction on a known set of p-values."""
        # Known p-values
        p_values = [0.01, 0.03, 0.04, 0.08, 0.15]
        
        corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        assert len(corrected) == len(p_values)
        # FDR corrected values should be >= original values
        for orig, corr in zip(p_values, corrected):
            assert corr >= orig

    def test_fdr_correction_empty_list(self):
        """Test that FDR correction handles empty list."""
        corrected = apply_fdr_correction([], alpha=0.05)
        assert corrected == []

    def test_fdr_correction_all_significant(self):
        """Test FDR correction where all p-values are significant."""
        p_values = [0.001, 0.002, 0.003]
        
        corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        # All should still be < 0.05 after correction
        assert all(p < 0.05 for p in corrected)

    def test_fdr_correction_monotonicity(self):
        """Test that corrected p-values maintain monotonicity relative to rank."""
        p_values = [0.05, 0.02, 0.08, 0.01]
        
        corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        # The Benjamini-Hochberg procedure ensures monotonicity
        # Sort original and corrected to check relationship
        sorted_indices = np.argsort(p_values)
        sorted_orig = [p_values[i] for i in sorted_indices]
        sorted_corr = [corrected[i] for i in sorted_indices]
        
        # Corrected p-values should be non-decreasing with respect to rank
        for i in range(len(sorted_corr) - 1):
            assert sorted_corr[i] <= sorted_corr[i+1]

    def test_fdr_correction_alpha_threshold(self):
        """Test that FDR correction respects the alpha threshold."""
        # Create p-values where some should be significant and some not
        p_values = [0.01, 0.02, 0.06, 0.07, 0.20]
        
        corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        # Count how many are significant after correction
        significant_count = sum(1 for p in corrected if p < 0.05)
        # We expect at least the first two to be significant
        assert significant_count >= 2


class TestIntegration:
    """Integration tests combining VIF and FDR logic."""

    def test_vif_fdr_pipeline(self):
        """Test the typical pipeline: calculate VIF, then apply FDR if needed."""
        # Create data with moderate collinearity
        np.random.seed(42)
        n = 50
        data = {
            'feature_1': np.random.randn(n),
            'feature_2': np.random.randn(n),
            'feature_3': np.random.randn(n) + 0.5 * np.random.randn(n)  # Slight correlation
        }
        df = pd.DataFrame(data)
        
        # Calculate VIF
        vif_results = calculate_vif(df)
        
        # Generate some p-values for a hypothetical test
        p_values = [0.01, 0.03, 0.04]
        
        # Apply FDR
        corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        # Verify both operations completed successfully
        assert len(vif_results) == 3
        assert len(corrected) == 3
        assert all(isinstance(v, float) for v in vif_results.values())
        assert all(isinstance(p, float) for p in corrected)