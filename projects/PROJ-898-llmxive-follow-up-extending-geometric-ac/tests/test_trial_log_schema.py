"""
Unit tests for the trial log schema and logger.
"""
import os
import csv
import tempfile
import pytest
from code.trial_log_schema import (
    TRIAL_LOG_COLUMNS,
    TrialLogEntry,
    TrialLogger,
    get_schema_description,
    verify_schema
)

class TestTrialLogEntry:
    def test_to_row_conversion(self):
        """Test that to_row() produces the correct dictionary format."""
        entry = TrialLogEntry(
            trial_id="trial_123",
            step=5,
            success=True,
            infeasible=False,
            timeout=False,
            latency_ms=10.5
        )
        row = entry.to_row()
        
        assert row["trial_id"] == "trial_123"
        assert row["step"] == 5
        assert row["success"] == 1
        assert row["infeasible"] == 0
        assert row["timeout"] == 0
        assert row["latency_ms"] == 10.5

    def test_to_row_conversion_false_values(self):
        """Test that boolean False values are converted to 0."""
        entry = TrialLogEntry(
            trial_id=1,
            step=0,
            success=False,
            infeasible=True,
            timeout=False,
            latency_ms=0.0
        )
        row = entry.to_row()
        
        assert row["success"] == 0
        assert row["infeasible"] == 1
        assert row["timeout"] == 0

class TestTrialLogger:
    @pytest.fixture
    def temp_csv_path(self):
        """Create a temporary file path for testing."""
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_write_single_entry(self, temp_csv_path):
        """Test writing a single entry to CSV."""
        entry = TrialLogEntry(1, 0, True, False, False, 10.0)
        
        with TrialLogger(temp_csv_path) as logger:
            logger.write_entry(entry)
        
        # Verify file contents
        with open(temp_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['trial_id'] == '1'
            assert rows[0]['step'] == '0'
            assert rows[0]['success'] == '1'
            assert rows[0]['latency_ms'] == '10.0'

    def test_write_multiple_entries(self, temp_csv_path):
        """Test writing multiple entries to CSV."""
        entries = [
            TrialLogEntry(1, 0, True, False, False, 10.0),
            TrialLogEntry(1, 1, True, False, False, 12.0),
            TrialLogEntry(2, 0, False, True, False, 0.0),
        ]
        
        with TrialLogger(temp_csv_path) as logger:
            logger.write_entries(entries)
        
        with open(temp_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0]['trial_id'] == '1'
            assert rows[2]['infeasible'] == '1'

    def test_context_manager_cleanup(self, temp_csv_path):
        """Test that the context manager properly closes the file."""
        entry = TrialLogEntry(1, 0, True, False, False, 10.0)
        
        with TrialLogger(temp_csv_path) as logger:
            logger.write_entry(entry)
        
        # Try to open for writing again - should work if closed properly
        try:
            with open(temp_csv_path, 'a') as f:
                f.write("\n")
            assert True
        except IOError:
            pytest.fail("File was not properly closed by context manager")

    def test_verify_schema_success(self, temp_csv_path):
        """Test schema verification on a valid file."""
        entry = TrialLogEntry(1, 0, True, False, False, 10.0)
        
        with TrialLogger(temp_csv_path) as logger:
            logger.write_entry(entry)
        
        assert verify_schema(temp_csv_path) is True

    def test_verify_schema_missing_file(self):
        """Test schema verification on a non-existent file."""
        assert verify_schema("/non/existent/path.csv") is False

    def test_verify_schema_wrong_header(self, temp_csv_path):
        """Test schema verification on a file with wrong header."""
        with open(temp_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["wrong", "header", "columns"])
            writer.writerow(["1", "0", "1"])
        
        assert verify_schema(temp_csv_path) is False

class TestSchemaConstants:
    def test_columns_order(self):
        """Test that the column list matches the specification."""
        expected = ["trial_id", "step", "success", "infeasible", "timeout", "latency_ms"]
        assert TRIAL_LOG_COLUMNS == expected

    def test_schema_description(self):
        """Test that schema descriptions are populated."""
        desc = get_schema_description()
        assert "trial_id" in desc
        assert "step" in desc
        assert "success" in desc
        assert "infeasible" in desc
        assert "timeout" in desc
        assert "latency_ms" in desc
        assert len(desc) == 6
