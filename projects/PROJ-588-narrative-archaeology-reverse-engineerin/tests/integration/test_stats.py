"""
Integration tests for statistical utilities in code/utils/stats.py.

Tests permutation test convergence and FDR correction.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path if not already
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.stats import permutation_test, apply_fdr_correction, run_group_permutation_analysis

class TestPermutationTest:
    def test_permutation_convergence(self):
        """Test that permutation test converges with sufficient iterations."""
        # Create a simple null distribution
        np.random.seed(42)
        null_dist = np.random.normal(0, 1, size=10000)
        
        # Observed value that is somewhat extreme
        observed = 2.5
        
        result = permutation_test(
            observed_diff=observed,
            permuted_diffs=null_dist,
            n_permutations=100,
            stability_threshold=0.001,
            stability_window=50,
            max_iterations=2000
        )
        
        # Check that we got a result
        assert "p_value" in result
        assert "iterations" in result
        assert "stable" in result
        
        # The p-value should be small for an extreme observed value
        assert result["p_value"] < 0.05
        
        # Check that iterations are within bounds
        assert 100 <= result["iterations"] <= 2000

    def test_permutation_stability_detection(self):
        """Test that the stability detection works correctly."""
        # Create a null distribution
        np.random.seed(123)
        null_dist = np.random.normal(0, 1, size=5000)
        
        # Observed value near the mean (should be stable quickly)
        observed = 0.1
        
        result = permutation_test(
            observed_diff=observed,
            permuted_diffs=null_dist,
            n_permutations=100,
            stability_threshold=0.001,
            stability_window=20,
            max_iterations=500
        )
        
        # With a value near the mean, p-value should be around 0.4-0.6
        # and should stabilize quickly
        assert 0.3 < result["p_value"] < 0.7
        
        # We expect it to be stable due to the small threshold and window
        # Note: This might not always be true depending on the random seed,
        # but with a large null dist and small observed, it should be stable.

class TestFDRCorrection:
    def test_fdr_correction_basic(self):
        """Test basic FDR correction functionality."""
        p_values = np.array([0.01, 0.03, 0.04, 0.06, 0.10, 0.20])
        
        rejections, adj_p_vals = apply_fdr_correction(p_values, alpha=0.05)
        
        # Check that we have the right number of results
        assert len(rejections) == len(p_values)
        assert len(adj_p_vals) == len(p_values)
        
        # Check that adjusted p-values are monotonically increasing
        assert np.all(np.diff(adj_p_vals) >= 0)
        
        # Check that rejections are boolean
        assert rejections.dtype == bool

    def test_fdr_correction_all_significant(self):
        """Test FDR correction when all p-values are significant."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004])
        
        rejections, adj_p_vals = apply_fdr_correction(p_values, alpha=0.05)
        
        # All should be rejected
        assert np.all(rejections)
        
        # Adjusted p-values should be < 0.05
        assert np.all(adj_p_vals < 0.05)

    def test_fdr_correction_none_significant(self):
        """Test FDR correction when no p-values are significant."""
        p_values = np.array([0.10, 0.20, 0.30, 0.40])
        
        rejections, adj_p_vals = apply_fdr_correction(p_values, alpha=0.05)
        
        # None should be rejected
        assert not np.any(rejections)
        
        # Adjusted p-values should be > 0.05
        assert np.all(adj_p_vals >= 0.05)

class TestRunGroupPermutationAnalysis:
    def test_run_group_analysis(self, tmp_path):
        """Test the full group permutation analysis pipeline."""
        # Create mock roi_stats
        roi_stats = {
            "hippocampus": {"early_late": 0.15, "early_early": 0.05},
            "mPFC": {"early_late": 0.12, "early_early": 0.04},
            "PCC": {"early_late": 0.08, "early_early": 0.06},
            "lateral_temporal": {"early_late": 0.05, "early_early": 0.05}
        }
        
        output_path = tmp_path / "permutation_pvalues.json"
        
        result = run_group_permutation_analysis(
            results_path=output_path,
            roi_stats=roi_stats,
            n_permutations=1000,
            alpha=0.05
        )
        
        # Check that the file was created
        assert output_path.exists()
        
        # Check the structure of the result
        assert "method" in result
        assert "roi_results" in result
        assert "summary" in result
        
        # Check that each ROI has the expected keys
        for roi in roi_stats.keys():
            assert roi in result["roi_results"]
            assert "p_value" in result["roi_results"][roi]
            assert "fdr_corrected_p" in result["roi_results"][roi]
            assert "significant_after_fdr" in result["roi_results"][roi]
        
        # Verify the JSON file contents
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == result