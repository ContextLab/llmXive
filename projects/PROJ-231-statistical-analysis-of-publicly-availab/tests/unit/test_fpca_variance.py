import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fpca import calculate_cumulative_variance, perform_fpca

class TestCumulativeVariance:
    
    def test_cumulative_variance_calculation(self):
        """Test that cumulative variance is calculated correctly."""
        # Create mock FPCA results
        eigenvalues = np.array([4.0, 2.0, 1.0, 0.5, 0.1])
        # Total variance = 7.6
        # Ratios: 4/7.6, 2/7.6, ...
        total_var = eigenvalues.sum()
        ratios = eigenvalues / total_var
        
        fpca_results = {
            "eigenvalues": eigenvalues,
            "explained_variance_ratio": ratios,
            "n_components": len(eigenvalues)
        }
        
        result = calculate_cumulative_variance(fpca_results)
        
        expected_cumulative = np.cumsum(ratios)
        np.testing.assert_array_almost_equal(
            np.array(result["cumulative_variance"]), 
            expected_cumulative
        )
    
    def test_stopping_at_80_percent(self):
        """Test that the correct number of components is selected to reach 80%."""
        # Eigenvalues: [10, 5, 2, 1] -> Total 18
        # Ratios: [0.555, 0.277, 0.111, 0.055]
        # Cumulative: [0.555, 0.833, 0.944, 1.0]
        # 80% is reached at index 1 (2 components)
        
        eigenvalues = np.array([10.0, 5.0, 2.0, 1.0])
        total_var = eigenvalues.sum()
        ratios = eigenvalues / total_var
        
        fpca_results = {
            "eigenvalues": eigenvalues,
            "explained_variance_ratio": ratios,
            "n_components": 4
        }
        
        result = calculate_cumulative_variance(fpca_results, threshold=0.80)
        
        assert result["n_components_selected"] == 2
        assert result["total_variance_explained"] >= 0.80
        assert result["total_variance_explained"] < 0.95 # Should not include the 3rd component unnecessarily
    
    def test_threshold_not_reached(self):
        """Test behavior when threshold is not reached even with all components."""
        # This shouldn't happen in PCA (sum is 1.0), but test robustness
        eigenvalues = np.array([1.0, 0.1])
        ratios = eigenvalues / eigenvalues.sum()
        
        fpca_results = {
            "eigenvalues": eigenvalues,
            "explained_variance_ratio": ratios,
            "n_components": 2
        }
        
        # Set threshold > 1.0 to force full selection
        result = calculate_cumulative_variance(fpca_results, threshold=1.5)
        
        assert result["n_components_selected"] == 2
        assert result["total_variance_explained"] == 1.0
    
    def test_output_structure(self):
        """Test that the output dictionary contains all required keys."""
        eigenvalues = np.array([1.0, 0.5])
        ratios = eigenvalues / eigenvalues.sum()
        
        fpca_results = {
            "eigenvalues": eigenvalues,
            "explained_variance_ratio": ratios,
            "n_components": 2
        }
        
        result = calculate_cumulative_variance(fpca_results)
        
        required_keys = [
            "cumulative_variance", 
            "n_components_selected", 
            "total_variance_explained", 
            "threshold",
            "all_eigenvalues",
            "all_variance_ratios"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_json_serialization(self):
        """Test that the result can be serialized to JSON."""
        eigenvalues = np.array([1.0, 0.5])
        ratios = eigenvalues / eigenvalues.sum()
        
        fpca_results = {
            "eigenvalues": eigenvalues,
            "explained_variance_ratio": ratios,
            "n_components": 2
        }
        
        result = calculate_cumulative_variance(fpca_results)
        
        # This should not raise an exception
        json_str = json.dumps(result)
        assert len(json_str) > 0
        
        # Verify we can load it back
        loaded = json.loads(json_str)
        assert loaded["n_components_selected"] == result["n_components_selected"]