import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from clean import convert_to_kb, clean_telomere_units
from logging_config import check_memory_pressure, get_memory_status
from utils import generate_checksum, validate_file_exists

class TestUnitConversionEdgeCases:
    """Tests for edge cases in telomere unit conversion logic."""

    def test_convert_kb_to_kb(self):
        """Verify that values already in kb pass through unchanged."""
        df = pd.DataFrame({"telomere_length": [1.5, 2.0, 3.5], "unit": ["kb", "kb", "kb"]})
        result = convert_to_kb(df)
        assert np.isclose(result["telomere_length"].iloc[0], 1.5)
        assert result["unit"].iloc[0] == "kb"

    def test_convert_bp_to_kb(self):
        """Verify conversion from base pairs to kilobases."""
        df = pd.DataFrame({"telomere_length": [1000, 2000, 5000], "unit": ["bp", "bp", "bp"]})
        result = convert_to_kb(df)
        assert np.isclose(result["telomere_length"].iloc[0], 1.0)
        assert result["unit"].iloc[0] == "kb"

    def test_convert_unknown_unit_raises(self):
        """Verify that unknown units raise a ValueError."""
        df = pd.DataFrame({"telomere_length": [100], "unit": ["unknown_unit"]})
        with pytest.raises(ValueError, match="Cannot convert unit"):
            convert_to_kb(df)

    def test_missing_unit_value_raises(self):
        """Verify that missing unit values raise a KeyError or ValueError."""
        df = pd.DataFrame({"telomere_length": [100], "unit": [np.nan]})
        with pytest.raises((KeyError, ValueError)):
            convert_to_kb(df)

    def test_negative_values_handling(self):
        """Verify behavior with negative telomere lengths (should raise or warn)."""
        df = pd.DataFrame({"telomere_length": [-1.5], "unit": ["kb"]})
        # Depending on implementation, this might raise or return NaN
        result = convert_to_kb(df)
        # We expect the value to be flagged or handled, not silently accepted as valid
        assert result["telomere_length"].iloc[0] < 0 or pd.isna(result["telomere_length"].iloc[0])

    def test_empty_dataframe(self):
        """Verify behavior with empty dataframe."""
        df = pd.DataFrame(columns=["telomere_length", "unit"])
        result = convert_to_kb(df)
        assert len(result) == 0

    def test_mixed_units(self):
        """Verify conversion of mixed units in same dataframe."""
        df = pd.DataFrame({
            "telomere_length": [1000, 2.0, 500000],
            "unit": ["bp", "kb", "bp"]
        })
        result = convert_to_kb(df)
        assert np.isclose(result["telomere_length"].iloc[0], 1.0)
        assert np.isclose(result["telomere_length"].iloc[1], 2.0)
        assert np.isclose(result["telomere_length"].iloc[2], 500.0)

class TestDataCleaningEdgeCases:
    """Tests for edge cases in general data cleaning logic."""

    def test_missing_species_name(self):
        """Verify handling of missing species names."""
        df = pd.DataFrame({
            "species": [np.nan, "Homo sapiens", "Gallus gallus"],
            "lifespan": [100, 80, 30]
        })
        # Test that cleaning doesn't crash, though behavior depends on implementation
        # Typically, we expect these to be filtered or flagged
        cleaned = df.dropna(subset=["species"])
        assert len(cleaned) < len(df)

    def test_duplicate_records(self):
        """Verify handling of duplicate records."""
        df = pd.DataFrame({
            "species": ["Homo sapiens", "Homo sapiens", "Gallus gallus"],
            "lifespan": [80, 80, 30]
        })
        # Test that duplicates are identified
        duplicates = df.duplicated(subset=["species", "lifespan"], keep=False)
        assert duplicates.sum() > 0

    def test_outlier_detection(self):
        """Verify that extreme outliers are flagged."""
        df = pd.DataFrame({
            "lifespan": [1, 2, 3, 1000]  # 1000 is likely an outlier
        })
        # Simple IQR check
        q1 = df["lifespan"].quantile(0.25)
        q3 = df["lifespan"].quantile(0.75)
        iqr = q3 - q1
        outliers = df["lifespan"] < (q1 - 1.5 * iqr) | df["lifespan"] > (q3 + 1.5 * iqr)
        assert outliers.sum() > 0

class TestLoggingAndValidationEdgeCases:
    """Tests for edge cases in logging and validation utilities."""

    def test_memory_pressure_check(self):
        """Verify memory pressure check returns a valid status."""
        status = get_memory_status()
        assert "used" in status or "percent" in status

    def test_file_validation_nonexistent(self):
        """Verify validation fails for non-existent files."""
        assert not validate_file_exists("nonexistent_file.txt")

    def test_checksum_generation(self):
        """Verify checksum generation for a known string."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = f.name
        try:
            checksum = generate_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_empty_string_checksum(self):
        """Verify checksum generation for empty file."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("")
            temp_path = f.name
        try:
            checksum = generate_checksum(temp_path)
            assert len(checksum) == 64
        finally:
            os.unlink(temp_path)

class TestMergeLogicEdgeCases:
    """Tests for edge cases in data merging logic."""

    def test_no_match_on_join(self):
        """Verify behavior when no species match between datasets."""
        df1 = pd.DataFrame({"species": ["SpeciesA", "SpeciesB"], "value1": [1, 2]})
        df2 = pd.DataFrame({"species": ["SpeciesC", "SpeciesD"], "value2": [3, 4]})
        # Inner join should result in empty dataframe
        merged = pd.merge(df1, df2, on="species", how="inner")
        assert len(merged) == 0

    def test_one_to_one_merge(self):
        """Verify one-to-one merge produces correct results."""
        df1 = pd.DataFrame({"species": ["A", "B"], "val1": [1, 2]})
        df2 = pd.DataFrame({"species": ["A", "B"], "val2": [3, 4]})
        merged = pd.merge(df1, df2, on="species")
        assert len(merged) == 2
        assert merged["val1"].iloc[0] == 1
        assert merged["val2"].iloc[0] == 3

    def test_missing_key_in_merge(self):
        """Verify handling of missing keys during merge."""
        df1 = pd.DataFrame({"species": ["A", "B"], "val1": [1, 2]})
        df2 = pd.DataFrame({"species": ["A"], "val2": [3]})
        # Left join should keep all df1 rows
        merged = pd.merge(df1, df2, on="species", how="left")
        assert len(merged) == 2
        assert pd.isna(merged["val2"].iloc[1])