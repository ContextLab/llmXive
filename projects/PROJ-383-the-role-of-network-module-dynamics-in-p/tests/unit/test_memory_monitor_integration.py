"""
Unit tests for memory monitoring integration in the ingestion pipeline.
Verifies that the memory guard correctly enforces the 7GB limit.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from utils.memory_monitor import (
    get_current_rss_bytes,
    get_peak_rss_bytes,
    reset_peak_rss,
    check_memory_limit,
    enforce_memory_limit,
    memory_guard,
    MEMORY_LIMIT_BYTES,
)

class TestMemoryMonitorIntegration:
    def test_reset_peak_rss_initializes(self):
        """Test that resetting peak RSS sets it to current value."""
        reset_peak_rss()
        current = get_current_rss_bytes()
        peak = get_peak_rss_bytes()
        # After reset, peak should be at least current
        assert peak >= current

    def test_memory_guard_within_limit(self):
        """Test that memory_guard completes successfully when under limit."""
        # Mock current usage to be well under 7GB
        mock_usage = 1 * 1024**3  # 1 GB
        with patch('psutil.Process') as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value.rss = mock_usage
            MockProcess.return_value = mock_instance

            # Reset to ensure clean state
            reset_peak_rss()

            # This should not raise
            with memory_guard(limit_bytes=MEMORY_LIMIT_BYTES):
                pass

        # Verify no exception was raised
        assert True

    def test_memory_guard_exceeds_limit(self):
        """Test that memory_guard raises MemoryError when over limit."""
        # Mock current usage to be over 7GB
        mock_usage = 8 * 1024**3  # 8 GB
        with patch('psutil.Process') as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value.rss = mock_usage
            MockProcess.return_value = mock_instance

            reset_peak_rss()

            with pytest.raises(MemoryError):
                with memory_guard(limit_bytes=MEMORY_LIMIT_BYTES):
                    pass

    def test_enforce_memory_limit_success(self):
        """Test enforce_memory_limit when under limit."""
        mock_usage = 1 * 1024**3
        with patch('psutil.Process') as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value.rss = mock_usage
            MockProcess.return_value = mock_instance

            # Should not raise
            enforce_memory_limit(limit_bytes=MEMORY_LIMIT_BYTES)

    def test_enforce_memory_limit_failure(self):
        """Test enforce_memory_limit raises when over limit."""
        mock_usage = 8 * 1024**3
        with patch('psutil.Process') as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value.rss = mock_usage
            MockProcess.return_value = mock_instance

            with pytest.raises(MemoryError):
                enforce_memory_limit(limit_bytes=MEMORY_LIMIT_BYTES)

    def test_check_memory_limit_boolean(self):
        """Test check_memory_limit returns correct boolean."""
        # Test under limit
        with patch('psutil.Process') as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value.rss = 1 * 1024**3
            MockProcess.return_value = mock_instance
            assert check_memory_limit() is True

        # Test over limit
        with patch('psutil.Process') as MockProcess:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value.rss = 8 * 1024**3
            MockProcess.return_value = mock_instance
            assert check_memory_limit() is False

    def test_memory_report_structure(self):
        """Test that memory report contains expected keys."""
        from utils.memory_monitor import get_memory_usage_report

        report = get_memory_usage_report()

        required_keys = [
            "current_rss_bytes",
            "current_rss_gb",
            "peak_rss_bytes",
            "peak_rss_gb",
            "limit_bytes",
            "limit_gb",
            "within_limit",
        ]

        for key in required_keys:
            assert key in report, f"Missing key in report: {key}"

        # Verify types
        assert isinstance(report["current_rss_bytes"], int)
        assert isinstance(report["within_limit"], bool)
        assert report["limit_bytes"] == MEMORY_LIMIT_BYTES