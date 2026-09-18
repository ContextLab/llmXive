"""
Unit tests for the provenance validator module.

Tests validate the regex patterns for DOI, PMID, and NIST ID,
as well as the validation and filtering logic.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.cleaning.provenance_validator import (
    is_valid_source_reference,
    validate_provenance,
    filter_valid_provenance,
    save_validation_report
)


class TestIsValidSourceReference:
    """Tests for is_valid_source_reference function."""

    def test_valid_doi(self):
        """Test valid DOI patterns."""
        assert is_valid_source_reference("10.1038/s41524-021-00567-8") is True
        assert is_valid_source_reference("10.1103/PhysRevB.103.125412") is True
        assert is_valid_source_reference("10.1021/acs.chemmater.1c01234") is True

    def test_invalid_doi(self):
        """Test invalid DOI patterns."""
        assert is_valid_source_reference("10.1038") is False
        assert is_valid_source_reference("10.1038/") is False
        assert is_valid_source_reference("10.123/abc") is False  # Only 4 digits
        assert is_valid_source_reference("http://doi.org/10.1038/s41524-021-00567-8") is False

    def test_valid_pmid(self):
        """Test valid PMID patterns."""
        assert is_valid_source_reference("10.1000/12345") is True
        assert is_valid_source_reference("10.1234/67890") is True

    def test_invalid_pmid(self):
        """Test invalid PMID patterns."""
        assert is_valid_source_reference("10.100/12345") is False  # Only 3 digits
        assert is_valid_source_reference("10.1000/abc") is False
        assert is_valid_source_reference("10.1000/12345/extra") is False

    def test_valid_nist_id(self):
        """Test valid NIST ID patterns."""
        assert is_valid_source_reference("NIST-ABC123") is True
        assert is_valid_source_reference("NIST-XYZ789") is True
        assert is_valid_source_reference("NIST-12345") is True

    def test_invalid_nist_id(self):
        """Test invalid NIST ID patterns."""
        assert is_valid_source_reference("nist-abc123") is False  # lowercase
        assert is_valid_source_reference("NIST_ABC123") is False  # underscore
        assert is_valid_source_reference("NIST-") is False
        assert is_valid_source_reference("NISTABC123") is False

    def test_empty_and_none(self):
        """Test empty and None inputs."""
        assert is_valid_source_reference("") is False
        assert is_valid_source_reference("   ") is False
        assert is_valid_source_reference(None) is False

    def test_invalid_format(self):
        """Test invalid format strings."""
        assert is_valid_source_reference("random text") is False
        assert is_valid_source_reference("doi:10.1038/s41524-021-00567-8") is False


class TestValidateProvenance:
    """Tests for validate_provenance function."""

    def test_validate_mixed_provenance(self):
        """Test validation with mixed valid and invalid entries."""
        df = pd.DataFrame({
            "structure_id": ["A", "B", "C", "D"],
            "source_reference": [
                "10.1038/s41524-021-00567-8",  # Valid DOI
                "NIST-ABC123",                  # Valid NIST
                "invalid-ref",                  # Invalid
                "10.1000/12345"                 # Valid PMID
            ]
        })

        valid, invalid = validate_provenance(df)

        assert len(valid) == 3
        assert len(invalid) == 1
        assert invalid[0]["structure_id"] == "C"

    def test_validate_all_valid(self):
        """Test validation when all entries are valid."""
        df = pd.DataFrame({
            "structure_id": ["A", "B"],
            "source_reference": [
                "10.1038/s41524-021-00567-8",
                "NIST-XYZ789"
            ]
        })

        valid, invalid = validate_provenance(df)

        assert len(valid) == 2
        assert len(invalid) == 0

    def test_validate_all_invalid(self):
        """Test validation when all entries are invalid."""
        df = pd.DataFrame({
            "structure_id": ["A", "B"],
            "source_reference": [
                "invalid1",
                "invalid2"
            ]
        })

        valid, invalid = validate_provenance(df)

        assert len(valid) == 0
        assert len(invalid) == 2

    def test_validate_empty_dataframe(self):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame(columns=["structure_id", "source_reference"])

        valid, invalid = validate_provenance(df)

        assert len(valid) == 0
        assert len(invalid) == 0


class TestFilterValidProvenance:
    """Tests for filter_valid_provenance function."""

    def test_filter_mixed(self):
        """Test filtering with mixed valid and invalid entries."""
        df = pd.DataFrame({
            "structure_id": ["A", "B", "C"],
            "source_reference": [
                "10.1038/s41524-021-00567-8",
                "invalid",
                "NIST-ABC123"
            ],
            "thermal_conductivity": [1.0, 2.0, 3.0]
        })

        filtered = filter_valid_provenance(df)

        assert len(filtered) == 2
        assert list(filtered["structure_id"]) == ["A", "C"]

    def test_filter_all_valid(self):
        """Test filtering when all entries are valid."""
        df = pd.DataFrame({
            "structure_id": ["A", "B"],
            "source_reference": [
                "10.1038/s41524-021-00567-8",
                "NIST-ABC123"
            ]
        })

        filtered = filter_valid_provenance(df)

        assert len(filtered) == 2

    def test_filter_all_invalid(self):
        """Test filtering when all entries are invalid."""
        df = pd.DataFrame({
            "structure_id": ["A", "B"],
            "source_reference": ["invalid1", "invalid2"]
        })

        filtered = filter_valid_provenance(df)

        assert len(filtered) == 0


class TestSaveValidationReport:
    """Tests for save_validation_report function."""

    def test_save_report(self):
        """Test saving a validation report."""
        valid_entries = [
            {"row_index": 0, "structure_id": "A", "source_reference": "10.1038/s41524-021-00567-8", "is_valid": True}
        ]
        invalid_entries = [
            {"row_index": 1, "structure_id": "B", "source_reference": "invalid", "is_valid": False}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            
            save_validation_report(1, 1, valid_entries, invalid_entries, output_path)

            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["summary"]["valid_count"] == 1
            assert report["summary"]["invalid_count"] == 1
            assert len(report["valid_entries"]) == 1
            assert len(report["invalid_entries"]) == 1

    def test_save_report_empty(self):
        """Test saving a report with no entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report_empty.json"
            
            save_validation_report(0, 0, [], [], output_path)

            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["summary"]["valid_count"] == 0
            assert report["summary"]["invalid_count"] == 0
            assert report["summary"]["validation_rate"] == 0.0