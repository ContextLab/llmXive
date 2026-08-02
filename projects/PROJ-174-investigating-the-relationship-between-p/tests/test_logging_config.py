"""
Tests for the logging infrastructure (T005).
Verifies file creation and column presence.
"""
import os
import csv
import pytest
from pathlib import Path
import sys

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from logging_config import initialize_quality_report, get_logger, LOGS_DIR, RESULTS_DIR

class TestLoggingInfrastructure:
    
    def test_preprocess_log_exists(self):
        """Verify that preprocess.log is created."""
        log_path = LOGS_DIR / "preprocess.log"
        
        # Trigger logger creation
        logger = get_logger()
        logger.info("Test log entry")
        
        assert log_path.exists(), f"Log file {log_path} was not created"
        
        # Verify content
        with open(log_path, 'r') as f:
            content = f.read()
            assert "Test log entry" in content, "Log entry not found in file"

    def test_quality_report_initialization(self):
        """Verify quality_report.csv is created with correct headers."""
        report_path = RESULTS_DIR / "quality_report.csv"
        
        # Remove if exists to test fresh initialization
        if report_path.exists():
            report_path.unlink()
        
        # Initialize
        result_path = initialize_quality_report()
        
        assert result_path.exists(), "Quality report file was not created"
        
        # Verify headers
        with open(result_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ['exclusion_type', 'count'], f"Headers mismatch: {headers}"
            
            # Verify no extra rows initially
            remaining = list(reader)
            assert len(remaining) == 0, "Quality report should be empty except headers"

    def test_quality_report_append(self):
        """Verify we can append to the quality report."""
        report_path = RESULTS_DIR / "quality_report.csv"
        
        # Ensure initialized
        initialize_quality_report()
        
        # Append a row manually to simulate pipeline usage
        with open(report_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['blink_exclusion', 15])
        
        # Verify
        with open(report_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 2, "Expected 2 rows (header + 1 data)"
            assert rows[1] == ['blink_exclusion', '15'], "Data row mismatch"
            
    def test_logging_functionality(self):
        """Verify logger writes to the correct file."""
        logger = get_logger("test_logger")
        test_msg = "Verification test message"
        logger.info(test_msg)
        
        log_path = LOGS_DIR / "preprocess.log"
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            content = f.read()
            assert test_msg in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])