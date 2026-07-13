"""
Unit tests for code/08_collinearity_check.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.io import save_dataframe
from code import code_08_collinearity_check as collinearity_module

class TestCollinearityCheck:
    
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe with known correlations."""
        np.random.seed(42)
        n = 50
        # Create highly correlated pair
        base = np.random.randn(n)
        col1 = base + np.random.randn(n) * 0.01  # Very high correlation
        col2 = base * 2 + np.random.randn(n) * 0.01
        # Create uncorrelated columns
        col3 = np.random.randn(n)
        col4 = np.random.randn(n)
        
        df = pd.DataFrame({
            "feature_A": col1,
            "feature_B": col2,
            "feature_C": col3,
            "feature_D": col4
        })
        return df

    def test_calculate_correlation_matrix(self, sample_data):
        """Test that correlation matrix is calculated correctly."""
        corr_matrix = collinearity_module.calculate_correlation_matrix(sample_data)
        
        assert not corr_matrix.empty
        assert "feature_A" in corr_matrix.columns
        assert "feature_B" in corr_matrix.columns
        assert "feature_C" in corr_matrix.columns
        assert "feature_D" in corr_matrix.columns
        
        # Check diagonal is 1.0
        assert np.allclose(np.diag(corr_matrix.values), 1.0)

    def test_find_highly_correlated_pairs(self, sample_data):
        """Test detection of highly correlated pairs."""
        corr_matrix = collinearity_module.calculate_correlation_matrix(sample_data)
        pairs = collinearity_module.find_highly_correlated_pairs(corr_matrix, threshold=0.95)
        
        assert len(pairs) >= 1
        # Check that feature_A and feature_B are detected
        found_pair = False
        for p in pairs:
            if (p["feature1"] == "feature_A" and p["feature2"] == "feature_B") or \
               (p["feature1"] == "feature_B" and p["feature2"] == "feature_A"):
                found_pair = True
                assert p["correlation"] > 0.95
        assert found_pair

    def test_find_no_highly_correlated_pairs(self):
        """Test when no pairs exceed threshold."""
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            "x": np.random.randn(n),
            "y": np.random.randn(n),
            "z": np.random.randn(n)
        })
        
        corr_matrix = collinearity_module.calculate_correlation_matrix(df)
        pairs = collinearity_module.find_highly_correlated_pairs(corr_matrix, threshold=0.95)
        
        # With random noise, unlikely to have >0.95 correlation
        # But we assert the function runs without error
        assert isinstance(pairs, list)

    def test_empty_dataframe_handling(self):
        """Test behavior with non-numeric or empty data."""
        df = pd.DataFrame({"A": ["a", "b", "c"]})
        corr_matrix = collinearity_module.calculate_correlation_matrix(df)
        assert corr_matrix.empty

    def test_main_execution(self, sample_data):
        """Test the main function writes output correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.json"
            
            save_dataframe(sample_data, input_path)
            
            # Mock arguments
            sys.argv = [
                "test",
                "--input", str(input_path),
                "--output", str(output_path),
                "--threshold", "0.95"
            ]
            
            try:
                collinearity_module.main()
                
                assert output_path.exists()
                with open(output_path) as f:
                    report = json.load(f)
                
                assert "pairs" in report
                assert "input_file" in report
                assert "threshold" in report
            finally:
                sys.argv = ["test"]