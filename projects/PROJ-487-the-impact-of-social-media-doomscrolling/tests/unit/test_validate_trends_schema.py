"""
Unit tests for Trends schema validation (T004b).
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

from code.validate_trends_schema import (
    validate_row,
    validate_csv_file,
    validate_and_save_report,
    ValidationError,
    validate_date_format
)


class TestValidateDateFormat:
    def test_valid_date_format(self):
        assert validate_date_format("2023-01-15") is True
        assert validate_date_format("2023-12-31") is True
        assert validate_date_format("2000-01-01") is True

    def test_invalid_date_format(self):
        assert validate_date_format("01-15-2023") is False
        assert validate_date_format("2023/01/15") is False
        assert validate_date_format("2023-1-15") is False
        assert validate_date_format("not-a-date") is False
        assert validate_date_format("") is False


class TestValidateRow:
    def test_valid_row(self):
        row = {
            "date": "2023-05-10",
            "value": "75.5",
            "source": "Google Trends"
        }
        is_valid, error = validate_row(row, 5)
        assert is_valid is True
        assert error == ""

    def test_missing_required_field_date(self):
        row = {
            "value": "75.5",
            "source": "Google Trends"
        }
        is_valid, error = validate_row(row, 10)
        assert is_valid is False
        assert "Missing required field 'date'" in error

    def test_missing_required_field_value(self):
        row = {
            "date": "2023-05-10",
            "source": "Google Trends"
        }
        is_valid, error = validate_row(row, 10)
        assert is_valid is False
        assert "Missing required field 'value'" in error

    def test_missing_required_field_source(self):
        row = {
            "date": "2023-05-10",
            "value": "75.5"
        }
        is_valid, error = validate_row(row, 10)
        assert is_valid is False
        assert "Missing required field 'source'" in error

    def test_invalid_date_format(self):
        row = {
            "date": "10-05-2023",
            "value": "75.5",
            "source": "Google Trends"
        }
        is_valid, error = validate_row(row, 15)
        assert is_valid is False
        assert "Invalid date format" in error

    def test_invalid_value_not_number(self):
        row = {
            "date": "2023-05-10",
            "value": "not-a-number",
            "source": "Google Trends"
        }
        is_valid, error = validate_row(row, 20)
        assert is_valid is False
        assert "Invalid value" in error

    def test_empty_source(self):
        row = {
            "date": "2023-05-10",
            "value": "75.5",
            "source": ""
        }
        is_valid, error = validate_row(row, 25)
        assert is_valid is False
        assert "Invalid source" in error

    def test_empty_source_whitespace(self):
        row = {
            "date": "2023-05-10",
            "value": "75.5",
            "source": "   "
        }
        is_valid, error = validate_row(row, 26)
        assert is_valid is False
        assert "Invalid source" in error


class TestValidateCsvFile:
    def _create_temp_csv(self, rows, header=None):
        """Helper to create a temporary CSV file."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                for row in rows:
                    writer.writerow(row)
            return path
        except Exception:
            os.close(fd)
            raise

    def test_valid_csv(self):
        header = ["date", "value", "source"]
        rows = [
            ["2023-01-01", "50.0", "Google Trends"],
            ["2023-01-02", "55.5", "Google Trends"],
            ["2023-01-03", "60.0", "Google Trends"]
        ]
        path = self._create_temp_csv(rows, header)
        try:
            results = validate_csv_file(path)
            assert results["valid"] is True
            assert results["total_rows"] == 3
            assert results["valid_rows"] == 3
            assert len(results["errors"]) == 0
        finally:
            os.unlink(path)

    def test_csv_with_invalid_rows(self):
        header = ["date", "value", "source"]
        rows = [
            ["2023-01-01", "50.0", "Google Trends"],
            ["invalid-date", "55.5", "Google Trends"],
            ["2023-01-03", "not-a-number", "Google Trends"]
        ]
        path = self._create_temp_csv(rows, header)
        try:
            results = validate_csv_file(path)
            assert results["valid"] is False
            assert results["total_rows"] == 3
            assert results["valid_rows"] == 1
            assert len(results["errors"]) == 2
        finally:
            os.unlink(path)

    def test_csv_missing_required_header(self):
        header = ["date", "value"]  # Missing 'source'
        rows = [
            ["2023-01-01", "50.0"]
        ]
        path = self._create_temp_csv(rows, header)
        try:
            with pytest.raises(ValidationError) as exc_info:
                validate_csv_file(path)
            assert "missing required fields" in str(exc_info.value).lower()
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_csv_file("/nonexistent/path/file.csv")


class TestValidateAndSaveReport:
    def test_report_generation(self):
        header = ["date", "value", "source"]
        rows = [
            ["2023-01-01", "50.0", "Google Trends"],
            ["2023-01-02", "55.5", "Google Trends"]
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_path = os.path.join(tmpdir, "report.txt")
                validate_and_save_report(csv_path, report_path)
                
                assert os.path.exists(report_path)
                
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                assert "Validation PASSED" in content
                assert "Total Rows: 2" in content
        finally:
            os.unlink(csv_path)

    def test_report_with_errors(self):
        header = ["date", "value", "source"]
        rows = [
            ["2023-01-01", "50.0", "Google Trends"],
            ["invalid-date", "55.5", "Google Trends"]
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_path = os.path.join(tmpdir, "report.txt")
                
                # This should raise SystemExit due to validation failure
                with pytest.raises(SystemExit) as exc_info:
                    validate_and_save_report(csv_path, report_path)
                
                assert exc_info.value.code == 1
                assert os.path.exists(report_path)
                
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                assert "Validation FAILED" in content
                assert "Errors" in content
        finally:
            os.unlink(csv_path)