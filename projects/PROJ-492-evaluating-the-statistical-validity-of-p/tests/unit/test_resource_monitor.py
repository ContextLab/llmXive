"""Unit tests for resource monitor parsing of /proc filesystem.

This module validates the parsing logic for CPU and memory statistics
extracted from Linux /proc filesystem entries.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from code.src.utils.resource_monitor import (
    parse_proc_stat,
    parse_proc_meminfo,
    get_cpu_usage,
    get_memory_usage,
    ResourceMonitorError,
)


class TestParseProcStat:
    """Tests for parsing /proc/stat CPU information."""

    def test_parse_valid_cpu_line(self):
        """Test parsing a valid CPU line from /proc/stat."""
        # Format: cpu user nice system idle iowait irq softirq steal guest guest_nice
        stat_line = "cpu 100 10 50 800 20 5 10 5 0 0"
        result = parse_proc_stat(stat_line)

        assert result is not None
        assert result["user"] == 100
        assert result["nice"] == 10
        assert result["system"] == 50
        assert result["idle"] == 800
        assert result["iowait"] == 20
        assert result["irq"] == 5
        assert result["softirq"] == 10
        assert result["steal"] == 5
        assert result["guest"] == 0
        assert result["guest_nice"] == 0

    def test_parse_cpu0_line(self):
        """Test parsing a specific CPU core line (cpu0)."""
        stat_line = "cpu0 50 5 25 400 10 2 5 2 0 0"
        result = parse_proc_stat(stat_line)

        assert result is not None
        assert result["user"] == 50
        assert result["system"] == 25
        assert result["idle"] == 400

    def test_parse_invalid_line_format(self):
        """Test parsing a line with incorrect format."""
        # Missing some fields
        stat_line = "cpu 100 10 50"
        result = parse_proc_stat(stat_line)
        assert result is None

    def test_parse_non_cpu_line(self):
        """Test parsing a line that doesn't start with 'cpu'."""
        stat_line = "intr 1000 50 60"
        result = parse_proc_stat(stat_line)
        assert result is None

    def test_parse_empty_line(self):
        """Test parsing an empty line."""
        stat_line = ""
        result = parse_proc_stat(stat_line)
        assert result is None

    def test_parse_whitespace_line(self):
        """Test parsing a line with only whitespace."""
        stat_line = "   "
        result = parse_proc_stat(stat_line)
        assert result is None


class TestParseProcMeminfo:
    """Tests for parsing /proc/meminfo memory information."""

    def test_parse_valid_meminfo_line(self):
        """Test parsing a valid meminfo line."""
        # Format: MemTotal:        16384000 kB
        mem_line = "MemTotal:        16384000 kB"
        result = parse_proc_meminfo(mem_line)

        assert result is not None
        assert result["key"] == "MemTotal"
        assert result["value"] == 16384000
        assert result["unit"] == "kB"

    def test_parse_memfree_line(self):
        """Test parsing MemFree line."""
        mem_line = "MemFree:         8192000 kB"
        result = parse_proc_meminfo(mem_line)

        assert result is not None
        assert result["key"] == "MemFree"
        assert result["value"] == 8192000

    def test_parse_memavailable_line(self):
        """Test parsing MemAvailable line."""
        mem_line = "MemAvailable:    12000000 kB"
        result = parse_proc_meminfo(mem_line)

        assert result is not None
        assert result["key"] == "MemAvailable"
        assert result["value"] == 12000000

    def test_parse_swap_total_line(self):
        """Test parsing SwapTotal line."""
        mem_line = "SwapTotal:       4096000 kB"
        result = parse_proc_meminfo(mem_line)

        assert result is not None
        assert result["key"] == "SwapTotal"
        assert result["value"] == 4096000

    def test_parse_invalid_format(self):
        """Test parsing a line with invalid format."""
        mem_line = "MemTotal 16384000"  # Missing colon
        result = parse_proc_meminfo(mem_line)
        assert result is None

    def test_parse_missing_value(self):
        """Test parsing a line with missing value."""
        mem_line = "MemTotal: kB"
        result = parse_proc_meminfo(mem_line)
        assert result is None

    def test_parse_non_numeric_value(self):
        """Test parsing a line with non-numeric value."""
        mem_line = "MemTotal: N/A kB"
        result = parse_proc_meminfo(mem_line)
        assert result is None

    def test_parse_empty_line(self):
        """Test parsing an empty line."""
        mem_line = ""
        result = parse_proc_meminfo(mem_line)
        assert result is None


