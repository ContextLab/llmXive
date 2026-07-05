"""
Integration tests for the structured logging infrastructure.
"""

import pytest
import tempfile
from pathlib import Path

from code.src.utils.logger import AuditLogger, get_error_message


class TestLoggerIntegration:
    """Integration tests for the logging infrastructure."""

    def test_full_log_cycle(self):
        """Test a complete logging cycle with all log levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "integration_test.log"
            logger = AuditLogger("integration_test", log_file)

            # Log various messages
            logger.log_error(1, "Error occurred")
            logger.log_warning(10, "Warning issued")
            logger.log_info("Information logged")
            logger.log_debug("Debug message")
            logger.log_success(1, "Success achieved")

            # Read and verify all logs
            with open(log_file, 'r') as f:
                content = f.read()

            assert "ERR-001" in content
            assert "ERR-010" in content
            assert "Error occurred" in content
            assert "Warning issued" in content
            assert "Information logged" in content
            assert "Debug message" in content
            assert "Success achieved" in content

    def test_error_code_consistency(self):
        """Test that error codes are consistent across multiple log calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "consistency_test.log"
            logger = AuditLogger("consistency_test", log_file)

            # Log the same error code multiple times
            for _ in range(5):
                logger.log_error(301, "Resource limit exceeded")

            # Read and verify
            with open(log_file, 'r') as f:
                content = f.read()

            # Count occurrences of ERR-301
            count = content.count("ERR-301")
            assert count == 5

    def test_nested_logging(self):
        """Test logging from multiple logger instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file1 = Path(tmpdir) / "logger1.log"
            log_file2 = Path(tmpdir) / "logger2.log"

            logger1 = AuditLogger("module1", log_file1)
            logger2 = AuditLogger("module2", log_file2)

            logger1.log_error(1, "Module 1 error")
            logger2.log_error(2, "Module 2 error")

            with open(log_file1, 'r') as f:
                content1 = f.read()
            with open(log_file2, 'r') as f:
                content2 = f.read()

            assert "module1" in content1
            assert "ERR-001" in content1
            assert "module2" in content2
            assert "ERR-002" in content2
