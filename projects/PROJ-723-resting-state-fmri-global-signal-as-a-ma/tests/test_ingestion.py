import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import (
    compute_global_signal_mean_time_series,
    compute_global_signal_sd_per_run,
    compute_subject_average_global_signal_sd,
    check_zero_variance_subjects
)

class TestZeroVarianceExclusion:
    """Tests for the zero-variance check functionality (T015)."""

    def test_exclude_zero_variance_subjects(self):
        """Test that subjects with global_signal_sd == 0 are excluded."""
        data = [
            {"subject_id": "sub-01", "global_signal_sd": 0.001, "mwq_score": 10},
            {"subject_id": "sub-02", "global_signal_sd": 0.0, "mwq_score": 15},
            {"subject_id": "sub-03", "global_signal_sd": 0.002, "mwq_score": 8},
            {"subject_id": "sub-04", "global_signal_sd": 0.0, "mwq_score": 12},
            {"subject_id": "sub-05", "global_signal_sd": 0.003, "mwq_score": 20},
        ]

        filtered_data = check_zero_variance_subjects(data, log=False)

        assert len(filtered_data) == 3
        excluded_ids = [s["subject_id"] for s in filtered_data]
        assert "sub-01" in excluded_ids
        assert "sub-02" not in excluded_ids
        assert "sub-03" in excluded_ids
        assert "sub-04" not in excluded_ids
        assert "sub-05" in excluded_ids

    def test_all_zero_variance_excluded(self):
        """Test that all subjects are excluded when all have zero variance."""
        data = [
            {"subject_id": "sub-01", "global_signal_sd": 0.0},
            {"subject_id": "sub-02", "global_signal_sd": 0.0},
        ]

        filtered_data = check_zero_variance_subjects(data, log=False)

        assert len(filtered_data) == 0

    def test_no_zero_variance(self):
        """Test that no subjects are excluded when none have zero variance."""
        data = [
            {"subject_id": "sub-01", "global_signal_sd": 0.001},
            {"subject_id": "sub-02", "global_signal_sd": 0.002},
            {"subject_id": "sub-03", "global_signal_sd": 0.003},
        ]

        filtered_data = check_zero_variance_subjects(data, log=False)

        assert len(filtered_data) == 3

    def test_empty_data(self):
        """Test that empty data returns empty list."""
        data = []
        filtered_data = check_zero_variance_subjects(data, log=False)
        assert len(filtered_data) == 0

    def test_missing_global_signal_sd_key(self):
        """Test that subjects missing global_signal_sd are excluded (default 0.0)."""
        data = [
            {"subject_id": "sub-01", "global_signal_sd": 0.001},
            {"subject_id": "sub-02"},  # Missing key
            {"subject_id": "sub-03", "global_signal_sd": 0.002},
        ]

        filtered_data = check_zero_variance_subjects(data, log=False)

        assert len(filtered_data) == 2
        excluded_ids = [s["subject_id"] for s in filtered_data]
        assert "sub-02" not in excluded_ids

    def test_logging_on_zero_variance(self, caplog):
        """Test that warnings are logged for excluded subjects."""
        import logging
        data = [
            {"subject_id": "sub-01", "global_signal_sd": 0.0},
            {"subject_id": "sub-02", "global_signal_sd": 0.001},
        ]

        with caplog.at_level(logging.WARNING):
            check_zero_variance_subjects(data, log=True)

        assert any("global_signal_sd is zero" in record.message for record in caplog.records)
        assert any("sub-01" in record.message for record in caplog.records)

class TestGlobalSignalComputation:
    """Tests for global signal computation functions."""

    def test_compute_global_signal_sd_per_run(self):
        """Test SD calculation for a single run."""
        # Create a simple time series with known SD
        time_series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected_sd = np.std(time_series)
        result = compute_global_signal_sd_per_run(time_series)
        assert np.isclose(result, expected_sd)

    def test_compute_global_signal_sd_per_run_empty(self):
        """Test SD calculation for empty array."""
        time_series = np.array([])
        result = compute_global_signal_sd_per_run(time_series)
        assert result == 0.0

    def test_compute_subject_average_global_signal_sd(self):
        """Test averaging SD across runs."""
        run_sds = [0.1, 0.2, 0.3]
        expected_avg = 0.2
        result = compute_subject_average_global_signal_sd(run_sds)
        assert np.isclose(result, expected_avg)

    def test_compute_subject_average_global_signal_sd_empty(self):
        """Test averaging SD with empty list."""
        run_sds = []
        result = compute_subject_average_global_signal_sd(run_sds)
        assert result == 0.0