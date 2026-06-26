"""Unit tests for memory monitoring functionality.

Tests for memory_monitor.py to validate 7GB memory limit enforcement (SC-002).
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import csv

# Import the module under test
from memory_monitor import (
    check_memory_limit,
    validate_memory_within_limit,
    memory_monitor,
    setup_memory_monitoring,
    get_total_memory_mb,
    MEMORY_LIMIT_GB,
    MEMORY_LIMIT_BYTES,
    MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD
)


class TestMemoryLimitConstants:
    """Test memory limit constants are correctly defined."""

    def test_memory_limit_is_7_gb(self):
        """Verify memory limit is set to 7GB."""
        assert MEMORY_LIMIT_GB == 7.0

    def test_memory_limit_bytes_conversion(self):
        """Verify bytes conversion is correct."""
        assert MEMORY_LIMIT_BYTES == 7.0 * (1024 ** 3)

    def test_warning_threshold_is_90_percent(self):
        """Verify warning threshold is 90%."""
        assert MEMORY_WARNING_THRESHOLD == 0.9

    def test_critical_threshold_is_95_percent(self):
        """Verify critical threshold is 95%."""
        assert MEMORY_CRITICAL_THRESHOLD == 0.95


class TestCheckMemoryLimit:
    """Test check_memory_limit function."""

    def test_check_memory_limit_returns_dict(self):
        """Verify check_memory_limit returns required dictionary keys."""
        result = check_memory_limit()

        assert isinstance(result, dict)
        assert 'current_mb' in result
        assert 'limit_mb' in result
        assert 'usage_percent' in result
        assert 'status' in result
        assert 'timestamp' in result

    def test_check_memory_limit_limit_mb_is_correct(self):
        """Verify limit_mb is the correct value in MB."""
        result = check_memory_limit()

        expected_limit_mb = 7.0 * 1024  # 7GB in MB
        assert result['limit_mb'] == expected_limit_mb

    def test_check_memory_limit_status_is_valid(self):
        """Verify status is one of the valid values."""
        result = check_memory_limit()

        assert result['status'] in ['ok', 'warning', 'critical']


class TestValidateMemoryWithinLimit:
    """Test validate_memory_within_limit function."""

    @patch('memory_monitor.get_total_memory_mb')
    def test_validate_returns_true_when_within_limit(self, mock_get_memory):
        """Verify returns True when memory is within limit."""
        # Mock memory usage at 5GB (within 7GB limit)
        mock_get_memory.return_value = 5 * 1024

        result = validate_memory_within_limit(raise_on_exceed=False)

        assert result is True

    @patch('memory_monitor.get_total_memory_mb')
    def test_validate_returns_false_when_critical(self, mock_get_memory):
        """Verify returns False when memory is at critical level."""
        # Mock memory usage at 6.8GB (97% of 7GB limit - critical)
        mock_get_memory.return_value = 6.8 * 1024

        result = validate_memory_within_limit(raise_on_exceed=False)

        assert result is False

    @patch('memory_monitor.get_total_memory_mb')
    def test_validate_raises_memory_error_when_exceeded(self, mock_get_memory):
        """Verify raises MemoryError when memory exceeds limit."""
        # Mock memory usage at 6.8GB (critical level)
        mock_get_memory.return_value = 6.8 * 1024

        with pytest.raises(MemoryError):
            validate_memory_within_limit(raise_on_exceed=True)


class TestMemoryMonitorContextManager:
    """Test memory_monitor context manager."""

    def test_memory_monitor_yields_dict(self):
        """Verify memory_monitor yields a dictionary with expected keys."""
        with memory_monitor("test_operation") as result:
            assert isinstance(result, dict)
            assert 'operation' in result
            assert 'start_mb' in result
            assert 'peak_mb' in result
            assert 'samples' in result

    def test_memory_monitor_tracks_samples(self):
        """Verify memory_monitor collects memory samples."""
        with memory_monitor("test_operation") as result:
            assert len(result['samples']) >= 1
            assert 'time' in result['samples'][0]
            assert 'memory_mb' in result['samples'][0]

    def test_memory_monitor_logs_to_file(self):
        """Verify memory_monitor writes to log file when path provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "memory_test.csv"

            with memory_monitor("test_operation", log_path=log_path) as result:
                pass

            # Verify log file was created
            assert log_path.exists()

            # Verify log file has correct format
            with open(log_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)

                # First row should be header
                assert len(rows) >= 1
                assert 'operation' in rows[0]

    def test_memory_monitor_operation_name_in_result(self):
        """Verify operation name is correctly recorded."""
        with memory_monitor("custom_operation_name") as result:
            assert result['operation'] == "custom_operation_name"


class TestSetupMemoryMonitoring:
    """Test setup_memory_monitoring function."""

    def test_setup_memory_monitoring_creates_directory(self):
        """Verify setup_memory_monitoring creates the log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "custom_logs"

            result_path = setup_memory_monitoring(log_dir=log_dir)

            assert log_dir.exists()
            assert result_path.parent == log_dir

    def test_setup_memory_monitoring_returns_path(self):
        """Verify setup_memory_monitoring returns a Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "custom_logs"

            result_path = setup_memory_monitoring(log_dir=log_dir)

            assert isinstance(result_path, Path)

    def test_setup_memory_monitoring_default_directory(self):
        """Verify setup_memory_monitoring uses default directory when not specified."""
        result_path = setup_memory_monitoring()

        # Default should be data/memory_logs/
        assert 'memory_logs' in str(result_path)


class TestGetTotalMemoryMb:
    """Test get_total_memory_mb function."""

    def test_get_total_memory_mb_returns_float(self):
        """Verify get_total_memory_mb returns a numeric value."""
        result = get_total_memory_mb()

        assert isinstance(result, (int, float))
        assert result >= 0

    def test_get_total_memory_mb_is_non_negative(self):
        """Verify memory usage is never negative."""
        result = get_total_memory_mb()

        assert result >= 0


class TestMemoryMonitorIntegration:
    """Integration tests for memory monitoring."""

    def test_memory_monitor_handles_exception_in_block(self):
        """Verify memory_monitor properly cleans up on exception."""
        with pytest.raises(ValueError):
            with memory_monitor("test_with_exception") as result:
                raise ValueError("Test exception")

        # Should not leak resources or hang

    def test_memory_monitor_multiple_operations(self):
        """Verify multiple memory monitor operations work correctly."""
        results = []

        for i in range(3):
            with memory_monitor(f"operation_{i}") as result:
                results.append(result)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result['operation'] == f"operation_{i}"
