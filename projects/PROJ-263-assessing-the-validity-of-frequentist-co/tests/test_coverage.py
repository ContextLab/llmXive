"""
Unit tests for the coverage calculation logic.
"""

import pytest
import numpy as np
import json
import os
import tempfile

from code.coverage import (
    check_coverage,
    calculate_coverage_rate,
    create_coverage_record,
    aggregate_coverage_records,
    save_coverage_records,
    load_coverage_records
)


class TestCheckCoverage:
    def test_mean_inside_interval(self):
        """Test when mean is strictly inside the interval."""
        assert check_coverage(1.0, 5.0, 3.0) is True

    def test_mean_on_lower_bound(self):
        """Test when mean is exactly on the lower bound."""
        assert check_coverage(3.0, 5.0, 3.0) is True

    def test_mean_on_upper_bound(self):
        """Test when mean is exactly on the upper bound."""
        assert check_coverage(1.0, 3.0, 3.0) is True

    def test_mean_below_interval(self):
        """Test when mean is below the interval."""
        assert check_coverage(2.0, 5.0, 1.0) is False

    def test_mean_above_interval(self):
        """Test when mean is above the interval."""
        assert check_coverage(1.0, 4.0, 5.0) is False

    def test_tolerance(self):
        """Test with a small tolerance."""
        # Mean is slightly below lower bound, but within tolerance
        assert check_coverage(3.0, 5.0, 2.99, tolerance=0.02) is True
        # Mean is outside tolerance
        assert check_coverage(3.0, 5.0, 2.99, tolerance=0.005) is False


class TestCalculateCoverageRate:
    def test_all_true(self):
        """Test when all intervals contain the mean."""
        results = [True, True, True, True]
        assert calculate_coverage_rate(results) == 1.0

    def test_all_false(self):
        """Test when no intervals contain the mean."""
        results = [False, False, False]
        assert calculate_coverage_rate(results) == 0.0

    def test_mixed(self):
        """Test with mixed results."""
        results = [True, False, True, False, True]
        assert calculate_coverage_rate(results) == 0.6

    def test_empty_list(self):
        """Test with an empty list."""
        assert calculate_coverage_rate([]) == 0.0


class TestCreateCoverageRecord:
    def test_record_structure(self):
        """Test that the record has all required fields."""
        record = create_coverage_record(
            dataset_id="wine",
            sample_size=20,
            confidence_level=0.95,
            interval_method="t_interval",
            lower_bound=1.2,
            upper_bound=2.8,
            true_mean=2.0,
            contains_mean=True,
            run_index=0,
            seed=42
        )

        assert record["dataset_id"] == "wine"
        assert record["sample_size"] == 20
        assert record["confidence_level"] == 0.95
        assert record["interval_method"] == "t_interval"
        assert record["interval_lower"] == 1.2
        assert record["interval_upper"] == 2.8
        assert record["true_mean"] == 2.0
        assert record["contains_mean"] is True
        assert record["run_index"] == 0
        assert record["seed"] == 42

    def test_float_conversion(self):
        """Test that numeric values are converted to float."""
        record = create_coverage_record(
            dataset_id="test",
            sample_size=10,
            confidence_level=0.9,
            interval_method="bootstrap",
            lower_bound=np.float64(1.5),
            upper_bound=np.float64(3.5),
            true_mean=np.float64(2.5),
            contains_mean=True,
            run_index=1,
            seed=None
        )

        assert isinstance(record["interval_lower"], float)
        assert isinstance(record["interval_upper"], float)
        assert isinstance(record["true_mean"], float)


class TestAggregateCoverageRecords:
    def test_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_coverage_records([])
        assert result["summary"] == {}
        assert result["total_runs"] == 0

    def test_single_record(self):
        """Test aggregation with a single record."""
        records = [
            create_coverage_record(
                dataset_id="wine",
                sample_size=20,
                confidence_level=0.95,
                interval_method="t_interval",
                lower_bound=1.0,
                upper_bound=3.0,
                true_mean=2.0,
                contains_mean=True,
                run_index=0
            )
        ]

        result = aggregate_coverage_records(records)
        assert result["total_runs"] == 1

        key = "wine_n20_0.95_t_interval"
        assert key in result["summary"]
        assert result["summary"][key]["coverage_rate"] == 1.0
        assert result["summary"][key]["deviation"] == 0.05

    def test_multiple_configs(self):
        """Test aggregation with multiple configurations."""
        records = [
            create_coverage_record("wine", 20, 0.95, "t_interval", 1.0, 3.0, 2.0, True, 0),
            create_coverage_record("wine", 20, 0.95, "t_interval", 1.0, 3.0, 2.0, False, 1),
            create_coverage_record("wine", 20, 0.95, "bootstrap", 1.0, 3.0, 2.0, True, 2),
            create_coverage_record("ionosphere", 20, 0.95, "t_interval", 1.0, 3.0, 2.0, True, 3),
        ]

        result = aggregate_coverage_records(records)
        assert result["total_runs"] == 4

        # Check wine t_interval aggregation (1/2 = 0.5)
        key_t = "wine_n20_0.95_t_interval"
        assert result["summary"][key_t]["coverage_rate"] == 0.5

        # Check wine bootstrap aggregation (1/1 = 1.0)
        key_b = "wine_n20_0.95_bootstrap"
        assert result["summary"][key_b]["coverage_rate"] == 1.0

        # Check ionosphere aggregation (1/1 = 1.0)
        key_i = "ionosphere_n20_0.95_t_interval"
        assert result["summary"][key_i]["coverage_rate"] == 1.0

    def test_interval_width_stats(self):
        """Test that interval width statistics are calculated."""
        records = [
            create_coverage_record("test", 10, 0.95, "t_interval", 0.0, 2.0, 1.0, True, 0), # width 2.0
            create_coverage_record("test", 10, 0.95, "t_interval", 0.5, 3.5, 1.0, True, 1), # width 3.0
        ]

        result = aggregate_coverage_records(records)
        key = "test_n10_0.95_t_interval"
        assert result["summary"][key]["avg_interval_width"] == 2.5
        assert result["summary"][key]["std_interval_width"] == 0.5


class TestSaveAndLoadCoverageRecords:
    def test_save_and_load_roundtrip(self):
        """Test saving and loading records preserves data."""
        records = [
            create_coverage_record("wine", 20, 0.95, "t_interval", 1.0, 3.0, 2.0, True, 0),
            create_coverage_record("wine", 20, 0.95, "t_interval", 1.0, 3.0, 2.0, False, 1),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_coverage_records(records, temp_path)
            loaded_records = load_coverage_records(temp_path)

            assert len(loaded_records) == len(records)
            for original, loaded in zip(records, loaded_records):
                assert original == loaded
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)