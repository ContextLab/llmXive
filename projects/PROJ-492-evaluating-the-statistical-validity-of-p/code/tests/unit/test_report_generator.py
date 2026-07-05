"""
Unit tests for the report generator module (T047).
"""

import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.src.audit.report_generator import (
    load_audit_records,
    load_prevalence_data,
    calculate_summary_statistics,
    generate_summary_report,
    main
)


class TestLoadAuditRecords:
    def test_load_list_format(self, tmp_path):
        """Test loading a JSON file that is a list of records."""
        records = [
            {'id': 1, 'is_inconsistent': True},
            {'id': 2, 'is_inconsistent': False},
            {'id': 3, 'is_inconsistent': True}
        ]
        json_file = tmp_path / 'audit_report.json'
        with open(json_file, 'w') as f:
            json.dump(records, f)

        result = load_audit_records(json_file)
        assert result == records
        assert len(result) == 3

    def test_load_dict_with_records_key(self, tmp_path):
        """Test loading a JSON file with a 'records' key."""
        data = {
            'records': [
                {'id': 1, 'is_inconsistent': True},
                {'id': 2, 'is_inconsistent': False}
            ],
            'metadata': {'version': '1.0'}
        }
        json_file = tmp_path / 'audit_report.json'
        with open(json_file, 'w') as f:
            json.dump(data, f)

        result = load_audit_records(json_file)
        assert result == data['records']
        assert len(result) == 2

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / 'nonexistent.json'
        with pytest.raises(FileNotFoundError):
            load_audit_records(missing_file)


class TestLoadPrevalenceData:
    def test_load_valid_prevalence(self, tmp_path):
        """Test loading valid prevalence data."""
        data = {
            'bias_adjusted_rate': 0.15,
            'wilson_ci_lower': 0.12,
            'wilson_ci_upper': 0.18
        }
        json_file = tmp_path / 'prevalence.json'
        with open(json_file, 'w') as f:
            json.dump(data, f)

        result = load_prevalence_data(json_file)
        assert result['bias_adjusted_rate'] == 0.15
        assert result['wilson_ci_lower'] == 0.12
        assert result['wilson_ci_upper'] == 0.18

    def test_missing_fields(self, tmp_path):
        """Test that KeyError is raised for missing fields."""
        data = {
            'bias_adjusted_rate': 0.15,
            # Missing wilson_ci_lower and wilson_ci_upper
        }
        json_file = tmp_path / 'prevalence.json'
        with open(json_file, 'w') as f:
            json.dump(data, f)

        with pytest.raises(KeyError) as excinfo:
            load_prevalence_data(json_file)
        assert 'wilson_ci_lower' in str(excinfo.value)

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / 'nonexistent.json'
        with pytest.raises(FileNotFoundError):
            load_prevalence_data(missing_file)


class TestCalculateSummaryStatistics:
    def test_calculate_with_inconsistencies(self):
        """Test calculation with mixed consistent/inconsistent records."""
        records = [
            {'is_inconsistent': True},
            {'is_inconsistent': False},
            {'is_inconsistent': True},
            {'is_inconsistent': False},
            {'is_inconsistent': True}
        ]
        result = calculate_summary_statistics(records)
        assert result['total_summaries'] == 5
        assert result['inconsistent_count'] == 3
        assert abs(result['inconsistent_rate'] - 0.6) < 1e-6

    def test_calculate_all_consistent(self):
        """Test calculation when all records are consistent."""
        records = [
            {'is_inconsistent': False},
            {'is_inconsistent': False}
        ]
        result = calculate_summary_statistics(records)
        assert result['total_summaries'] == 2
        assert result['inconsistent_count'] == 0
        assert result['inconsistent_rate'] == 0.0

    def test_calculate_empty_list(self):
        """Test calculation with empty list."""
        result = calculate_summary_statistics([])
        assert result['total_summaries'] == 0
        assert result['inconsistent_count'] == 0
        assert result['inconsistent_rate'] == 0.0


class TestGenerateSummaryReport:
    def test_full_generation(self, tmp_path):
        """Test full report generation end-to-end."""
        # Setup input files
        audit_records = [
            {'id': 1, 'is_inconsistent': True},
            {'id': 2, 'is_inconsistent': False},
            {'id': 3, 'is_inconsistent': True}
        ]
        audit_file = tmp_path / 'audit_report.json'
        with open(audit_file, 'w') as f:
            json.dump(audit_records, f)

        prevalence_data = {
            'bias_adjusted_rate': 0.123456,
            'wilson_ci_lower': 0.10,
            'wilson_ci_upper': 0.15
        }
        prevalence_file = tmp_path / 'prevalence.json'
        with open(prevalence_file, 'w') as f:
            json.dump(prevalence_data, f)

        output_file = tmp_path / 'summary_report.csv'

        # Generate report
        result_path = generate_summary_report(audit_file, prevalence_file, output_file)

        # Verify output
        assert result_path.exists()
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert int(row['total_summaries']) == 3
        assert int(row['inconsistent_count']) == 2
        assert abs(float(row['inconsistent_rate']) - (2/3)) < 0.0001
        assert float(row['bias_adjusted_rate']) == 0.123456
        assert float(row['wilson_ci_lower']) == 0.10
        assert float(row['wilson_ci_upper']) == 0.15

    def test_output_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        audit_records = [{'is_inconsistent': False}]
        audit_file = tmp_path / 'audit_report.json'
        with open(audit_file, 'w') as f:
            json.dump(audit_records, f)

        prevalence_data = {
            'bias_adjusted_rate': 0.1,
            'wilson_ci_lower': 0.05,
            'wilson_ci_upper': 0.15
        }
        prevalence_file = tmp_path / 'prevalence.json'
        with open(prevalence_file, 'w') as f:
            json.dump(prevalence_data, f)

        # Create nested output path
        output_file = tmp_path / 'subdir' / 'nested' / 'summary_report.csv'

        result_path = generate_summary_report(audit_file, prevalence_file, output_file)
        assert result_path.exists()


class TestMain:
    @patch('code.src.audit.report_generator.generate_summary_report')
    @patch('code.src.audit.report_generator.Path')
    def test_main_success(self, mock_path, mock_generate, caplog):
        """Test main function success path."""
        mock_path.return_value.parent = MagicMock()
        mock_path.return_value.parent.mkdir = MagicMock()
        mock_generate.return_value = MagicMock()

        result = main()
        assert result == 0

    @patch('code.src.audit.report_generator.generate_summary_report')
    @patch('code.src.audit.report_generator.Path')
    def test_main_file_not_found(self, mock_path, mock_generate, caplog):
        """Test main function with FileNotFoundError."""
        mock_path.return_value.parent = MagicMock()
        mock_path.return_value.parent.mkdir = MagicMock()
        mock_generate.side_effect = FileNotFoundError("Test error")

        result = main()
        assert result == 1

    @patch('code.src.audit.report_generator.generate_summary_report')
    @patch('code.src.audit.report_generator.Path')
    def test_main_key_error(self, mock_path, mock_generate, caplog):
        """Test main function with KeyError."""
        mock_path.return_value.parent = MagicMock()
        mock_path.return_value.parent.mkdir = MagicMock()
        mock_generate.side_effect = KeyError("Test error")

        result = main()
        assert result == 1