"""
Tests for T023b: Verify Grid Generation
"""

import csv
import json
import os
import tempfile
import pytest
from unittest.mock import patch

# We need to import the verify_grid module logic
# Since it's in code/verify_grid.py, we add the parent directory to sys.path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

import verify_grid


class TestVerifyFile:
    """Tests for the verify_file function."""

    def test_file_does_not_exist(self, tmp_path):
        """Test that a non-existent file returns correct result."""
        non_existent_path = str(tmp_path / "does_not_exist.csv")
        result = verify_grid.verify_file(
            non_existent_path,
            'spec',
            verify_grid.EXPECTED_COLUMNS
        )

        assert result['exists'] is False
        assert result['non_zero_rows'] is False
        assert result['source_column_valid'] is False
        assert result['schema_valid'] is False
        assert len(result['errors']) > 0
        assert "does not exist" in result['errors'][0]

    def test_empty_file(self, tmp_path):
        """Test that an empty file (header only) is detected."""
        file_path = tmp_path / "empty.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=verify_grid.EXPECTED_COLUMNS)
            writer.writeheader()

        result = verify_grid.verify_file(
            str(file_path),
            'spec',
            verify_grid.EXPECTED_COLUMNS
        )

        assert result['exists'] is True
        assert result['non_zero_rows'] is False
        assert result['row_count'] == 0
        assert "zero data rows" in result['errors'][0]

    def test_missing_columns(self, tmp_path):
        """Test that missing required columns are detected."""
        file_path = tmp_path / "missing_cols.csv"
        # Write header with missing columns
        partial_columns = {'x', 'y', 'h'}  # Missing start_offset, count, density, ratio
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=partial_columns)
            writer.writeheader()
            writer.writerow({'x': 100, 'y': 10, 'h': 5})

        result = verify_grid.verify_file(
            str(file_path),
            'spec',
            verify_grid.EXPECTED_COLUMNS
        )

        assert result['schema_valid'] is False
        assert "Missing required columns" in result['errors'][0]

    def test_valid_file_with_correct_source(self, tmp_path):
        """Test a valid file with the correct source value."""
        file_path = tmp_path / "valid.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=verify_grid.EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'x': 1000, 'y': 10, 'h': 50, 'start_offset': 0,
                'count': 10, 'density': 0.2, 'ratio': 1.0, 'source': 'spec'
            })
            writer.writerow({
                'x': 2000, 'y': 20, 'h': 100, 'start_offset': 10,
                'count': 20, 'density': 0.2, 'ratio': 1.0, 'source': 'spec'
            })

        result = verify_grid.verify_file(
            str(file_path),
            'spec',
            verify_grid.EXPECTED_COLUMNS
        )

        assert result['exists'] is True
        assert result['non_zero_rows'] is True
        assert result['row_count'] == 2
        assert result['schema_valid'] is True
        assert result['source_column_valid'] is True
        assert len(result['errors']) == 0

    def test_invalid_source_value(self, tmp_path):
        """Test that an incorrect source value is detected."""
        file_path = tmp_path / "invalid_source.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=verify_grid.EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'x': 1000, 'y': 10, 'h': 50, 'start_offset': 0,
                'count': 10, 'density': 0.2, 'ratio': 1.0, 'source': 'wrong_source'
            })

        result = verify_grid.verify_file(
            str(file_path),
            'spec',
            verify_grid.EXPECTED_COLUMNS
        )

        assert result['source_column_valid'] is False
        assert "does not contain expected value" in result['errors'][0]

    def test_mixed_source_values(self, tmp_path):
        """Test that mixed source values are detected as invalid for a single source file."""
        file_path = tmp_path / "mixed_source.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=verify_grid.EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'x': 1000, 'y': 10, 'h': 50, 'start_offset': 0,
                'count': 10, 'density': 0.2, 'ratio': 1.0, 'source': 'spec'
            })
            writer.writerow({
                'x': 2000, 'y': 20, 'h': 100, 'start_offset': 10,
                'count': 20, 'density': 0.2, 'ratio': 1.0, 'source': 'plan'
            })

        # We expect this to fail because the file should only contain 'spec'
        result = verify_grid.verify_file(
            str(file_path),
            'spec',
            verify_grid.EXPECTED_COLUMNS
        )

        assert result['source_column_valid'] is False
        assert "unexpected values" in result['errors'][0]

class TestMainFunction:
    """Tests for the main function logic (integration-like)."""

    def test_main_with_missing_files(self, tmp_path, monkeypatch):
        """Test main when files are missing."""
        # Mock the file paths to point to tmp_path
        monkeypatch.setattr(verify_grid, 'SPEC_FILE_PATH', str(tmp_path / "missing_spec.csv"))
        monkeypatch.setattr(verify_grid, 'PLAN_FILE_PATH', str(tmp_path / "missing_plan.csv"))
        monkeypatch.setattr(verify_grid, 'OUTPUT_REPORT_PATH', str(tmp_path / "report.json"))

        exit_code = verify_grid.main()

        assert exit_code == 1
        assert os.path.exists(str(tmp_path / "report.json"))
        with open(tmp_path / "report.json") as f:
            report = json.load(f)
        assert report['spec_valid'] is False
        assert report['plan_valid'] is False

    def test_main_with_valid_files(self, tmp_path, monkeypatch):
        """Test main when files are valid."""
        spec_path = tmp_path / "spec.csv"
        plan_path = tmp_path / "plan.csv"
        report_path = tmp_path / "report.json"

        # Create valid spec file
        with open(spec_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=verify_grid.EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'x': 1000, 'y': 10, 'h': 50, 'start_offset': 0,
                'count': 10, 'density': 0.2, 'ratio': 1.0, 'source': 'spec'
            })

        # Create valid plan file
        with open(plan_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=verify_grid.EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'x': 1000, 'y': 10, 'h': 50, 'start_offset': 0,
                'count': 10, 'density': 0.2, 'ratio': 1.0, 'source': 'plan'
            })

        monkeypatch.setattr(verify_grid, 'SPEC_FILE_PATH', str(spec_path))
        monkeypatch.setattr(verify_grid, 'PLAN_FILE_PATH', str(plan_path))
        monkeypatch.setattr(verify_grid, 'OUTPUT_REPORT_PATH', str(report_path))

        exit_code = verify_grid.main()

        assert exit_code == 0
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)
        assert report['spec_valid'] is True
        assert report['plan_valid'] is True
        assert 'timestamp' in report
        assert 'spec_details' in report
        assert 'plan_details' in report