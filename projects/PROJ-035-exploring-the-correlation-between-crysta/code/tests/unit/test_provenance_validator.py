"""
Unit tests for the provenance_validator module.
"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import json
import sys
import os

# Add code directory to path if not already there
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.cleaning.provenance_validator import (
    is_valid_source_reference,
    validate_provenance,
    filter_valid_provenance,
    save_validation_report,
    main
)


class TestIsValidSourceReference:
    """Tests for is_valid_source_reference function."""

    def test_valid_doi(self):
        assert is_valid_source_reference("10.1000/abc123") is True
        assert is_valid_source_reference("10.1038/nature12345") is True
        assert is_valid_source_reference("10.1021/acs.jpclett.1c00001") is True

    def test_valid_pmid(self):
        # Based on regex 10.\\d{4}/\\d+
        assert is_valid_source_reference("10.1234/56789") is True
        assert is_valid_source_reference("10.1234/1") is True

    def test_valid_nist_id(self):
        assert is_valid_source_reference("NIST-AB123") is True
        assert is_valid_source_reference("NIST-X9Y8Z7") is True
        assert is_valid_source_reference("NIST-123") is True

    def test_invalid_formats(self):
        assert is_valid_source_reference("Not a reference") is False
        assert is_valid_source_reference("") is False
        assert is_valid_source_reference(None) is False
        assert is_valid_source_reference("10.1000") is False  # Missing /
        assert is_valid_source_reference("10.1000/") is False  # Missing suffix
        assert is_valid_source_reference("NIST-abc") is False  # Lowercase not allowed in pattern [A-Z0-9]
        assert is_valid_source_reference("NIST_123") is False  # Underscore not allowed

    def test_case_sensitivity_doi(self):
        # DOI is case-insensitive per regex IGNORECASE flag
        assert is_valid_source_reference("10.1000/ABC") is True

    def test_case_sensitivity_nist(self):
        # NIST pattern has IGNORECASE flag
        assert is_valid_source_reference("nist-abc123") is True


class TestValidateProvenance:
    """Tests for validate_provenance function."""

    def test_validate_dataframe(self):
        data = {
            'structure_id': ['A', 'B', 'C', 'D'],
            'source_reference': [
                "10.1000/valid",
                "NIST-VALID1",
                "invalid_ref",
                None
            ]
        }
        df = pd.DataFrame(data)
        df_validated, stats = validate_provenance(df, 'source_reference')

        assert 'provenance_valid' in df_validated.columns
        assert df_validated['provenance_valid'].iloc[0] is True
        assert df_validated['provenance_valid'].iloc[1] is True
        assert df_validated['provenance_valid'].iloc[2] is False
        assert df_validated['provenance_valid'].iloc[3] is False

        assert stats['total_records'] == 4
        assert stats['passed'] == 2
        assert stats['failed'] == 2

    def test_missing_column(self):
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(ValueError, match="Column 'source_reference' not found"):
            validate_provenance(df, 'source_reference')

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['structure_id', 'source_reference'])
        df_validated, stats = validate_provenance(df, 'source_reference')
        assert stats['total_records'] == 0
        assert stats['passed'] == 0
        assert stats['failed'] == 0
        assert stats['pass_rate'] == 0.0


class TestFilterValidProvenance:
    """Tests for filter_valid_provenance function."""

    def test_filter_valid(self):
        data = {
            'structure_id': ['A', 'B', 'C'],
            'source_reference': [
                "10.1000/valid",
                "invalid_ref",
                "NIST-VALID1"
            ]
        }
        df = pd.DataFrame(data)
        filtered = filter_valid_provenance(df, 'source_reference')

        assert len(filtered) == 2
        assert list(filtered['structure_id']) == ['A', 'C']

    def test_all_invalid(self):
        data = {
            'structure_id': ['A', 'B'],
            'source_reference': ["invalid1", "invalid2"]
        }
        df = pd.DataFrame(data)
        filtered = filter_valid_provenance(df, 'source_reference')
        assert len(filtered) == 0

    def test_all_valid(self):
        data = {
            'structure_id': ['A', 'B'],
            'source_reference': ["10.1000/valid", "NIST-VALID"]
        }
        df = pd.DataFrame(data)
        filtered = filter_valid_provenance(df, 'source_reference')
        assert len(filtered) == 2


class TestSaveValidationReport:
    """Tests for save_validation_report function."""

    def test_save_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            stats = {
                'total_records': 10,
                'passed': 8,
                'failed': 2,
                'pass_rate': 0.8
            }
            failed_entries = [
                {'index': 0, 'source_reference': 'bad'}
            ]

            save_validation_report(stats, output_path, failed_entries)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                report = json.load(f)

            assert report['validation_stats']['passed'] == 8
            assert report['validation_stats']['failed'] == 2
            assert len(report['failed_entries']) == 1


class TestMain:
    """Tests for the main CLI function."""

    def test_main_missing_input(self, capsys):
        # Create a temp dir and ensure no input file exists
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir to isolate file system
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                # Ensure data/cleaned doesn't exist
                Path("data/cleaned").mkdir(parents=True, exist_ok=True)
                ret = main()
                assert ret == 1
            finally:
                os.chdir(old_cwd)

    def test_main_success(self, tmp_path):
        # Create a mock input file
        input_data = tmp_path / "data" / "cleaned"
        input_data.mkdir(parents=True)
        input_file = input_data / "thermal_raw.csv"
        input_file.write_text("structure_id,source_reference\nA,10.1000/valid\nB,NIST-123\n")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            ret = main()
            assert ret == 0
            # Check report exists
            report_path = input_data / "provenance_report.json"
            assert report_path.exists()
            with open(report_path, 'r') as f:
                report = json.load(f)
            assert report['validation_stats']['failed'] == 0
        finally:
            os.chdir(old_cwd)

    def test_main_failure_invalid_entries(self, tmp_path):
        input_data = tmp_path / "data" / "cleaned"
        input_data.mkdir(parents=True)
        input_file = input_data / "thermal_raw.csv"
        # Include an invalid entry
        input_file.write_text("structure_id,source_reference\nA,10.1000/valid\nB,invalid\n")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            ret = main()
            assert ret == 1
            report_path = input_data / "provenance_report.json"
            assert report_path.exists()
            with open(report_path, 'r') as f:
                report = json.load(f)
            assert report['validation_stats']['failed'] == 1
        finally:
            os.chdir(old_cwd)
