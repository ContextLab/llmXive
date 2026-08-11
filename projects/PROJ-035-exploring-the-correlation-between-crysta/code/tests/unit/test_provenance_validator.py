"""
Unit tests for the provenance_validator module.
"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import json

from cleaning.provenance_validator import (
    is_valid_source_reference,
    validate_provenance,
    filter_valid_provenance,
    save_validation_report
)


class TestIsValidSourceReference:
    """Tests for is_valid_source_reference function."""

    def test_valid_doi(self):
        """Test that DOI references are considered valid."""
        is_valid, reason = is_valid_source_reference("https://doi.org/10.1038/s41586-021-00000-0")
        assert is_valid is True
        assert "DOI" in reason

    def test_valid_nist(self):
        """Test that NIST references are considered valid."""
        is_valid, reason = is_valid_source_reference("NIST Standard Reference Database 69")
        assert is_valid is True
        assert "NIST" in reason

    def test_valid_journal_name(self):
        """Test that journal names are considered valid."""
        is_valid, reason = is_valid_source_reference("Physical Review B, 123, 456 (2020)")
        assert is_valid is True
        assert "keyword" in reason

    def test_invalid_empty(self):
        """Test that empty references are invalid."""
        is_valid, reason = is_valid_source_reference("")
        assert is_valid is False
        assert "Missing" in reason or "empty" in reason.lower()

    def test_invalid_none(self):
        """Test that None references are invalid."""
        is_valid, reason = is_valid_source_reference(None)
        assert is_valid is False
        assert "Missing" in reason or "empty" in reason.lower()

    def test_invalid_unknown_source(self):
        """Test that unknown sources are invalid."""
        is_valid, reason = is_valid_source_reference("Unknown blog post about crystals")
        assert is_valid is False
        assert "does not match" in reason.lower()


class TestValidateProvenance:
    """Tests for validate_provenance function."""

    def test_all_valid(self):
        """Test validation with all valid entries."""
        df = pd.DataFrame({
            "structure_id": ["1", "2", "3"],
            "thermal_conductivity": [1.0, 2.0, 3.0],
            "source_reference": [
                "https://doi.org/10.1038/s41586-021-00000-0",
                "NIST Standard Reference Database 69",
                "Physical Review B, 123, 456 (2020)"
            ]
        })

        validated_df, report = validate_provenance(df)

        assert report["total_entries"] == 3
        assert report["valid_entries"] == 3
        assert report["invalid_entries"] == 0
        assert report["all_valid"] is True

    def test_mixed_validity(self):
        """Test validation with mixed valid and invalid entries."""
        df = pd.DataFrame({
            "structure_id": ["1", "2", "3"],
            "thermal_conductivity": [1.0, 2.0, 3.0],
            "source_reference": [
                "https://doi.org/10.1038/s41586-021-00000-0",
                "Unknown blog",
                "NIST Standard Reference Database 69"
            ]
        })

        validated_df, report = validate_provenance(df)

        assert report["total_entries"] == 3
        assert report["valid_entries"] == 2
        assert report["invalid_entries"] == 1
        assert report["all_valid"] is False
        assert len(report["invalid_details"]) == 1

    def test_all_invalid_raises_error(self):
        """Test that all invalid entries raise a ValueError."""
        df = pd.DataFrame({
            "structure_id": ["1", "2", "3"],
            "thermal_conductivity": [1.0, 2.0, 3.0],
            "source_reference": [
                "Unknown blog 1",
                "Unknown blog 2",
                "Unknown blog 3"
            ]
        })

        with pytest.raises(ValueError, match="No valid peer-reviewed or NIST sources found"):
            validate_provenance(df)

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise a ValueError."""
        df = pd.DataFrame({
            "structure_id": ["1", "2", "3"],
            "thermal_conductivity": [1.0, 2.0, 3.0]
            # Missing source_reference
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_provenance(df)


class TestFilterValidProvenance:
    """Tests for filter_valid_provenance function."""

    def test_filter_removes_invalid(self):
        """Test that filtering removes invalid entries."""
        df = pd.DataFrame({
            "structure_id": ["1", "2", "3", "4"],
            "thermal_conductivity": [1.0, 2.0, 3.0, 4.0],
            "source_reference": [
                "https://doi.org/10.1038/s41586-021-00000-0",
                "Unknown blog",
                "NIST Standard Reference Database 69",
                "Another invalid source"
            ]
        })

        filtered_df = filter_valid_provenance(df)

        assert len(filtered_df) == 2
        assert all(
            is_valid_source_reference(ref)[0]
            for ref in filtered_df["source_reference"]
        )

    def test_filter_preserves_valid(self):
        """Test that filtering preserves all valid entries."""
        df = pd.DataFrame({
            "structure_id": ["1", "2"],
            "thermal_conductivity": [1.0, 2.0],
            "source_reference": [
                "https://doi.org/10.1038/s41586-021-00000-0",
                "NIST Standard Reference Database 69"
            ]
        })

        filtered_df = filter_valid_provenance(df)

        assert len(filtered_df) == 2
        assert list(filtered_df["structure_id"]) == ["1", "2"]


class TestSaveValidationReport:
    """Tests for save_validation_report function."""

    def test_save_report(self):
        """Test that the report is saved correctly."""
        report = {
            "total_entries": 10,
            "valid_entries": 8,
            "invalid_entries": 2,
            "validity_rate": 0.8,
            "invalid_details": [],
            "all_valid": False
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            save_validation_report(report, output_path)

            assert output_path.exists()
            with open(output_path, "r") as f:
                saved_report = json.load(f)

            assert saved_report["total_entries"] == 10
            assert saved_report["valid_entries"] == 8
            assert saved_report["invalid_entries"] == 2