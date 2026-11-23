import pytest
import os
import csv
import sys
import tempfile
import shutil
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import LoggingContext, initialize_quality_report, write_quality_entry, QUALITY_REPORT_PATH

class TestLoggingContext:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup: Create a temporary directory for test artifacts.
        Teardown: Clean up temporary directory.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.test_report_path = Path(self.temp_dir) / "test_quality_report.csv"
        
        # Temporarily override the global path for this test class
        # We will pass the path explicitly to write_report instead of relying on global state
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_exclusion_accumulates(self, setup_and_teardown):
        """Test that add_exclusion correctly accumulates counts for the same type."""
        ctx = LoggingContext()
        ctx.add_exclusion("blink_loss", 10)
        ctx.add_exclusion("blink_loss", 5)
        ctx.add_exclusion("missing_data", 2)
        
        assert ctx.exclusions["blink_loss"] == 15
        assert ctx.exclusions["missing_data"] == 2
        assert len(ctx.exclusions) == 2

    def test_write_report_creates_file(self, setup_and_teardown):
        """Test that write_report creates the CSV file with correct headers and data."""
        ctx = LoggingContext()
        ctx.add_exclusion("blink_loss", 10)
        ctx.add_exclusion("missing_data", 5)
        
        # Write to our temp path
        ctx.write_report(str(self.test_report_path))
        
        assert self.test_report_path.exists()
        
        with open(self.test_report_path, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        # Check headers
        assert rows[0] == ['exclusion_type', 'count', 'timestamp']
        
        # Check data rows (order might vary, so we check content presence)
        data_rows = rows[1:]
        assert len(data_rows) == 2
        
        # Verify content
        found_blink = False
        found_missing = False
        for row in data_rows:
            if row[0] == 'blink_loss' and int(row[1]) == 10:
                found_blink = True
            if row[0] == 'missing_data' and int(row[1]) == 5:
                found_missing = True
        
        assert found_blink, "blink_loss entry not found"
        assert found_missing, "missing_data entry not found"

    def test_write_report_appends(self, setup_and_teardown):
        """Test that write_report appends to an existing file."""
        # Create initial file with headers
        initialize_quality_report()
        # Override path for test
        import logging_config
        original_path = logging_config.QUALITY_REPORT_PATH
        logging_config.QUALITY_REPORT_PATH = self.test_report_path
        
        try:
            # Manually write headers to temp file to simulate existing file
            with open(self.test_report_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['exclusion_type', 'count', 'timestamp'])
                writer.writerow(['initial', '1', '2023-01-01'])
            
            ctx = LoggingContext()
            ctx.add_exclusion("new_exclusion", 42)
            ctx.write_report(str(self.test_report_path))
            
            with open(self.test_report_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert len(rows) == 3 # Header + initial + new
            assert rows[2][0] == 'new_exclusion'
            assert int(rows[2][1]) == 42
        finally:
            # Restore original path
            logging_config.QUALITY_REPORT_PATH = original_path

    def test_add_exclusion_negative_count_fails(self, setup_and_teardown):
        """Test that adding a negative count raises ValueError."""
        ctx = LoggingContext()
        with pytest.raises(ValueError):
            ctx.add_exclusion("error_type", -1)

class TestInitializeQualityReport:
    def test_creates_file_with_headers(self, tmp_path):
        """Test that initialize_quality_report creates the file with correct headers."""
        # Mock the global path
        import logging_config
        original_path = logging_config.QUALITY_REPORT_PATH
        test_path = tmp_path / "quality_report.csv"
        logging_config.QUALITY_REPORT_PATH = test_path
        
        try:
            assert not test_path.exists()
            initialize_quality_report()
            assert test_path.exists()
            
            with open(test_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
            
            assert headers == ['exclusion_type', 'count', 'timestamp']
        finally:
            logging_config.QUALITY_REPORT_PATH = original_path

class TestWriteQualityEntry:
    def test_writes_entry_correctly(self, tmp_path):
        """Test that write_quality_entry appends a row correctly."""
        import logging_config
        original_path = logging_config.QUALITY_REPORT_PATH
        test_path = tmp_path / "quality_report.csv"
        logging_config.QUALITY_REPORT_PATH = test_path
        
        try:
            initialize_quality_report()
            write_quality_entry("test_type", 99)
            
            with open(test_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert len(rows) == 2 # Header + 1 entry
            assert rows[1][0] == 'test_type'
            assert int(rows[1][1]) == 99
            # Check that timestamp exists (just verify it's a string)
            assert isinstance(rows[1][2], str)
        finally:
            logging_config.QUALITY_REPORT_PATH = original_path