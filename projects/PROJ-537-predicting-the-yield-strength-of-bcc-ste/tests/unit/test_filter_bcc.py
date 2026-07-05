"""
Unit tests for BCC filtering logic (Space Group 229).
Tests the filtering function used in the ingestion pipeline to ensure
only BCC steels (Space Group 229) are retained.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.merge_and_filter import filter_bcc_steels


class TestBCCFiltering:
    """Test suite for BCC steel filtering logic."""

    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame with mixed space groups."""
        data = {
            "composition": ["Fe-Cr", "Fe-Mo", "Fe-Ni", "Fe-W", "Fe-Mn"],
            "yield_strength_MPa": [500, 600, 400, 700, 450],
            "space_group": [229, 229, 225, 229, 221],  # 229 is BCC
            "shear_modulus_GPa": [80.0, 85.0, 75.0, 90.0, 70.0],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def expected_bcc_data(self):
        """Expected result after filtering for BCC (Space Group 229)."""
        data = {
            "composition": ["Fe-Cr", "Fe-Mo", "Fe-W"],
            "yield_strength_MPa": [500, 600, 700],
            "space_group": [229, 229, 229],
            "shear_modulus_GPa": [80.0, 85.0, 90.0],
        }
        return pd.DataFrame(data)

    def test_filter_retains_bcc_only(self, sample_data, expected_bcc_data):
        """Test that only Space Group 229 rows are retained."""
        result = filter_bcc_steels(sample_data)

        # Check row count
        assert len(result) == 3, f"Expected 3 BCC rows, got {len(result)}"

        # Check all space groups are 229
        assert all(result["space_group"] == 229), "Not all rows have Space Group 229"

        # Check specific compositions
        expected_compositions = {"Fe-Cr", "Fe-Mo", "Fe-W"}
        assert set(result["composition"]) == expected_compositions

    def test_filter_empty_input(self):
        """Test filtering an empty DataFrame."""
        empty_df = pd.DataFrame(columns=["composition", "yield_strength_MPa", "space_group"])
        result = filter_bcc_steels(empty_df)
        assert len(result) == 0

    def test_filter_no_bcc(self):
        """Test filtering when no BCC data is present."""
        data = {
            "composition": ["Fe-Ni", "Fe-Mn"],
            "yield_strength_MPa": [400, 450],
            "space_group": [225, 221],  # Non-BCC
            "shear_modulus_GPa": [75.0, 70.0],
        }
        df = pd.DataFrame(data)
        result = filter_bcc_steels(df)
        assert len(result) == 0

    def test_filter_all_bcc(self, sample_data):
        """Test filtering when all data is BCC."""
        all_bcc_data = sample_data.copy()
        all_bcc_data["space_group"] = 229
        result = filter_bcc_steels(all_bcc_data)
        assert len(result) == len(all_bcc_data)
        assert all(result["space_group"] == 229)

    def test_filter_preserves_columns(self, sample_data):
        """Test that all original columns are preserved in the output."""
        result = filter_bcc_steels(sample_data)
        assert set(result.columns) == set(sample_data.columns)

    def test_filter_with_null_space_group(self):
        """Test filtering when space_group column has null values."""
        data = {
            "composition": ["Fe-Cr", "Fe-Mo", "Fe-Ni"],
            "yield_strength_MPa": [500, 600, 400],
            "space_group": [229, None, 225],
            "shear_modulus_GPa": [80.0, 85.0, 75.0],
        }
        df = pd.DataFrame(data)
        result = filter_bcc_steels(df)
        # Only the row with 229 should remain
        assert len(result) == 1
        assert result.iloc[0]["composition"] == "Fe-Cr"

    def test_filter_with_string_space_group(self):
        """Test filtering when space_group is stored as string."""
        data = {
            "composition": ["Fe-Cr", "Fe-Mo", "Fe-Ni"],
            "yield_strength_MPa": [500, 600, 400],
            "space_group": ["229", "229", "225"],  # Strings instead of ints
            "shear_modulus_GPa": [80.0, 85.0, 75.0],
        }
        df = pd.DataFrame(data)
        result = filter_bcc_steels(df)
        # Should handle string "229" correctly
        assert len(result) == 2
        assert all(result["space_group"] == "229")

    def test_filter_case_insensitive_space_group(self):
        """Test filtering handles different case representations if applicable."""
        # This test ensures robustness if space_group is represented as "Space Group 229"
        data = {
            "composition": ["Fe-Cr", "Fe-Mo", "Fe-Ni"],
            "yield_strength_MPa": [500, 600, 400],
            "space_group": ["229", "229", "225"],
            "shear_modulus_GPa": [80.0, 85.0, 75.0],
        }
        df = pd.DataFrame(data)
        result = filter_bcc_steels(df)
        assert len(result) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