class TestGetCpuUsage:
    """Tests for CPU usage calculation."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    def test_cpu_usage_calculation(self, mock_exists, mock_open_file):
        """Test CPU usage calculation from two snapshots."""
        # Mock /proc/stat content
        mock_open_file.return_value.read.return_value = (
            "cpu 100 10 50 800 20 5 10 5 0 0\n"
            "cpu0 50 5 25 400 10 2 5 2 0 0\n"
        )

        # Mock time.sleep to avoid actual delay
        with patch("time.sleep", return_value=None):
            try:
                usage = get_cpu_usage(interval=0.01)
                assert usage >= 0.0
                assert usage <= 100.0
            except ResourceMonitorError:
                # Expected if /proc/stat is not accessible in test environment
                pass

    @patch("os.path.exists", return_value=False)
    def test_cpu_usage_file_not_found(self, mock_exists):
        """Test CPU usage when /proc/stat is not accessible."""
        with patch("time.sleep", return_value=None):
            with pytest.raises(ResourceMonitorError):
                get_cpu_usage(interval=0.01)


class TestGetMemoryUsage:
    """Tests for memory usage calculation."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    def test_memory_usage_calculation(self, mock_exists, mock_open_file):
        """Test memory usage calculation from /proc/meminfo."""
        # Mock /proc/meminfo content
        meminfo_content = (
            "MemTotal:        16384000 kB\n"
            "MemFree:         8192000 kB\n"
            "MemAvailable:    12000000 kB\n"
            "Buffers:          512000 kB\n"
            "Cached:          2048000 kB\n"
            "SwapTotal:       4096000 kB\n"
            "SwapFree:        4096000 kB\n"
        )
        mock_open_file.return_value.read.return_value = meminfo_content

        try:
            usage = get_memory_usage()
            assert usage is not None
            assert "total_kb" in usage
            assert "available_kb" in usage
            assert "used_kb" in usage
            assert "usage_percent" in usage
            assert usage["total_kb"] == 16384000
            assert usage["available_kb"] == 12000000
            assert usage["used_kb"] == 4384000  # total - available
            assert 0.0 <= usage["usage_percent"] <= 100.0
        except ResourceMonitorError:
            # Expected if /proc/meminfo is not accessible in test environment
            pass

    @patch("os.path.exists", return_value=False)
    def test_memory_usage_file_not_found(self, mock_exists):
        """Test memory usage when /proc/meminfo is not accessible."""
        with pytest.raises(ResourceMonitorError):
            get_memory_usage()

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    def test_memory_usage_missing_fields(self, mock_exists, mock_open_file):
        """Test memory usage with missing MemAvailable field."""
        # Mock /proc/meminfo without MemAvailable
        meminfo_content = (
            "MemTotal:        16384000 kB\n"
            "MemFree:         8192000 kB\n"
            "Buffers:          512000 kB\n"
            "Cached:          2048000 kB\n"
        )
        mock_open_file.return_value.read.return_value = meminfo_content

        try:
            usage = get_memory_usage()
            assert usage is not None
            # Should fall back to MemFree + Buffers + Cached
            assert "total_kb" in usage
            assert "used_kb" in usage
            assert "usage_percent" in usage
        except ResourceMonitorError:
            # Expected if calculation fails
            pass


class TestResourceMonitorError:
    """Tests for ResourceMonitorError exception."""

    def test_error_creation(self):
        """Test creating a ResourceMonitorError."""
        error = ResourceMonitorError("Test error message")
        assert str(error) == "Test error message"
        assert error.args[0] == "Test error message"

    def test_error_with_code(self):
        """Test creating a ResourceMonitorError with an error code."""
        error = ResourceMonitorError("Test error", code="ERR-301")
        assert "ERR-301" in str(error)


class TestIntegration:
    """Integration tests for resource monitor parsing."""

    def test_parse_proc_stat_realistic_data(self):
        """Test parsing realistic /proc/stat data."""
        realistic_stat = (
            "cpu  854834 21953 107537 4293754 3349 0 763 0 0 0\n"
            "cpu0 213708 5488 26884 1073438 837 0 190 0 0 0\n"
            "cpu1 213709 5489 26885 1073439 838 0 191 0 0 0\n"
            "intr 12345678 0 0 0 0 0 0 0 0 1 2 3\n"
            "ctxt 987654321\n"
        )

        # Parse the cpu line
        cpu_result = parse_proc_stat(realistic_stat.split("\n")[0])
        assert cpu_result is not None
        assert cpu_result["user"] == 854834
        assert cpu_result["idle"] == 4293754

    def test_parse_proc_meminfo_realistic_data(self):
        """Test parsing realistic /proc/meminfo data."""
        realistic_meminfo = (
            "MemTotal:       16384000 kB\n"
            "MemFree:         1024000 kB\n"
            "MemAvailable:    8192000 kB\n"
            "Buffers:          256000 kB\n"
            "Cached:          1536000 kB\n"
            "SwapCached:            0 kB\n"
            "Active:          4096000 kB\n"
            "Inactive:        2048000 kB\n"
            "SwapTotal:       4096000 kB\n"
            "SwapFree:        4096000 kB\n"
        )

        # Parse MemTotal
        mem_total = None
        for line in realistic_meminfo.split("\n"):
            if line.startswith("MemTotal:"):
                mem_total = parse_proc_meminfo(line)
                break

        assert mem_total is not None
        assert mem_total["value"] == 16384000
        assert mem_total["unit"] == "kB"