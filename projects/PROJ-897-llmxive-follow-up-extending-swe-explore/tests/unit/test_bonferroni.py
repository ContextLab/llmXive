"""
Unit tests for Bonferroni correction and associational framing.
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.stats import apply_bonferroni_correction, format_associational_statement

class TestBonferroniCorrection:
    def test_basic_correction(self):
        """Test basic Bonferroni correction logic."""
        p_values = [0.01, 0.04, 0.06]
        corrected, significant = apply_bonferroni_correction(p_values, alpha=0.05)
        
        # Expected: 0.01*3=0.03, 0.04*3=0.12, 0.06*3=0.18
        assert abs(corrected[0] - 0.03) < 1e-6
        assert abs(corrected[1] - 0.12) < 1e-6
        assert abs(corrected[2] - 0.18) < 1e-6
        
        # Significance check
        assert significant[0] is True   # 0.03 < 0.05
        assert significant[1] is False  # 0.12 > 0.05
        assert significant[2] is False  # 0.18 > 0.05

    def test_p_value_capping(self):
        """Test that p-values are capped at 1.0."""
        p_values = [0.5, 0.6]
        corrected, _ = apply_bonferroni_correction(p_values, alpha=0.05)
        
        assert corrected[0] == 1.0
        assert corrected[1] == 1.0

    def test_empty_list(self):
        """Test handling of empty p-value list."""
        corrected, significant = apply_bonferroni_correction([], alpha=0.05)
        assert corrected == []
        assert significant == []

class TestAssociationalFraming:
    def test_significant_statement(self):
        """Test generation of significant associational statement."""
        stmt = format_associational_statement(
            "coverage", True, 0.03, "higher"
        )
        assert "statistically significant associational difference" in stmt
        assert "p = 0.0300" in stmt
        assert "higher" in stmt
        assert "causal" not in stmt.lower()

    def test_non_significant_statement(self):
        """Test generation of non-significant associational statement."""
        stmt = format_associational_statement(
            "ranking", False, 0.15, "lower"
        )
        assert "No statistically significant associational difference" in stmt
        assert "p = 0.1500" in stmt
        assert "causal" not in stmt.lower()

    def test_framing_constraint(self):
        """Ensure no causal language is used."""
        stmt = format_associational_statement("test", True, 0.01, "better")
        assert "cause" not in stmt.lower()
        assert "causes" not in stmt.lower()
        assert "effect" not in stmt.lower()
        assert "proves" not in stmt.lower()
        assert "demonstrates causality" not in stmt.lower()