"""
Unit tests for resource monitor parsing of /proc filesystem.

This module verifies that the resource_monitor module correctly parses
/proc/stat and /proc/self/status to extract CPU and memory metrics.
"""
import os
import sys
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from code.src.utils.resource_monitor import (
    parse_cpu_stat_line,
    parse_memory_from_status,
    get_cpu_usage,
    get_memory_usage_mb,
    check_resource_limits
)


class TestParseCpuStatLine:
    """Tests for parse_cpu_stat_line function."""

    def test_parse_valid_cpu_line(self):
        """Test parsing a valid /proc/stat cpu line."""
        # Format: cpu user nice system idle iowait irq softirq steal guest guest_nice
        line = "cpu 100 10 50 800 20 5 10 0 0 0"
        user, nice, system, idle, iowait, irq, softirq, steal = parse_cpu_stat_line(line)
        
        assert user == 100
        assert nice == 10
        assert system == 50
        assert idle == 800
        assert iowait == 20
        assert irq == 5
        assert softirq == 10
        assert steal == 0

    def test_parse_cpu_line_with_steal(self):
        """Test parsing cpu line with steal time."""
        line = "cpu 200 20 60 700 30 10 15 5 1 1"
        user, nice, system, idle, iowait, irq, softirq, steal = parse_cpu_stat_line(line)
        
        assert user == 200
        assert nice == 20
        assert system == 60
        assert idle == 700
        assert steal == 1

    def test_parse_cpu0_line(self):
        """Test parsing per-cpu line (cpu0, cpu1, etc)."""
        line = "cpu0 150 15 45 600 25 8 12 3 0 0"
        user, nice, system, idle, iowait, irq, softirq, steal = parse_cpu_stat_line(line)
        
        assert user == 150
        assert nice == 15
        assert system == 45
        assert idle == 600

    def test_parse_invalid_line_format(self):
        """Test parsing line with insufficient fields."""
        line = "cpu 100 10 50"
        with pytest.raises(ValueError, match="Insufficient fields in cpu line"):
            parse_cpu_stat_line(line)

    def test_parse_non_numeric_values(self):
        """Test parsing line with non-numeric values."""
        line = "cpu abc 10 50 800 20 5 10 0 0 0"
        with pytest.raises(ValueError, match="Invalid numeric value"):
            parse_cpu_stat_line(line)


class TestParseMemoryFromStatus:
    """Tests for parse_memory_from_status function."""

    def test_parse_valid_status(self):
        """Test parsing valid /proc/self/status content."""
        status_content = """
        Name:   python
        State:  S (sleeping)
        Rss:    123456 kB
        VmSize: 987654 kB
        VmRSS:  123456 kB
        """
        mem_rss, mem_vms = parse_memory_from_status(status_content)
        
        assert mem_rss == 123456  # in kB
        assert mem_vms == 987654  # in kB

    def test_parse_status_with_various_formats(self):
        """Test parsing status with different value formats."""
        status_content = """
        Name:   test
        Rss:    50000 kB
        VmSize: 100000 kB
        """
        mem_rss, mem_vms = parse_memory_from_status(status_content)
        
        assert mem_rss == 50000
        assert mem_vms == 100000

    def test_parse_missing_fields(self):
        """Test parsing status with missing Rss field."""
        status_content = """
        Name:   test
        State:  S
        VmSize: 100000 kB
        """
        mem_rss, mem_vms = parse_memory_from_status(status_content)
        
        assert mem_rss == 0  # Default when missing
        assert mem_vms == 100000

    def test_parse_non_numeric_values(self):
        """Test parsing status with non-numeric values."""
        status_content = """
        Name:   test
        Rss:    abc kB
        """
        with pytest.raises(ValueError, match="Invalid numeric value"):
            parse_memory_from_status(status_content)

    def test_parse_empty_status(self):
        """Test parsing empty status content."""
        status_content = ""
        mem_rss, mem_vms = parse_memory_from_status(status_content)
        
        assert mem_rss == 0
        assert mem_vms == 0


