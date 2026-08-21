"""
Unit tests for verify_descriptors module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_descriptors import (
    verify_column_presence,
    verify_column_data_validity,
    REQUIRED_COLUMNS
)


class TestVerifyColumnPresence:
    """Tests for verify_column_presence function."""

    def test_all_columns_present(self):
        """Test when all required columns are present."""
        df = pd.DataFrame({col: [1.0] for col in REQUIRED_COLUMNS})
        all_present, missing, present = verify_column_presence(df)
        
        assert all_present is True
        assert len(missing) == 0
        assert len(present) == len(REQUIRED_COLUMNS)

    def test_missing_column(self):
        """Test when one required column is missing."""
        df = pd.DataFrame({col: [1.0] for col in REQUIRED_COLUMNS if col != "first_ionization_energy"})
        all_present, missing, present = verify_column_presence(df)
        
        assert all_present is False
        assert "first_ionization_energy" in missing
        assert len(present) == len(REQUIRED_COLUMNS) - 1

    def test_custom_columns(self):
        """Test with custom required columns list."""
        df = pd.DataFrame({"col_a": [1.0], "col_b": [1.0]})
        all_present, missing, present = verify_column_presence(df, required_cols=["col_a", "col_b", "col_c"])
        
        assert all_present is False
        assert "col_c" in missing
        assert "col_a" in present
        assert "col_b" in present


class TestVerifyColumnDataValidity:
    """Tests for verify_column_data_validity function."""

    def test_all_valid(self):
        """Test when all columns have valid non-null data."""
        df = pd.DataFrame({
            "first_ionization_energy": [5.0, 6.0, 7.0],
            "weighted_ionic_radius": [1.5, 1.6, 1.7],
            "T_d": [500, 600, 700]
        })
        all_valid, invalid = verify_column_data_validity(df, columns_to_check=["first_ionization_energy", "T_d"])
        
        assert all_valid is True
        assert len(invalid) == 0

    def test_null_values(self):
        """Test when columns contain null values."""
        df = pd.DataFrame({
            "first_ionization_energy": [5.0, np.nan, 7.0],
            "T_d": [500, 600, 700]
        })
        all_valid, invalid = verify_column_data_validity(df, columns_to_check=["first_ionization_energy"])
        
        assert all_valid is False
        assert len(invalid) == 1
        assert "first_ionization_energy" in invalid[0]

    def test_missing_column_in_check(self):
        """Test when a column to check is missing from DataFrame."""
        df = pd.DataFrame({"other_col": [1.0, 2.0]})
        all_valid, invalid = verify_column_data_validity(df, columns_to_check=["missing_col"])
        
        assert all_valid is False
        assert len(invalid) == 1
        assert "missing_col (missing)" in invalid[0]


class TestRequiredColumns:
    """Tests for the REQUIRED_COLUMNS constant."""

    def test_first_ionization_energy_present(self):
        """Verify FR-002 requirement: first_ionization_energy must be in REQUIRED_COLUMNS."""
        assert "first_ionization_energy" in REQUIRED_COLUMNS

    def test_t_d_present(self):
        """Verify T_d is in required columns."""
        assert "T_d" in REQUIRED_COLUMNS

    def test_atomic_fractions_present(self):
        """Verify atomic fraction columns are required."""
        assert "atomic_fraction_A" in REQUIRED_COLUMNS
        assert "atomic_fraction_B" in REQUIRED_COLUMNS
        assert "atomic_fraction_X" in REQUIRED_COLUMNS