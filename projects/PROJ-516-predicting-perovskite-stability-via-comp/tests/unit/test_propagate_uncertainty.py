"""
Unit tests for T013b: propagate_uncertainty.py

Tests:
  - map_uncertainty_to_descriptors correctly maps temperature_precision
  - Missing temperature_precision defaults to 10.0 and logs warning
  - T_d_uncertainty is calculated using calculate_combined_uncertainty
  - Output DataFrame contains T_d_uncertainty column
"""

import json
import logging
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from propagate_uncertainty import map_uncertainty_to_descriptors, load_json, load_descriptors
from utils.uncertainty_propagator import calculate_combined_uncertainty

# Sample metadata for testing
SAMPLE_METADATA = {
    "ABX3": {"temperature_precision": 5.0, "instrument": "TGA-1"},
    "CDX2": {"temperature_precision": 2.0},
    "EFX4": {},  # Missing temperature_precision
}

# Sample descriptors DataFrame
SAMPLE_DESCRIPTORS = pd.DataFrame({
    "formula": ["ABX3", "CDX2", "EFX4"],
    "T_d": [500.0, 600.0, 700.0],
    "feature1": [0.1, 0.2, 0.3]
})

# Expected sigma values (assuming experimental_error=0.0)
# sigma = sqrt(temp_precision^2 + experimental_error^2) = temp_precision
EXPECTED_SIGMA = {
    "ABX3": 5.0,
    "CDX2": 2.0,
    "EFX4": 10.0,  # Default
}

@pytest.fixture
def sample_metadata():
    return SAMPLE_METADATA

@pytest.fixture
def sample_descriptors():
    return SAMPLE_DESCRIPTORS

def test_map_uncertainty_to_descriptors_maps_precisions(sample_metadata, sample_descriptors):
    """Test that temperature_precision is correctly mapped from metadata."""
    result_df = map_uncertainty_to_descriptors(sample_descriptors, sample_metadata)

    # Check that T_d_uncertainty column exists
    assert "T_d_uncertainty" in result_df.columns

    # Check that values match expected sigma
    for formula, expected in EXPECTED_SIGMA.items():
        row = result_df[result_df["formula"] == formula]
        assert len(row) == 1, f"Formula {formula} not found or duplicated"
        actual = row["T_d_uncertainty"].values[0]
        assert actual == pytest.approx(expected, rel=1e-5), \
            f"Expected sigma {expected} for {formula}, got {actual}"

def test_missing_temperature_precision_defaults_to_10(sample_metadata, sample_descriptors):
    """Test that missing temperature_precision defaults to 10.0 and logs warning."""
    # Capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.WARNING)
    logger = logging.getLogger("propagate_uncertainty")
    logger.addHandler(handler)

    try:
        result_df = map_uncertainty_to_descriptors(sample_descriptors, sample_metadata)

        # Check that EFX4 has default sigma of 10.0
        row = result_df[result_df["formula"] == "EFX4"]
        assert row["T_d_uncertainty"].values[0] == pytest.approx(10.0, rel=1e-5)

        # Check that warning was logged
        log_output = log_stream.getvalue()
        assert "temperature_precision missing" in log_output
        assert "EFX4" in log_output
        assert "10.0" in log_output
    finally:
        logger.removeHandler(handler)

def test_map_uncertainty_uses_combined_uncertainty_logic(sample_metadata, sample_descriptors):
    """Test that sigma is calculated using calculate_combined_uncertainty."""
    # Manually compute expected sigma for one entry
    manual_sigma = calculate_combined_uncertainty(temp_precision=5.0, experimental_error=0.0)

    result_df = map_uncertainty_to_descriptors(sample_descriptors, sample_metadata)
    actual_sigma = result_df[result_df["formula"] == "ABX3"]["T_d_uncertainty"].values[0]

    assert actual_sigma == pytest.approx(manual_sigma, rel=1e-5)

def test_map_uncertainty_raises_on_missing_formula_column(sample_metadata):
    """Test that a DataFrame without 'formula' column raises ValueError."""
    bad_df = pd.DataFrame({"T_d": [500.0]})
    with pytest.raises(ValueError, match="must contain a 'formula' column"):
        map_uncertainty_to_descriptors(bad_df, sample_metadata)

def test_load_json_file_not_found(tmp_path):
    """Test that load_json raises FileNotFoundError for missing file."""
    missing_path = tmp_path / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        load_json(missing_path)

def test_load_descriptors_file_not_found(tmp_path):
    """Test that load_descriptors raises FileNotFoundError for missing file."""
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_descriptors(missing_path)