"""
Unit tests for T009: Environment configuration management (memory and runtime).
"""
import time
import logging
from unittest.mock import patch, MagicMock

import pytest

from config import check_memory_limit, set_runtime_cap, ENV_CONSTRAINTS
from utils.io import monitor_runtime_and_warn


class TestCheckMemoryLimit:
    def test_check_memory_limit_returns_tuple(self):
        """Verify check_memory_limit returns a tuple (bool, float)."""
        is_sufficient, available_gb = check_memory_limit()
        assert isinstance(is_sufficient, bool)
        assert isinstance(available_gb, float)
        assert available_gb > 0.0

    def test_check_memory_limit_custom_limit(self):
        """Verify check_memory_limit respects custom limit."""
        # Should be sufficient if limit is very low (e.g., 0.001 GB)
        is_sufficient, _ = check_memory_limit(limit_gb=0.001)
        assert is_sufficient is True

        # Mock a scenario where memory is limited
        with patch("resource.getrlimit", return_value=(1024, 0)): # 1KB limit -> very small
            # 1KB is 1024 bytes. 1024 / (1024^3) is negligible.
            is_sufficient, available_gb = check_memory_limit(limit_gb=1.0)
            assert is_sufficient is False
            assert available_gb < 1.0


class TestMonitorRuntime:
    def test_monitor_runtime_no_warning(self, caplog):
        """Verify no warning is logged when under threshold."""
        start_time = time.time() - 10  # 10 seconds ago
        with caplog.at_level(logging.WARNING):
            result = monitor_runtime_and_warn(start_time, limit_hours=1.0, warning_threshold=0.8)
            assert result is False
            assert "RUNTIME WARNING" not in caplog.text

    def test_monitor_runtime_triggers_warning(self, caplog):
        """Verify warning is logged when over threshold."""
        # Simulate 90% of 1 hour limit (54 minutes = 3240 seconds)
        start_time = time.time() - 3240
        with caplog.at_level(logging.WARNING):
            result = monitor_runtime_and_warn(start_time, limit_hours=1.0, warning_threshold=0.8)
            assert result is True
            assert "RUNTIME WARNING" in caplog.text
            assert "approaches the configured limit" in caplog.text

    def test_monitor_runtime_custom_threshold(self, caplog):
        """Verify warning triggers at custom threshold."""
        # 50% of 1 hour limit
        start_time = time.time() - 1800
        with caplog.at_level(logging.WARNING):
            result = monitor_runtime_and_warn(start_time, limit_hours=1.0, warning_threshold=0.5)
            assert result is True
            assert "RUNTIME WARNING" in caplog.text
            assert "RUNTIME WARNING" in caplog.text