"""
Unit tests for the efficiency derivation validation logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the validation function
from code.validate_efficiency_derivation import validate_efficiency_formulas, TOLERANCE


class TestEfficiencyValidation:
    """Test cases for efficiency formula validation."""

    def test_perfect_global_efficiency(self):
        """Test with perfect global efficiency calculation."""
        # Create a dataframe with perfect data
        data = {
            "global_efficiency": [0.5, 0.25, 0.1],
            "characteristic_path_length": [2.0, 4.0, 10.0],
            "local_efficiency": [0.3, 0.2, 0.15],
            "local_path_length": [3.333333, 5.0, 6.666667]
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        assert results["formula_verified"] is True
        assert results["max_deviation"] < TOLERANCE
        assert results["details"]["global_efficiency"]["verified"] is True

    def test_perfect_local_efficiency(self):
        """Test with perfect local efficiency calculation."""
        data = {
            "global_efficiency": [0.5, 0.25],
            "characteristic_path_length": [2.0, 4.0],
            "local_efficiency": [0.333333, 0.25],
            "local_path_length": [3.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        assert results["formula_verified"] is True
        assert results["details"]["local_efficiency"]["verified"] is True

    def test_small_deviation(self):
        """Test with small deviation within tolerance."""
        # Create data with small deviation
        data = {
            "global_efficiency": [0.5000001, 0.2500001],
            "characteristic_path_length": [2.0, 4.0],
            "local_efficiency": [0.3333334, 0.2500001],
            "local_path_length": [3.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        # Should still pass as deviation is within tolerance
        assert results["formula_verified"] is True
        assert results["max_deviation"] < TOLERANCE

    def test_large_deviation(self):
        """Test with large deviation exceeding tolerance."""
        # Create data with large deviation
        data = {
            "global_efficiency": [0.6, 0.3],  # Wrong values
            "characteristic_path_length": [2.0, 4.0],
            "local_efficiency": [0.4, 0.3],  # Wrong values
            "local_path_length": [3.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        assert results["formula_verified"] is False
        assert results["max_deviation"] > TOLERANCE

    def test_missing_columns(self):
        """Test with missing required columns."""
        data = {
            "global_efficiency": [0.5],
            "characteristic_path_length": [2.0]
            # Missing local efficiency columns
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        assert "error" in results["details"]
        assert "Missing columns" in results["details"]["error"]

    def test_zero_path_length(self):
        """Test handling of zero path length (should be skipped)."""
        data = {
            "global_efficiency": [0.5, 0.0],
            "characteristic_path_length": [2.0, 0.0],  # Zero value
            "local_efficiency": [0.3, 0.0],
            "local_path_length": [3.0, 0.0]  # Zero value
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        # Should handle gracefully, only validate non-zero entries
        assert "global_efficiency" in results["details"]
        assert "local_efficiency" in results["details"]

    def test_nan_values(self):
        """Test handling of NaN values."""
        data = {
            "global_efficiency": [0.5, np.nan],
            "characteristic_path_length": [2.0, np.nan],
            "local_efficiency": [0.3, np.nan],
            "local_path_length": [3.0, np.nan]
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        # Should handle NaN values gracefully
        assert results["details"]["global_efficiency"]["sample_count"] == 1
        assert results["details"]["local_efficiency"]["sample_count"] == 1

    def test_empty_dataframe(self):
        """Test with empty dataframe."""
        data = {
            "global_efficiency": [],
            "characteristic_path_length": [],
            "local_efficiency": [],
            "local_path_length": []
        }
        df = pd.DataFrame(data)
        
        results = validate_efficiency_formulas(df)
        
        assert results["details"]["global_efficiency"]["sample_count"] == 0
        assert results["details"]["local_efficiency"]["sample_count"] == 0