"""
Unit tests for code/analyze_results.py utilities.
Verifies sample size validation, spline formula building, and summary writing.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.analyze_results import validate_sample_size, build_formula_with_splines, write_summary, write_hypothesis_summary


class TestValidateSampleSize:
    """Tests for sample size validation."""

    def test_sufficient_sample_size(self):
        """Test with a sample size that meets the minimum requirement."""
        df = pd.DataFrame({"success": [1]*100, "density": [0.5]*100, "horizon": [5]*100})
        result = validate_sample_size(df, min_samples=50)
        assert result is True

    def test_insufficient_sample_size(self):
        """Test with a sample size below the minimum requirement."""
        df = pd.DataFrame({"success": [1]*10, "density": [0.5]*10, "horizon": [5]*10})
        result = validate_sample_size(df, min_samples=50)
        assert result is False

    def test_exact_sample_size(self):
        """Test with a sample size exactly equal to the minimum."""
        df = pd.DataFrame({"success": [1]*50, "density": [0.5]*50, "horizon": [5]*50})
        result = validate_sample_size(df, min_samples=50)
        assert result is True


class TestBuildFormulaWithSplines:
    """Tests for building the regression formula with natural splines."""

    def test_formula_structure(self):
        """Verify the formula contains the expected terms."""
        formula = build_formula_with_splines(df_cols=["success", "density", "horizon"], df=MagicMock(), df_splines=3)
        # The formula should include density, horizon, and the spline terms for horizon
        # Exact string depends on patsy syntax, but we check for key components
        assert "density" in formula
        assert "horizon" in formula
        # Splines are typically named like 'ns(horizon, df=3)'
        assert "ns" in formula or "splines" in formula.lower()

    def test_default_df(self):
        """Verify default degrees of freedom are used if not specified."""
        formula = build_formula_with_splines(df_cols=["success", "density", "horizon"], df=MagicMock())
        # Check if default (e.g., 3) is used
        assert "df=" in formula or "3" in formula


class TestWriteSummary:
    """Tests for writing regression summary JSON."""

    def test_write_valid_summary(self):
        """Test writing a valid summary dictionary."""
        summary = {
            "coefficients": {"density": 0.5, "horizon": 0.3},
            "interaction_p_value": 0.01,
            "model_aic": 100.5
        }
        with patch("builtins.open", MagicMock()) as mock_open, \
             patch("json.dump") as mock_dump:
            write_summary("dummy_path.json", summary)
            mock_open.assert_called_once()
            mock_dump.assert_called_once()

    def test_write_invalid_path(self):
        """Test handling of invalid path (should raise or log)."""
        # If the directory doesn't exist, it should raise
        with pytest.raises(FileNotFoundError):
            write_summary("/non_existent_dir/dummy.json", {})


class TestWriteHypothesisSummary:
    """Tests for writing the hypothesis summary text file."""

    def test_write_supported_hypothesis(self):
        """Test writing a summary where hypothesis is supported."""
        summary_data = {
            "interaction_p_value": 0.01,
            "significant": True,
            "conclusion": "Positive correlation found."
        }
        with patch("builtins.open", MagicMock()) as mock_open, \
             patch("builtins.print") as mock_print:
            write_hypothesis_summary("dummy_path.txt", summary_data)
            mock_open.assert_called_once()

    def test_write_rejected_hypothesis(self):
        """Test writing a summary where hypothesis is rejected."""
        summary_data = {
            "interaction_p_value": 0.2,
            "significant": False,
            "conclusion": "No significant correlation found."
        }
        with patch("builtins.open", MagicMock()) as mock_open, \
             patch("builtins.print") as mock_print:
            write_hypothesis_summary("dummy_path.txt", summary_data)
            mock_open.assert_called_once()