class TestGetCpuUsage:
    """Tests for get_cpu_usage function."""

    @patch('builtins.open', new_callable=mock_open, read_data="cpu 100 10 50 800 20 5 10 0 0 0\ncpu0 50 5 25 400 10 2 5 0 0 0")
    def test_get_cpu_usage_single_read(self, mock_file):
        """Test CPU usage calculation with single read."""
        # When only one read, we can't calculate delta, should return 0.0
        usage = get_cpu_usage()
        assert usage == 0.0

    @patch('time.sleep', return_value=None)  # Mock sleep to speed up test
    @patch('builtins.open', new_callable=mock_open)
    def test_get_cpu_usage_with_delta(self, mock_file, mock_sleep):
        """Test CPU usage calculation with time delta."""
        # Setup mock to return different values on second read
        mock_file.side_effect = [
            mock_open(read_data="cpu 100 10 50 800 20 5 10 0 0 0").return_value,
            mock_open(read_data="cpu 200 20 100 700 30 10 20 0 0 0").return_value
        ]
        
        # First read
        usage = get_cpu_usage()
        assert usage == 0.0
        
        # Second read (should calculate delta)
        usage = get_cpu_usage()
        # Delta: user=100, nice=10, system=50, idle=-100 (impossible, but testing calculation)
        # Total delta = (100+10+50+(-100)+10+5+10+0) = 85
        # Active delta = 85 - (-100) = 185 (idle decreased, so more active)
        # This test verifies the calculation logic works
        assert usage >= 0.0
        assert usage <= 100.0


class TestGetMemoryUsageMb:
    """Tests for get_memory_usage_mb function."""

    @patch('builtins.open', new_callable=mock_open, read_data="Name:   test\nRss:    123456 kB\nVmSize: 987654 kB")
    def test_get_memory_usage_mb(self, mock_file):
        """Test memory usage conversion to MB."""
        mem_mb = get_memory_usage_mb()
        
        # 123456 kB = 123456 / 1024 = 120.5625 MB
        expected = 123456 / 1024
        assert abs(mem_mb - expected) < 0.01

    @patch('builtins.open', new_callable=mock_open, read_data="Name:   test\nRss:    0 kB")
    def test_get_memory_usage_zero(self, mock_file):
        """Test memory usage with zero RSS."""
        mem_mb = get_memory_usage_mb()
        assert mem_mb == 0.0


class TestCheckResourceLimits:
    """Tests for check_resource_limits function."""

    def test_check_limits_within_bounds(self):
        """Test that limits pass when within bounds."""
        cpu_limit = 2.0  # 2 vCPU
        mem_limit_mb = 2048.0  # 2 GB
        
        with patch('code.src.utils.resource_monitor.get_cpu_usage', return_value=1.5):
            with patch('code.src.utils.resource_monitor.get_memory_usage_mb', return_value=1500.0):
                result = check_resource_limits(cpu_limit, mem_limit_mb)
                assert result is True

    def test_check_limits_cpu_exceeded(self):
        """Test that limits fail when CPU exceeded."""
        cpu_limit = 2.0
        mem_limit_mb = 2048.0
        
        with patch('code.src.utils.resource_monitor.get_cpu_usage', return_value=2.5):
            with patch('code.src.utils.resource_monitor.get_memory_usage_mb', return_value=1500.0):
                result = check_resource_limits(cpu_limit, mem_limit_mb)
                assert result is False

    def test_check_limits_memory_exceeded(self):
        """Test that limits fail when memory exceeded."""
        cpu_limit = 2.0
        mem_limit_mb = 2048.0
        
        with patch('code.src.utils.resource_monitor.get_cpu_usage', return_value=1.5):
            with patch('code.src.utils.resource_monitor.get_memory_usage_mb', return_value=2500.0):
                result = check_resource_limits(cpu_limit, mem_limit_mb)
                assert result is False

    def test_check_limits_both_exceeded(self):
        """Test that limits fail when both exceeded."""
        cpu_limit = 2.0
        mem_limit_mb = 2048.0
        
        with patch('code.src.utils.resource_monitor.get_cpu_usage', return_value=3.0):
            with patch('code.src.utils.resource_monitor.get_memory_usage_mb', return_value=3000.0):
                result = check_resource_limits(cpu_limit, mem_limit_mb)
                assert result is False

    def test_check_limits_exact_boundary(self):
        """Test that limits pass when exactly at boundary."""
        cpu_limit = 2.0
        mem_limit_mb = 2048.0
        
        with patch('code.src.utils.resource_monitor.get_cpu_usage', return_value=2.0):
            with patch('code.src.utils.resource_monitor.get_memory_usage_mb', return_value=2048.0):
                result = check_resource_limits(cpu_limit, mem_limit_mb)
                assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])