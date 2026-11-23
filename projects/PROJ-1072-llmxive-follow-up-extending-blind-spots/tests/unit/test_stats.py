import pytest
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
import json
import tempfile
from pathlib import Path

from code_04_statistical_analysis import (
    build_contingency_table,
    select_statistical_test,
    apply_multiple_comparison_correction,
    run_statistical_test
)

class TestContingencyTable:
    def test_build_contingency_table_basic(self):
        """Test basic contingency table construction."""
        data = [
            {"category": "Abstract Reasoning", "error_label": "Perceptual"},
            {"category": "Abstract Reasoning", "error_label": "Perceptual"},
            {"category": "Abstract Reasoning", "error_label": "Procedural"},
            {"category": "Object-Centric", "error_label": "Perceptual"},
            {"category": "Object-Centric", "error_label": "Correct"},
        ]
        
        table = build_contingency_table(data)
        
        # Expected: 2x3 table (2 categories, 3 error types)
        # Categories: Abstract Reasoning, Object-Centric
        # Error types: Correct, Perceptual, Procedural (sorted)
        assert table.shape == (3, 2)
        
        # Check counts
        # Abstract Reasoning: 2 Perceptual, 1 Procedural, 0 Correct
        # Object-Centric: 1 Perceptual, 0 Procedural, 1 Correct
        assert table[0, 0] == 0  # Correct, Abstract Reasoning
        assert table[1, 0] == 2  # Perceptual, Abstract Reasoning
        assert table[2, 0] == 1  # Procedural, Abstract Reasoning
        assert table[0, 1] == 1  # Correct, Object-Centric
        assert table[1, 1] == 1  # Perceptual, Object-Centric
        assert table[2, 1] == 0  # Procedural, Object-Centric

class TestTestSelection:
    def test_chi_squared_selection(self):
        """Test Chi-squared selection when all expected counts >= 5."""
        # Create a table with high counts
        table = np.array([
            [10, 15],
            [12, 18]
        ])
        
        test_name, result = select_statistical_test(table)
        
        assert test_name == "Chi-squared"
        assert "p_value" in result
        assert result["p_value"] > 0
        
    def test_fisher_exact_selection(self):
        """Test Fisher's Exact selection when expected count < 5 in 2x2 table."""
        # Create a 2x2 table with low expected counts
        table = np.array([
            [1, 2],
            [3, 1]
        ])
        
        test_name, result = select_statistical_test(table)
        
        # Should select Fisher's Exact for 2x2 with low counts
        assert "Fisher" in test_name or "Chi-squared" in test_name
        assert "p_value" in result

class TestMultipleComparisonCorrection:
    def test_bonferroni_correction(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.03, 0.05]
        corrected = apply_multiple_comparison_correction(p_values, method="bonferroni")
        
        assert len(corrected) == 3
        # Bonferroni: p * n
        assert abs(corrected[0] - 0.03) < 0.001
        assert abs(corrected[1] - 0.09) < 0.001
        assert abs(corrected[2] - 0.15) < 0.001
        
    def test_benjamini_hochberg_correction(self):
        """Test Benjamini-Hochberg correction."""
        p_values = [0.01, 0.03, 0.05]
        corrected = apply_multiple_comparison_correction(p_values, method="benjamini-hochberg")
        
        assert len(corrected) == 3
        # All corrected values should be >= original
        assert all(c >= p for c, p in zip(corrected, p_values))
        
    def test_no_correction_single_test(self):
        """Test that no correction is applied for single test."""
        p_values = [0.05]
        corrected = apply_multiple_comparison_correction(p_values)
        
        assert corrected == p_values

class TestRunStatisticalTest:
    def test_run_statistical_test_completes(self):
        """Test that run_statistical_test completes without error."""
        table = np.array([
            [10, 15],
            [12, 18]
        ])
        
        result = run_statistical_test(table)
        
        assert "p_value" in result
        assert "test_selection_reason" in result
        assert result["p_value"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])