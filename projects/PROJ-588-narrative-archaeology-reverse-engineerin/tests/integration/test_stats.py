import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.stats import permutation_test, apply_fdr_correction, run_group_permutation_analysis

class TestPermutationTest:
    def test_permutation_test_deterministic(self):
        """Test that permutation test is deterministic with a fixed seed."""
        np.random.seed(42)
        data_early = np.random.randn(20, 10)
        data_late = np.random.randn(20, 10)
        
        p1 = permutation_test(data_early, data_late, n_iterations=100, random_seed=123)
        p2 = permutation_test(data_early, data_late, n_iterations=100, random_seed=123)
        
        assert p1 == p2, "Permutation test should be deterministic with fixed seed"
        
    def test_permutation_test_significant_difference(self):
        """Test that permutation test detects a significant difference."""
        # Create distinct groups
        data_early = np.random.randn(50, 10) + 5.0  # Shifted mean
        data_late = np.random.randn(50, 10)
        
        p_val = permutation_test(data_early, data_late, n_iterations=1000, random_seed=42)
        
        # With a large shift, p-value should be very low
        assert p_val < 0.05, f"Expected significant p-value, got {p_val}"

class TestFDRCorrection:
    def test_fdr_correction_basic(self):
        """Test basic FDR correction functionality."""
        p_values = [0.01, 0.03, 0.04, 0.06, 0.10, 0.20]
        adj_p, significant = apply_fdr_correction(p_values, alpha=0.05)
        
        assert len(adj_p) == len(p_values)
        assert len(significant) == len(p_values)
        # First few should be significant
        assert significant[0] == True, "First p-value (0.01) should be significant"
        
    def test_fdr_correction_empty(self):
        """Test FDR correction with empty input."""
        adj_p, significant = apply_fdr_correction([], alpha=0.05)
        assert adj_p == []
        assert significant == []

class TestGroupPermutationAnalysis:
    def test_run_group_permutation_analysis_structure(self, tmp_path):
        """Test that the group analysis produces the correct output structure."""
        # Mock data
        roi_data = {
            'hippocampus': {
                'early': np.random.randn(10, 5),
                'late': np.random.randn(10, 5)
            },
            'mPFC': {
                'early': np.random.randn(10, 5),
                'late': np.random.randn(10, 5)
            }
        }
        
        output_file = tmp_path / "test_permutation.json"
        
        results = run_group_permutation_analysis(
            roi_data,
            n_iterations=100, # Reduced for speed
            output_path=str(output_file)
        )
        
        # Verify structure
        assert "n_iterations" in results
        assert "rois" in results
        assert "raw_p_values" in results
        assert "adj_p_values" in results
        assert "significant" in results
        
        # Verify file was written
        assert output_file.exists()
        with open(output_file, 'r') as f:
            written_data = json.load(f)
            
        assert written_data["n_iterations"] == 100
        assert 'hippocampus' in written_data["rois"]
        assert 'mPFC' in written_data["rois"]
        assert "p_value" in written_data["rois"]["hippocampus"]
        assert "significant_fdr" in written_data["rois"]["hippocampus"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
