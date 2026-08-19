"""
Unit tests for TDP Calibration Script.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.calibrate_tdp import (
    CalibrationError,
    get_cpu_base_frequency,
    run_calibration_workload,
    estimate_tdp_from_frequency,
    calibrate_tdp
)


class TestGetCpuBaseFrequency:
    def test_returns_float(self):
        """Test that the function returns a float."""
        freq = get_cpu_base_frequency()
        assert isinstance(freq, float)
        assert freq > 0


class TestRunCalibrationWorkload:
    def test_returns_list_of_frequencies(self):
        """Test that the workload returns a list of frequency values."""
        # Run for a very short time for testing
        freqs = run_calibration_workload(0.1)
        assert isinstance(freqs, list)
        assert len(freqs) > 0
        assert all(isinstance(f, float) for f in freqs)

    def test_workload_runs_without_error(self):
        """Test that the workload completes without raising exceptions."""
        try:
            run_calibration_workload(0.1)
        except Exception as e:
            pytest.fail(f"Workload raised an exception: {e}")


class TestEstimateTdpFromFrequency:
    def test_estimates_tdp_correctly(self):
        """Test TDP estimation with mock frequency data."""
        # Mock frequencies around 2.0 GHz
        mock_freqs = [2.0e9, 2.1e9, 1.9e9, 2.0e9]
        base_freq = 2.0e9

        results = estimate_tdp_from_frequency(mock_freqs, base_freq)

        assert "tdp_watts" in results
        assert "error_margin" in results
        assert "confidence_interval" in results
        assert isinstance(results["tdp_watts"], float)
        assert results["tdp_watts"] > 0
        assert results["error_margin"] >= 0
        assert len(results["confidence_interval"]) == 2

    def test_handles_empty_list(self):
        """Test that an empty list raises CalibrationError."""
        with pytest.raises(CalibrationError):
            estimate_tdp_from_frequency([], 2.0e9)


class TestCalibrateTdp:
    def test_creates_output_file(self):
        """Test that the calibration function creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_tdp.json")
            result = calibrate_tdp(output_path)

            assert os.path.exists(output_path)
            assert "tdp_watts" in result
            assert "error_margin" in result
            assert "confidence_interval" in result

    def test_output_contains_required_fields(self):
        """Test that the output JSON contains all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_tdp.json")
            calibrate_tdp(output_path)

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "tdp_watts" in data
            assert "error_margin" in data
            assert "confidence_interval" in data
            assert "calibration_metadata" in data
            assert "method" in data["calibration_metadata"]
            assert "timestamp" in data["calibration_metadata"]