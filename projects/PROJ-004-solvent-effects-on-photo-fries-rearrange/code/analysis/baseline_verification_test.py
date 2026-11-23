"""Unit tests for baseline verification module."""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Adjust import path for local execution
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.baseline_verification import (
    calculate_baseline_deviation,
    flag_deviations,
    verify_baseline_integrity,
    write_verification_report
)


def test_calculate_baseline_deviation_identical():
    """Test with identical spectra - deviation should be zero."""
    wavelengths = np.linspace(200, 800, 100)
    absorbance = np.sin(wavelengths / 100) + 0.5

    pre_df = pd.DataFrame({"wavelength": wavelengths, "absorbance": absorbance})
    post_df = pd.DataFrame({"wavelength": wavelengths, "absorbance": absorbance})

    metrics = calculate_baseline_deviation(pre_df, post_df)

    assert metrics["max_deviation"] == 0.0
    assert metrics["mean_deviation"] == 0.0
    assert metrics["rms_deviation"] == 0.0
    assert metrics["threshold_exceeded"] is False


def test_calculate_baseline_deviation_shifted():
    """Test with shifted spectra - deviation should be detected."""
    wavelengths = np.linspace(200, 800, 100)
    base_abs = np.sin(wavelengths / 100) + 0.5
    # Add a constant shift larger than 3x noise (assuming noise is std of base)
    noise_est = np.std(base_abs)
    shift = 4.0 * noise_est # Exceeds threshold

    pre_df = pd.DataFrame({"wavelength": wavelengths, "absorbance": base_abs})
    post_df = pd.DataFrame({"wavelength": wavelengths, "absorbance": base_abs + shift})

    metrics = calculate_baseline_deviation(pre_df, post_df)

    assert metrics["threshold_exceeded"] is True
    assert metrics["max_deviation"] > metrics["threshold_value"]


def test_calculate_baseline_deviation_missing_data():
    """Test handling of None inputs."""
    metrics = calculate_baseline_deviation(None, None)
    assert metrics["status"] == "missing_data"
    assert metrics["threshold_exceeded"] is None


def test_flag_deviations_pass():
    """Test flag generation for passing case."""
    metrics = {"threshold_exceeded": False, "status": "ok"}
    flag = flag_deviations(metrics, "water", 1)

    assert flag["status"] == "PASS"
    assert flag["solvent"] == "water"
    assert flag["replicate"] == 1


def test_flag_deviations_fail():
    """Test flag generation for failing case."""
    metrics = {"threshold_exceeded": True, "status": "deviation_detected"}
    flag = flag_deviations(metrics, "methanol", 2)

    assert flag["status"] == "FAIL"


def test_verify_baseline_integrity():
    """Test summary generation."""
    flags = [
        {"status": "PASS", "solvent": "water", "replicate": 1},
        {"status": "PASS", "solvent": "water", "replicate": 2},
        {"status": "FAIL", "solvent": "methanol", "replicate": 1}
    ]

    summary = verify_baseline_integrity(flags)

    assert summary["total_runs"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["integrity_verified"] is False
    assert abs(summary["pass_rate_percent"] - (2/3 * 100)) < 0.1


def test_write_verification_report(tmp_path):
    """Test writing the report to disk."""
    flags = [{"status": "PASS", "solvent": "water", "replicate": 1}]
    summary = {"integrity_verified": True, "total_runs": 1}
    output_file = tmp_path / "test_report.json"

    write_verification_report(flags, summary, output_file)

    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)

    assert "report_metadata" in data
    assert "summary" in data
    assert "individual_flags" in data
    assert data["summary"]["integrity_verified"] is True