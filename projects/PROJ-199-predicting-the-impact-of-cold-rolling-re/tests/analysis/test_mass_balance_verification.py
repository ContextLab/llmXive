"""
Unit tests for system-level mass balance verification (T020b).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.mass_balance_verification import (
    load_descriptors,
    calculate_total_fractions,
    validate_aggregated_mass_balance,
    run_mass_balance_verification,
    COMPONENT_COLUMNS,
    TOLERANCE
)


@pytest.fixture
def valid_descriptors_df():
    """Create a valid descriptors dataframe for testing."""
    data = {
        "sample_id": ["sample_1", "sample_2", "sample_3"],
        "material": ["Al", "Cu", "Ni"],
        "reduction": [30, 50, 70],
        "brass_fraction": [0.25, 0.30, 0.35],
        "copper_fraction": [0.20, 0.25, 0.20],
        "s_fraction": [0.15, 0.10, 0.15],
        "goss_fraction": [0.10, 0.15, 0.10],
        "random_fraction": [0.30, 0.20, 0.20]
    }
    # Each row sums to 1.0
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def out_of_tolerance_df():
    """Create a dataframe where some samples are out of tolerance."""
    data = {
        "sample_id": ["sample_1", "sample_2", "sample_3"],
        "material": ["Al", "Cu", "Ni"],
        "reduction": [30, 50, 70],
        "brass_fraction": [0.25, 0.30, 0.40],  # sample_3 will be out
        "copper_fraction": [0.20, 0.25, 0.20],
        "s_fraction": [0.15, 0.10, 0.15],
        "goss_fraction": [0.10, 0.15, 0.10],
        "random_fraction": [0.30, 0.20, 0.15]  # sample_3 sum = 1.00 (0.4+0.2+0.15+0.1+0.15 = 1.0) - let's make it fail
    }
    # Actually, let's make sample_3 sum to 1.05 (out of tolerance)
    data["brass_fraction"] = [0.25, 0.30, 0.45]
    data["random_fraction"] = [0.30, 0.20, 0.20]
    # sample_3: 0.45 + 0.20 + 0.15 + 0.10 + 0.20 = 1.10 (out of tolerance)
    df = pd.DataFrame(data)
    return df


def test_calculate_total_fractions(valid_descriptors_df):
    """Test that total fractions are calculated correctly."""
    totals = calculate_total_fractions(valid_descriptors_df)
    expected = pd.Series([1.0, 1.0, 1.0])
    pd.testing.assert_series_equal(totals, expected)


def test_validate_aggregated_mass_balance_pass(valid_descriptors_df):
    """Test validation passes when all samples sum to 1.0."""
    is_valid, report = validate_aggregated_mass_balance(valid_descriptors_df)
    assert is_valid is True
    assert report["status"] == "PASS"
    assert abs(report["mean_sum"] - 1.0) < 0.0001
    assert report["out_of_tolerance_samples"] == 0


def test_validate_aggregated_mass_balance_fail(out_of_tolerance_df):
    """Test validation fails when mean is out of tolerance."""
    # Create a dataframe where the MEAN is out of tolerance
    # If one sample is 1.10 and others are 1.0, mean = (1.0 + 1.0 + 1.10) / 3 = 1.033
    # This is > 1.0 + 0.01, so should fail
    is_valid, report = validate_aggregated_mass_balance(out_of_tolerance_df)
    # The mean is 1.033, which is > 1.01, so it should fail
    assert is_valid is False
    assert report["status"] == "FAIL"
    assert report["out_of_tolerance_samples"] == 1


def test_load_descriptors_file_not_found():
    """Test that FileNotFoundError is raised when file is missing."""
    with patch("analysis.mass_balance_verification.DESCRIPTORS_PATH", Path("/nonexistent/path.csv")):
        with pytest.raises(FileNotFoundError, match="Descriptors file not found"):
            load_descriptors()


def test_load_descriptors_missing_columns(tmp_path):
    """Test that ValueError is raised when required columns are missing."""
    # Create a CSV with missing columns
    csv_path = tmp_path / "descriptors.csv"
    df_missing = pd.DataFrame({
        "sample_id": ["sample_1"],
        "brass_fraction": [0.25]
        # Missing other component columns
    })
    df_missing.to_csv(csv_path, index=False)

    with patch("analysis.mass_balance_verification.DESCRIPTORS_PATH", csv_path):
        with pytest.raises(ValueError, match="Missing required columns"):
            load_descriptors()


def test_run_mass_balance_verification_integration(tmp_path, valid_descriptors_df):
    """Integration test for the full verification pipeline."""
    # Setup
    descriptors_path = tmp_path / "descriptors.csv"
    report_path = tmp_path / "mass_balance_verification_report.json"

    valid_descriptors_df.to_csv(descriptors_path, index=False)

    with patch("analysis.mass_balance_verification.DESCRIPTORS_PATH", descriptors_path), \
         patch("analysis.mass_balance_verification.OUTPUT_REPORT_PATH", report_path):

        report = run_mass_balance_verification()

        # Verify report was generated
        assert report_path.exists()
        with open(report_path) as f:
            saved_report = json.load(f)

        assert saved_report["status"] == "PASS"
        assert report["status"] == "PASS"


def test_tolerance_boundary():
    """Test that the tolerance boundary is correctly applied."""
    # Create a dataframe where mean is exactly at tolerance boundary
    data = {
        "sample_id": ["s1", "s2"],
        "brass_fraction": [0.5 + TOLERANCE/2, 0.5 - TOLERANCE/2],
        "copper_fraction": [0.2, 0.2],
        "s_fraction": [0.1, 0.1],
        "goss_fraction": [0.1, 0.1],
        "random_fraction": [0.1, 0.1 + TOLERANCE]
    }
    # s1: 0.5 + 0.005 + 0.2 + 0.1 + 0.1 + 0.1 = 1.005
    # s2: 0.5 - 0.005 + 0.2 + 0.1 + 0.1 + 0.101 = 1.001
    # Mean: (1.005 + 1.001) / 2 = 1.003 (within tolerance)
    df = pd.DataFrame(data)

    is_valid, report = validate_aggregated_mass_balance(df)
    assert is_valid is True