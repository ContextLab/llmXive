"""
Unit tests for resource monitoring utilities (code/utils/monitor.py).
"""
import time
import sys
import os
import pytest

# Ensure code/ is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from code.utils.monitor import (
    get_ram_usage,
    get_cpu_utilization,
    get_peak_memory_mb,
    get_elapsed_time,
    format_bytes,
    format_duration,
    ResourceMonitor,
    validate_resource_limits
)


def test_get_ram_usage():
    """Test that get_ram_usage returns a positive float."""
    ram = get_ram_usage()
    assert isinstance(ram, float), "get_ram_usage should return a float"
    assert ram > 0, "get_ram_usage should return a value greater than 0"


def test_get_cpu_utilization():
    """Test that get_cpu_utilization returns a non-negative float."""
    cpu = get_cpu_utilization()
    assert isinstance(cpu, float), "get_cpu_utilization should return a float"
    assert cpu >= 0, "get_cpu_utilization should return a non-negative value"
    # Allow for very low CPU usage in idle tests, but not negative
    assert cpu < 1000, "CPU usage should be reasonable (less than 1000%)"


def test_get_peak_memory_mb():
    """Test that get_peak_memory_mb returns a positive float."""
    peak = get_peak_memory_mb()
    assert isinstance(peak, float), "get_peak_memory_mb should return a float"
    assert peak > 0, "get_peak_memory_mb should return a value greater than 0"


def test_get_elapsed_time():
    """Test elapsed time calculation."""
    start = time.time()
    time.sleep(0.1)
    elapsed = get_elapsed_time(start)
    assert elapsed >= 0.1, "Elapsed time should be at least 0.1s"


def test_format_bytes():
    """Test byte formatting."""
    assert "B" in format_bytes(100)
    assert "KB" in format_bytes(1024)
    assert "MB" in format_bytes(1024 * 1024)
    assert "GB" in format_bytes(1024 * 1024 * 1024)


def test_format_duration():
    """Test duration formatting."""
    assert "s" in format_duration(5)
    assert "m" in format_duration(65)
    assert "h" in format_duration(3665)


def test_resource_monitor_lifecycle():
    """Test starting and stopping the ResourceMonitor."""
    monitor = ResourceMonitor()
    monitor.start()
    time.sleep(0.2)
    monitor.stop()

    summary = monitor.get_summary()
    assert summary["sample_count"] > 0, "Monitor should have collected samples"
    assert summary["peak_memory_mb"] > 0, "Peak memory should be recorded"


def test_validate_resource_limits_pass():
    """Test validation when limits are respected."""
    result = validate_resource_limits(peak_ram_gb=4.0, current_time_h=1.0)
    assert result["status"] == "pass"
    assert len(result["reasons"]) == 0


def test_validate_resource_limits_fail_ram():
    """Test validation when RAM limit is exceeded."""
    result = validate_resource_limits(peak_ram_gb=8.0, max_ram_gb=7.0)
    assert result["status"] == "fail"
    assert any("Peak RAM" in r for r in result["reasons"])


def test_validate_resource_limits_fail_time():
    """Test validation when time limit is exceeded."""
    result = validate_resource_limits(peak_ram_gb=4.0, max_time_h=1.0, current_time_h=2.0)
    assert result["status"] == "fail"
    assert any("Elapsed time" in r for r in result["reasons"])
