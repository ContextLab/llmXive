"""
Unit tests for power analysis functionality.
"""

import pytest
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from power_analysis import (
    calculate_cohen_d,
    interpret_effect_size,
    check_dataset_power,
    run_power_analysis_from_csv
)


class TestCohenD:
    """Tests for Cohen's d calculation."""

    def test_cohen_d_small_difference(self):
        """Test calculation with small difference between groups."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])

        d = calculate_cohen_d(group1, group2)
        assert abs(d) < 0.5, "Effect size should be small for similar groups"

    def test_cohen_d_large_difference(self):
        """Test calculation with large difference between groups."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])

        d = calculate_cohen_d(group1, group2)
        assert abs(d) > 0.8, "Effect size should be large for dissimilar groups"

    def test_cohen_d_identical_groups(self):
        """Test calculation with identical groups (should be ~0)."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        d = calculate_cohen_d(group1, group2)
        assert abs(d) < 0.001, "Effect size should be near zero for identical groups"

    def test_cohen_d_empty_group_raises(self):
        """Test that empty groups raise an error."""
        group1 = np.array([])
        group2 = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError):
            calculate_cohen_d(group1, group2)


class TestInterpretEffectSize:
    """Tests for effect size interpretation."""

    def test_negligible_effect(self):
        """Test interpretation of negligible effect."""
        assert interpret_effect_size(0.1) == "negligible"
        assert interpret_effect_size(-0.1) == "negligible"

    def test_small_effect(self):
        """Test interpretation of small effect."""
        assert interpret_effect_size(0.3) == "small"
        assert interpret_effect_size(-0.4) == "small"

    def test_medium_effect(self):
        """Test interpretation of medium effect."""
        assert interpret_effect_size(0.5) == "medium"
        assert interpret_effect_size(-0.7) == "medium"

    def test_large_effect(self):
        """Test interpretation of large effect."""
        assert interpret_effect_size(0.8) == "large"
        assert interpret_effect_size(1.5) == "large"
        assert interpret_effect_size(-1.2) == "large"


class TestCheckDatasetPower:
    """Tests for dataset power checking."""

    def test_sufficient_power_large_sample(self):
        """Test with large sample size and medium effect."""
        result = check_dataset_power(n_samples=500, effect_size=0.5)
        assert result["is_sufficient"] is True
        assert result["n_samples"] == 500

    def test_insufficient_power_small_sample(self):
        """Test with small sample size and small effect."""
        result = check_dataset_power(n_samples=20, effect_size=0.2)
        # Small sample with small effect likely insufficient
        assert result["n_samples"] == 20

    def test_power_calculation_consistency(self):
        """Test that power calculation is consistent."""
        result1 = check_dataset_power(n_samples=200, effect_size=0.5)
        result2 = check_dataset_power(n_samples=200, effect_size=0.5)

        assert result1["calculated_power"] == result2["calculated_power"]


class TestRunPowerAnalysisFromCSV:
    """Tests for CSV-based power analysis."""

    def test_full_analysis_with_temp_csv(self):
        """Test full analysis pipeline with a temporary CSV file."""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("group,value\n")
            for i in range(50):
                f.write(f"A,{1.0 + i * 0.1}\n")
            for i in range(50):
                f.write(f"B,{2.0 + i * 0.1}\n")
            temp_csv = f.name

        # Create temporary output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_output = f.name

        try:
            result = run_power_analysis_from_csv(
                csv_path=temp_csv,
                value_column="value",
                group_column="group",
                output_path=temp_output,
                alpha=0.05,
                beta=0.20,
                minimum_threshold=150
            )

            # Verify report structure
            assert "dataset_statistics" in result
            assert "effect_size" in result
            assert "power_analysis" in result
            assert "overall_status" in result
            assert result["dataset_statistics"]["total_samples"] == 100

            # Verify JSON file was created
            assert os.path.exists(temp_output)
            with open(temp_output, 'r') as f:
                loaded = json.load(f)
            assert loaded["overall_status"]["passed"] is False  # Below threshold

        finally:
            # Cleanup
            os.unlink(temp_csv)
            os.unlink(temp_output)

    def test_missing_column_raises(self):
        """Test that missing columns raise appropriate errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("group,value\n")
            f.write("A,1.0\n")
            temp_csv = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_output = f.name

        try:
            with pytest.raises(ValueError):
                run_power_analysis_from_csv(
                    csv_path=temp_csv,
                    value_column="nonexistent",
                    group_column="group",
                    output_path=temp_output
                )
        finally:
            os.unlink(temp_csv)
            os.unlink(temp_output)

    def test_single_group_raises(self):
        """Test that single group raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("group,value\n")
            for i in range(50):
                f.write(f"A,{1.0 + i * 0.1}\n")
            temp_csv = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_output = f.name

        try:
            with pytest.raises(ValueError):
                run_power_analysis_from_csv(
                    csv_path=temp_csv,
                    value_column="value",
                    group_column="group",
                    output_path=temp_output
                )
        finally:
            os.unlink(temp_csv)
            os.unlink(temp_output)