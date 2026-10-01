"""
Unit tests for T015a: filter_descriptors.py
"""
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Import the module functions
import sys
from code.filter_descriptors import (
    count_missing_values,
    filter_entries,
    DESCRIPTOR_COLUMNS,
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        "formula": ["CsPbI3", "MAPbI3", "FAPbI3", "CsSnI3", "RbPbBr3"],
        "T_d": [350, 370, 380, 300, 360],
        "atomic_fraction_A": [0.2, 0.2, 0.2, 0.2, 0.2],
        "atomic_fraction_B": [0.2, 0.2, 0.2, 0.2, 0.2],
        "atomic_fraction_X": [0.6, 0.6, 0.6, 0.6, 0.6],
        "weighted_ionic_radius": [2.5, 2.6, 2.7, 2.4, 2.55],
        "weighted_electronegativity": [1.8, 1.9, 2.0, 1.7, 1.85],
        "weighted_formation_enthalpy": [-100, -110, -120, -90, -105],
        "first_ionization_energy": [5.0, 5.1, 5.2, 4.9, 5.05],
        "variance_ionic_radius": [0.1, 0.15, 0.2, 0.05, 0.12],
        "variance_electronegativity": [0.05, 0.08, 0.1, 0.03, 0.06],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataframe_with_missing():
    """Create a sample DataFrame with missing values for testing."""
    data = {
        "formula": ["CsPbI3", "MAPbI3", "FAPbI3", "CsSnI3", "RbPbBr3"],
        "T_d": [350, 370, 380, 300, 360],
        "atomic_fraction_A": [0.2, 0.2, None, 0.2, 0.2],
        "atomic_fraction_B": [0.2, None, 0.2, 0.2, 0.2],
        "atomic_fraction_X": [0.6, 0.6, 0.6, None, 0.6],
        "weighted_ionic_radius": [2.5, 2.6, 2.7, 2.4, None],
        "weighted_electronegativity": [1.8, 1.9, None, 1.7, 1.85],
        "weighted_formation_enthalpy": [-100, -110, -120, -90, -105],
        "first_ionization_energy": [5.0, 5.1, 5.2, 4.9, 5.05],
        "variance_ionic_radius": [0.1, 0.15, 0.2, 0.05, 0.12],
        "variance_electronegativity": [0.05, 0.08, 0.1, 0.03, 0.06],
    }
    return pd.DataFrame(data)


def test_count_missing_values_no_missing(sample_dataframe):
    """Test counting missing values when there are none."""
    missing_counts = count_missing_values(sample_dataframe)
    assert all(missing_counts == 0), "Expected 0 missing values for all rows"


def test_count_missing_values_with_missing(sample_dataframe_with_missing):
    """Test counting missing values when some are present."""
    missing_counts = count_missing_values(sample_dataframe_with_missing)
    expected_counts = [1, 2, 2, 1, 1]  # Row 1 and 2 have 2 missing, others have 1
    assert missing_counts.tolist() == expected_counts, f"Expected {expected_counts}, got {missing_counts.tolist()}"


def test_filter_entries_no_missing(sample_dataframe):
    """Test filtering when there are no missing values."""
    filtered_df, excluded_df = filter_entries(sample_dataframe, threshold=2)
    assert len(filtered_df) == len(sample_dataframe), "All rows should be kept"
    assert len(excluded_df) == 0, "No rows should be excluded"


def test_filter_entries_with_missing(sample_dataframe_with_missing):
    """Test filtering when some rows have >= 2 missing values."""
    filtered_df, excluded_df = filter_entries(sample_dataframe_with_missing, threshold=2)

    # Rows 1 and 2 (index 1 and 2) have 2 missing values each, so they should be excluded
    assert len(filtered_df) == 3, f"Expected 3 rows kept, got {len(filtered_df)}"
    assert len(excluded_df) == 2, f"Expected 2 rows excluded, got {len(excluded_df)}"

    # Check that excluded rows have the correct formulas
    excluded_formulas = excluded_df["formula"].tolist()
    assert "MAPbI3" in excluded_formulas, "MAPbI3 should be excluded"
    assert "FAPbI3" in excluded_formulas, "FAPbI3 should be excluded"


def test_filter_entries_threshold_1(sample_dataframe_with_missing):
    """Test filtering with threshold=1 (exclude any row with >= 1 missing)."""
    filtered_df, excluded_df = filter_entries(sample_dataframe_with_missing, threshold=1)

    # All rows have at least 1 missing value
    assert len(filtered_df) == 0, "All rows should be excluded with threshold=1"
    assert len(excluded_df) == 5, "All 5 rows should be excluded"