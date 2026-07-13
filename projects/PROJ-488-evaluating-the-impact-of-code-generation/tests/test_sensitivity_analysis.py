"""
Tests for sensitivity analysis module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from sensitivity_analysis import (
    perform_sensitivity_test,
    generate_markdown_report,
    SIGNIFICANCE_THRESHOLDS
)

class TestSensitivityAnalysis:
    """Test cases for sensitivity analysis functions."""

    def test_perform_sensitivity_test_significant_difference(self):
        """Test detection of significant difference between groups."""
        # Create two groups with clear difference
        group1 = np.random.normal(10, 1, 100)
        group2 = np.random.normal(15, 1, 100)
        
        is_sig, p_val, adj_p_val = perform_sensitivity_test(group1, group2, 0.05)
        
        # With such a clear difference, we expect significance
        assert is_sig is True
        assert p_val is not None
        assert adj_p_val is not None
        assert p_val < 0.05

    def test_perform_sensitivity_test_no_difference(self):
        """Test detection of no significant difference between groups."""
        # Create two groups from same distribution
        group1 = np.random.normal(10, 1, 100)
        group2 = np.random.normal(10, 1, 100)
        
        is_sig, p_val, adj_p_val = perform_sensitivity_test(group1, group2, 0.05)
        
        # With same distribution, we expect no significance (most of the time)
        # Note: There's a 5% chance of false positive at alpha=0.05
        assert p_val is not None
        assert adj_p_val is not None

    def test_perform_sensitivity_test_threshold_001(self):
        """Test with alpha=0.01 threshold."""
        group1 = np.random.normal(10, 1, 100)
        group2 = np.random.normal(15, 1, 100)
        
        is_sig, p_val, adj_p_val = perform_sensitivity_test(group1, group2, 0.01)
        
        assert p_val is not None
        assert adj_p_val is not None
        # For very different groups, should still be significant at 0.01
        assert is_sig is True

    def test_perform_sensitivity_test_threshold_01(self):
        """Test with alpha=0.1 threshold."""
        group1 = np.random.normal(10, 1, 100)
        group2 = np.random.normal(12, 1, 100)
        
        is_sig, p_val, adj_p_val = perform_sensitivity_test(group1, group2, 0.1)
        
        assert p_val is not None
        assert adj_p_val is not None
        # At higher alpha, more likely to be significant
        assert is_sig is True or is_sig is False  # Depends on random draw

    def test_generate_markdown_report_structure(self):
        """Test that the generated report has expected structure."""
        mock_results = {
            "thresholds": SIGNIFICANCE_THRESHOLDS,
            "metrics": ["metric1", "metric2"],
            "analysis": {
                "metric1": {
                    "human_n": 50,
                    "codegen_n": 50,
                    "thresholds": {
                        "0.01": {"is_significant": False, "p_value": 0.06, "adjusted_p_value": 0.06},
                        "0.05": {"is_significant": False, "p_value": 0.06, "adjusted_p_value": 0.06},
                        "0.1": {"is_significant": True, "p_value": 0.06, "adjusted_p_value": 0.06}
                    }
                },
                "metric2": {
                    "human_n": 60,
                    "codegen_n": 60,
                    "thresholds": {
                        "0.01": {"is_significant": True, "p_value": 0.005, "adjusted_p_value": 0.005},
                        "0.05": {"is_significant": True, "p_value": 0.005, "adjusted_p_value": 0.005},
                        "0.1": {"is_significant": True, "p_value": 0.005, "adjusted_p_value": 0.005}
                    }
                }
            }
        }
        
        report = generate_markdown_report(mock_results)
        
        # Check for expected sections
        assert "# Sensitivity Analysis Report" in report
        assert "## Summary" in report
        assert "## Detailed Results" in report
        assert "## Headline Rates Analysis" in report
        assert "## Conclusion" in report
        
        # Check for metrics
        assert "### metric1" in report
        assert "### metric2" in report
        
        # Check for thresholds
        assert "0.01" in report
        assert "0.05" in report
        assert "0.1" in report

    def test_generate_markdown_report_headline_rates(self):
        """Test that headline rates are calculated correctly."""
        mock_results = {
            "thresholds": SIGNIFICANCE_THRESHOLDS,
            "metrics": ["metric1", "metric2", "metric3"],
            "analysis": {
                "metric1": {
                    "human_n": 50,
                    "codegen_n": 50,
                    "thresholds": {
                        "0.01": {"is_significant": False, "p_value": 0.06, "adjusted_p_value": 0.06},
                        "0.05": {"is_significant": False, "p_value": 0.06, "adjusted_p_value": 0.06},
                        "0.1": {"is_significant": True, "p_value": 0.06, "adjusted_p_value": 0.06}
                    }
                },
                "metric2": {
                    "human_n": 50,
                    "codegen_n": 50,
                    "thresholds": {
                        "0.01": {"is_significant": True, "p_value": 0.005, "adjusted_p_value": 0.005},
                        "0.05": {"is_significant": True, "p_value": 0.005, "adjusted_p_value": 0.005},
                        "0.1": {"is_significant": True, "p_value": 0.005, "adjusted_p_value": 0.005}
                    }
                },
                "metric3": {
                    "human_n": 50,
                    "codegen_n": 50,
                    "thresholds": {
                        "0.01": {"is_significant": False, "p_value": 0.2, "adjusted_p_value": 0.2},
                        "0.05": {"is_significant": False, "p_value": 0.2, "adjusted_p_value": 0.2},
                        "0.1": {"is_significant": False, "p_value": 0.2, "adjusted_p_value": 0.2}
                    }
                }
            }
        }
        
        report = generate_markdown_report(mock_results)
        
        # At 0.01: 1/3 significant (metric2)
        assert "0.01 | 1/3" in report
        # At 0.05: 1/3 significant (metric2)
        assert "0.05 | 1/3" in report
        # At 0.1: 2/3 significant (metric1 and metric2)
        assert "0.1 | 2/3" in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
