"""
Unit tests for CI Resource Monitoring (T046).

Tests verify that the resource monitor:
1. Generates a valid JSON report structure.
2. Correctly calculates execution time.
3. Reports memory usage (even if 0 or small).
4. Handles directory creation.
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from monitor.ci_resource_monitor import (
    get_memory_usage_mb,
    generate_report,
    save_report,
    run_monitoring,
    MEMORY_LIMIT_MB
)


class TestResourceMonitor:

    def test_get_memory_usage_mb_returns_number(self):
        """Test that memory usage function returns a non-negative number."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, (int, float))
        assert usage >= 0

    def test_generate_report_structure(self):
        """Test that the generated report has all required keys."""
        report = generate_report(
            start_time=100.0,
            end_time=105.0,
            peak_memory_mb=500.0,
            peak_cpu_percent=10.0,
            task_name="test_task"
        )

        assert "timestamp" in report
        assert "task_name" in report
        assert "execution_time_seconds" in report
        assert "peak_memory_mb" in report
        assert "compliance" in report
        assert "status" in report

        assert report["task_name"] == "test_task"
        assert report["execution_time_seconds"] == 5.0
        assert report["peak_memory_mb"] == 500.0
        assert report["compliance"]["memory"] is True
        assert report["compliance"]["overall"] is True
        assert report["status"] == "PASS"

    def test_generate_report_memory_failure(self):
        """Test report generation when memory limit is exceeded."""
        report = generate_report(
            start_time=100.0,
            end_time=105.0,
            peak_memory_mb=8000.0,  # > 7000 limit
            peak_cpu_percent=10.0,
            task_name="test_task"
        )

        assert report["compliance"]["memory"] is False
        assert report["compliance"]["overall"] is False
        assert report["status"] == "FAIL"

    def test_save_report_creates_file(self):
        """Test that save_report creates the file and writes valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.json")
            report = generate_report(100, 105, 500, 10, "test")

            save_report(report, output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert loaded["task_name"] == "test"
            assert loaded["status"] == "PASS"

    def test_run_monitoring_integration(self):
        """Test the full run_monitoring function end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "report.json")
            log_path = os.path.join(tmpdir, "log.jsonl")

            report = run_monitoring(
                task_name="integration_test",
                output_path=output_path,
                log_path=log_path
            )

            # Check return value
            assert report["task_name"] == "integration_test"
            assert report["status"] in ["PASS", "FAIL"]

            # Check file creation
            assert os.path.exists(output_path)
            assert os.path.exists(log_path)

            # Check log content
            with open(log_path, 'r') as f:
                line = f.readline()
                loaded_log = json.loads(line)
                assert loaded_log["task_name"] == "integration_test"

    def test_memory_limit_constant(self):
        """Verify the memory limit constant is set correctly."""
        assert MEMORY_LIMIT_MB == 7000  # 7GB