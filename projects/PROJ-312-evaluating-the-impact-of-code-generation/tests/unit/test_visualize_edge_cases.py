"""
Unit tests for edge cases in code/visualize.py.

Tests cover:
- Zero variance in data (all values identical)
- Empty datasets
- Single data point per group
- NaN/None values handling
- Extreme outliers
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from visualize import (
    load_outlier_indices,
    prepare_boxplot_data,
    generate_boxplot,
)


class TestZeroVariance:
    """Test handling of zero variance scenarios."""

    def test_zero_variance_ai_group(self, tmp_path):
        """Test boxplot generation when AI group has zero variance."""
        # Create test data with zero variance in AI group
        data = {
            "ai": [5.0, 5.0, 5.0, 5.0, 5.0],  # Zero variance
            "non_ai": [3.0, 4.0, 5.0, 6.0, 7.0],
        }

        # Should not raise an error
        fig, ax = generate_boxplot(data, tmp_path / "test_zero_var.png")
        assert fig is not None
        assert ax is not None

    def test_zero_variance_both_groups(self, tmp_path):
        """Test boxplot generation when both groups have zero variance."""
        data = {
            "ai": [5.0, 5.0, 5.0],
            "non_ai": [3.0, 3.0, 3.0],
        }

        # Should handle gracefully
        fig, ax = generate_boxplot(data, tmp_path / "test_both_zero_var.png")
        assert fig is not None
        assert ax is not None

    def test_zero_variance_in_outlier_data(self, tmp_path):
        """Test prepare_boxplot_data with zero variance outlier indices."""
        outlier_data = {
            "ai": [1.0, 1.0, 1.0],
            "non_ai": [2.0, 2.0, 2.0],
        }

        # Should not crash
        result = prepare_boxplot_data(outlier_data, outlier_data)
        assert "ai" in result
        assert "non_ai" in result


class TestEmptyData:
    """Test handling of empty datasets."""

    def test_empty_ai_group(self, tmp_path):
        """Test behavior when AI group is empty."""
        data = {
            "ai": [],
            "non_ai": [3.0, 4.0, 5.0],
        }

        # Should handle or raise appropriate error
        with pytest.raises((ValueError, IndexError)):
            generate_boxplot(data, tmp_path / "test_empty_ai.png")

    def test_empty_non_ai_group(self, tmp_path):
        """Test behavior when non-AI group is empty."""
        data = {
            "ai": [3.0, 4.0, 5.0],
            "non_ai": [],
        }

        with pytest.raises((ValueError, IndexError)):
            generate_boxplot(data, tmp_path / "test_empty_non_ai.png")

    def test_both_groups_empty(self, tmp_path):
        """Test behavior when both groups are empty."""
        data = {
            "ai": [],
            "non_ai": [],
        }

        with pytest.raises((ValueError, IndexError)):
            generate_boxplot(data, tmp_path / "test_both_empty.png")

    def test_prepare_boxplot_data_empty(self):
        """Test prepare_boxplot_data with empty input."""
        data = {
            "ai": [],
            "non_ai": [],
        }

        # Should handle gracefully or raise appropriate error
        with pytest.raises((ValueError, KeyError)):
            prepare_boxplot_data(data, data)


class TestSingleDataPoint:
    """Test handling of single data point scenarios."""

    def test_single_point_ai_group(self, tmp_path):
        """Test boxplot with only one AI data point."""
        data = {
            "ai": [5.0],
            "non_ai": [3.0, 4.0, 5.0, 6.0, 7.0],
        }

        # Should handle gracefully
        fig, ax = generate_boxplot(data, tmp_path / "test_single_ai.png")
        assert fig is not None

    def test_single_point_non_ai_group(self, tmp_path):
        """Test boxplot with only one non-AI data point."""
        data = {
            "ai": [3.0, 4.0, 5.0, 6.0, 7.0],
            "non_ai": [5.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_single_non_ai.png")
        assert fig is not None

    def test_single_point_both_groups(self, tmp_path):
        """Test boxplot with one point in each group."""
        data = {
            "ai": [5.0],
            "non_ai": [3.0],
        }

        # Should handle without crashing
        fig, ax = generate_boxplot(data, tmp_path / "test_single_both.png")
        assert fig is not None


class TestNaNHandling:
    """Test handling of NaN and None values."""

    def test_nan_in_ai_group(self, tmp_path):
        """Test boxplot with NaN values in AI group."""
        data = {
            "ai": [3.0, np.nan, 5.0, 6.0, 7.0],
            "non_ai": [3.0, 4.0, 5.0, 6.0, 7.0],
        }

        # Should handle NaN gracefully
        fig, ax = generate_boxplot(data, tmp_path / "test_nan_ai.png")
        assert fig is not None

    def test_none_in_non_ai_group(self, tmp_path):
        """Test boxplot with None values in non-AI group."""
        data = {
            "ai": [3.0, 4.0, 5.0, 6.0, 7.0],
            "non_ai": [3.0, None, 5.0, 6.0, 7.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_none_non_ai.png")
        assert fig is not None

    def test_mixed_nan_none(self, tmp_path):
        """Test boxplot with both NaN and None values."""
        data = {
            "ai": [3.0, np.nan, None, 6.0, 7.0],
            "non_ai": [None, np.nan, 5.0, 6.0, 7.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_mixed_nan.png")
        assert fig is not None


class TestExtremeOutliers:
    """Test handling of extreme outlier values."""

    def test_extreme_outlier_ai(self, tmp_path):
        """Test boxplot with extreme outlier in AI group."""
        data = {
            "ai": [3.0, 4.0, 5.0, 6.0, 1000.0],  # Extreme outlier
            "non_ai": [3.0, 4.0, 5.0, 6.0, 7.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_extreme_ai.png")
        assert fig is not None

    def test_extreme_outlier_non_ai(self, tmp_path):
        """Test boxplot with extreme outlier in non-AI group."""
        data = {
            "ai": [3.0, 4.0, 5.0, 6.0, 7.0],
            "non_ai": [3.0, 4.0, 5.0, 6.0, 1000000.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_extreme_non_ai.png")
        assert fig is not None

    def test_multiple_extreme_outliers(self, tmp_path):
        """Test boxplot with multiple extreme outliers."""
        data = {
            "ai": [3.0, 4.0, 5.0, 1000.0, 2000.0],
            "non_ai": [3.0, 4.0, 5.0, 10000.0, 20000.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_multiple_extreme.png")
        assert fig is not None


class TestLoadOutlierIndices:
    """Test load_outlier_indices function edge cases."""

    def test_missing_outlier_file(self, tmp_path):
        """Test loading from non-existent outlier file."""
        with pytest.raises(FileNotFoundError):
            load_outlier_indices(tmp_path / "nonexistent.json")

    def test_empty_outlier_file(self, tmp_path):
        """Test loading from empty outlier file."""
        empty_file = tmp_path / "empty_outliers.json"
        empty_file.write_text("{}")

        result = load_outlier_indices(empty_file)
        assert result == {}

    def test_invalid_json_outlier_file(self, tmp_path):
        """Test loading from invalid JSON file."""
        invalid_file = tmp_path / "invalid_outliers.json"
        invalid_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            load_outlier_indices(invalid_file)


class TestPrepareBoxplotData:
    """Test prepare_boxplot_data function edge cases."""

    def test_missing_group_in_data(self):
        """Test when one group is missing from input data."""
        data = {
            "ai": [3.0, 4.0, 5.0],
            # non_ai missing
        }

        with pytest.raises(KeyError):
            prepare_boxplot_data(data, data)

    def test_mismatched_groups(self):
        """Test when outlier data has different groups than main data."""
        data = {
            "ai": [3.0, 4.0, 5.0],
            "non_ai": [3.0, 4.0, 5.0],
        }
        outlier_data = {
            "ai": [1.0, 2.0],
            # non_ai missing
        }

        with pytest.raises(KeyError):
            prepare_boxplot_data(data, outlier_data)

    def test_all_outliers_removed(self):
        """Test when all points are identified as outliers."""
        data = {
            "ai": [3.0, 4.0, 5.0],
            "non_ai": [3.0, 4.0, 5.0],
        }
        outlier_data = {
            "ai": [3.0, 4.0, 5.0],  # All will be filtered
            "non_ai": [3.0, 4.0, 5.0],
        }

        result = prepare_boxplot_data(data, outlier_data)
        # Should handle gracefully, possibly with empty lists
        assert result is not None


class TestGenerateBoxplot:
    """Test generate_boxplot function edge cases."""

    def test_invalid_output_path(self, tmp_path):
        """Test saving to invalid directory."""
        data = {
            "ai": [3.0, 4.0, 5.0],
            "non_ai": [3.0, 4.0, 5.0],
        }

        invalid_path = Path("/nonexistent/directory/boxplot.png")
        with pytest.raises((OSError, FileNotFoundError)):
            generate_boxplot(data, invalid_path)

    def test_unsupported_file_extension(self, tmp_path):
        """Test saving with unsupported file extension."""
        data = {
            "ai": [3.0, 4.0, 5.0],
            "non_ai": [3.0, 4.0, 5.0],
        }

        with pytest.raises(ValueError):
            generate_boxplot(data, tmp_path / "boxplot.txt")

    def test_data_with_negative_values(self, tmp_path):
        """Test boxplot with negative turnaround times (shouldn't happen but test edge case)."""
        data = {
            "ai": [-5.0, 3.0, 4.0, 5.0],
            "non_ai": [-3.0, 4.0, 5.0, 6.0],
        }

        # Should handle without crashing
        fig, ax = generate_boxplot(data, tmp_path / "test_negative.png")
        assert fig is not None

    def test_very_small_values(self, tmp_path):
        """Test boxplot with very small values."""
        data = {
            "ai": [0.001, 0.002, 0.003],
            "non_ai": [0.001, 0.002, 0.003],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_small.png")
        assert fig is not None

    def test_very_large_values(self, tmp_path):
        """Test boxplot with very large values."""
        data = {
            "ai": [1000000.0, 2000000.0, 3000000.0],
            "non_ai": [1000000.0, 2000000.0, 3000000.0],
        }

        fig, ax = generate_boxplot(data, tmp_path / "test_large.png")
        assert fig is not None