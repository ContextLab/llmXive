import pytest
import pandas as pd
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from verify_descriptors import verify_column_presence, verify_column_data_validity

class TestVerifyDescriptors:
    """Unit tests for verify_descriptors module."""

    def test_verify_column_presence_exists(self):
        """Test that presence check returns True for existing column."""
        df = pd.DataFrame({"first_ionization_energy": [1.0, 2.0, 3.0]})
        assert verify_column_presence(df, "first_ionization_energy") is True

    def test_verify_column_presence_missing(self, caplog):
        """Test that presence check returns False for missing column."""
        df = pd.DataFrame({"other_col": [1.0, 2.0, 3.0]})
        assert verify_column_presence(df, "first_ionization_energy") is False
        assert "Missing required column" in caplog.text

    def test_verify_column_data_validity_valid(self):
        """Test validity check on good data."""
        df = pd.DataFrame({"first_ionization_energy": [5.0, 6.0, 7.0]})
        assert verify_column_data_validity(df, "first_ionization_energy") is True

    def test_verify_column_data_validity_nulls(self, caplog):
        """Test validity check fails on null values."""
        df = pd.DataFrame({"first_ionization_energy": [5.0, None, 7.0]})
        assert verify_column_data_validity(df, "first_ionization_energy") is False
        assert "contains null values" in caplog.text

    def test_verify_column_data_validity_empty(self, caplog):
        """Test validity check fails on empty column."""
        df = pd.DataFrame({"first_ionization_energy": pd.Series([], dtype=float)})
        assert verify_column_data_validity(df, "first_ionization_energy") is False
        assert "is empty" in caplog.text

    def test_verify_column_data_validity_non_numeric(self, caplog):
        """Test validity check fails on non-numeric data."""
        df = pd.DataFrame({"first_ionization_energy": ["a", "b", "c"]})
        assert verify_column_data_validity(df, "first_ionization_energy") is False
        assert "is not numeric" in caplog.text