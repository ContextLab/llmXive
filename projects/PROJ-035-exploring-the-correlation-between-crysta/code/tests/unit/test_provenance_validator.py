"""
Unit tests for the provenance validator module.
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

    def test_valid_nist_reference(self):
        """Test that NIST references are recognized as valid."""
        assert is_valid_source_reference("NIST Standard Reference Database") is True
        assert is_valid_source_reference("Data from nist.gov") is True

    def test_valid_journal_reference(self):
        """Test that journal references are recognized as valid."""
        assert is_valid_source_reference("Journal of Materials Science, 2020") is True
        assert is_valid_source_reference("Applied Physics Letters, doi:10.1063/1.2345") is True

    def test_valid_doi_reference(self):
        """Test that DOI references are recognized as valid."""
        assert is_valid_source_reference("doi:10.1038/s41524-020-00403-7") is True
        assert is_valid_source_reference("https://doi.org/10.1038/s41524-020-00403-7") is True

    def test_invalid_none_reference(self):
        """Test that None references are invalid."""
        assert is_valid_source_reference(None) is False

    def test_invalid_empty_reference(self):
        """Test that empty references are invalid."""
        assert is_valid_source_reference("") is False
        assert is_valid_source_reference("   ") is False

    def test_invalid_unknown_source(self):
        """Test that unknown sources are invalid."""
        assert is_valid_source_reference("Unknown source without DOI or journal") is False
        assert is_valid_source_reference("Personal communication") is False


class TestValidateProvenance:
    """Tests for validate_provenance function."""

    def test_validate_all_valid(self):
        """Test validation with all valid references."""
        df = pd.DataFrame({
            'structure_id': ['mp-1', 'mp-2', 'mp-3'],
            'source_reference': [
                'Journal of Materials Science',
                'doi:10.1038/s41524-020-00403-7',
                'NIST Database'
            ],
            'thermal_conductivity': [10.5, 12.3, 8.7]
        })

        valid_df, report = validate_provenance(df)

        assert len(valid_df) == 3
        assert report['valid_entries'] == 3
        assert report['invalid_entries'] == 0
        assert report['validity_rate'] == 1.0

    def test_validate_mixed_validity(self):
        """Test validation with mixed valid/invalid references."""
        df = pd.DataFrame({
            'structure_id': ['mp-1', 'mp-2', 'mp-3', 'mp-4'],
            'source_reference': [
                'Journal of Materials Science',
                'Unknown source',
                'doi:10.1038/s41524-020-00403-7',
                'Personal communication'
            ],
            'thermal_conductivity': [10.5, 12.3, 8.7, 15.2]
        })

        valid_df, report = validate_provenance(df)

        assert len(valid_df) == 2
        assert report['valid_entries'] == 2
        assert report['invalid_entries'] == 2
        assert report['validity_rate'] == 0.5

    def test_validate_missing_columns(self):
        """Test validation fails when required columns are missing."""
        df = pd.DataFrame({
            'structure_id': ['mp-1'],
            'thermal_conductivity': [10.5]
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_provenance(df)


class TestFilterValidProvenance:
    """Tests for filter_valid_provenance function."""

    def test_filter_with_sufficient_samples(self):
        """Test filtering when sufficient valid samples exist."""
        df = pd.DataFrame({
            'structure_id': [f'mp-{i}' for i in range(60)],
            'source_reference': ['Journal of Materials Science'] * 60,
            'thermal_conductivity': [10.0 + i * 0.1 for i in range(60)]
        })

        filtered_df = filter_valid_provenance(df)

        assert len(filtered_df) == 60

    def test_filter_with_insufficient_samples(self):
        """Test filtering fails when insufficient valid samples exist."""
        df = pd.DataFrame({
            'structure_id': [f'mp-{i}' for i in range(30)],
            'source_reference': ['Journal of Materials Science'] * 30,
            'thermal_conductivity': [10.0 + i * 0.1 for i in range(30)]
        })

        with pytest.raises(ValueError, match="Insufficient samples after provenance filtering"):
            filter_valid_provenance(df)

    def test_filter_removes_invalid(self):
        """Test that invalid references are removed."""
        df = pd.DataFrame({
            'structure_id': ['mp-1', 'mp-2', 'mp-3', 'mp-4', 'mp-5'],
            'source_reference': [
                'Journal of Materials Science',
                'Unknown',
                'doi:10.1038/s41524-020-00403-7',
                'Personal',
                'NIST Database'
            ],
            'thermal_conductivity': [10.0, 11.0, 12.0, 13.0, 14.0]
        })

        filtered_df = filter_valid_provenance(df)

        assert len(filtered_df) == 3
        assert all(
            filtered_df.apply(lambda row: is_valid_source_reference(row['source_reference']), axis=1)
        )


class TestSaveValidationReport:
    """Tests for save_validation_report function."""

    def test_save_report_creates_file(self):
        """Test that the report file is created."""
        report = {
            'total_entries': 100,
            'valid_entries': 80,
            'invalid_entries': 20,
            'validity_rate': 0.8,
            'validation_timestamp': '2024-01-01T00:00:00',
            'validation_details': [
                {'index': 0, 'structure_id': 'mp-1', 'is_valid': True},
                {'index': 1, 'structure_id': 'mp-2', 'is_valid': False}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.json'
            save_validation_report(report, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                saved_report = json.load(f)

            assert saved_report['total_entries'] == 100
            assert saved_report['valid_entries'] == 80
            assert saved_report['invalid_entries'] == 20

    def test_save_report_with_empty_details(self):
        """Test saving report with empty validation details."""
        report = {
            'total_entries': 0,
            'valid_entries': 0,
            'invalid_entries': 0,
            'validity_rate': 0.0,
            'validation_timestamp': '2024-01-01T00:00:00',
            'validation_details': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_report.json'
            save_validation_report(report, output_path)

            assert output_path.exists()