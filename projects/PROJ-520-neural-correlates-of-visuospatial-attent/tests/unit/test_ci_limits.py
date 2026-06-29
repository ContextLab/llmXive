"""
Unit tests for CI environment limits detection.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We import the function, not the module, to avoid side effects during import
# if the module has top-level execution (it doesn't, but good practice)
from ci_limits import get_cpu_count, get_memory_limit_gb, get_environment_report

class TestGetCpuCount:
    def test_default_when_no_env(self):
        """Test fallback to multiprocessing.cpu_count when no env vars set."""
        with patch('ci_limits.os.getenv', return_value=None):
            with patch('ci_limits.multiprocessing.cpu_count', return_value=4):
                count = get_cpu_count()
                assert count == 4

    def test_uses_slurm_env(self):
        """Test detection of SLURM_CPUS_PER_TASK."""
        with patch('ci_limits.os.getenv', side_effect=lambda x, default=None: '8' if x == 'SLURM_CPUS_PER_TASK' else default):
            count = get_cpu_count()
            assert count == 8

    def test_uses_ci_cpu_env(self):
        """Test detection of CI_CPU_LIMIT."""
        with patch('ci_limits.os.getenv', side_effect=lambda x, default=None: '16' if x == 'CI_CPU_LIMIT' else default):
            count = get_cpu_count()
            assert count == 16

    def test_invalid_env_falls_back(self):
        """Test that invalid env value falls back to default."""
        with patch('ci_limits.os.getenv', return_value='invalid'):
            with patch('ci_limits.multiprocessing.cpu_count', return_value=2):
                count = get_cpu_count()
                assert count == 2

class TestGetMemoryLimit:
    def test_default_when_no_env(self):
        """Test fallback to default when no env vars or resource limits."""
        with patch('ci_limits.os.getenv', return_value=None):
            with patch('ci_limits.HAS_RESOURCE', False):
                limit = get_memory_limit_gb()
                # Check against default constant
                from ci_limits import DEFAULT_RAM_LIMIT_GB
                assert limit == DEFAULT_RAM_LIMIT_GB

    def test_uses_ci_ram_env(self):
        """Test detection of CI_RAM_LIMIT_GB."""
        with patch('ci_limits.os.getenv', return_value='8.0'):
            limit = get_memory_limit_gb()
            assert limit == 8.0

    def test_handles_slurm_mb(self):
        """Test detection of SLURM_MEM_PER_NODE (assuming MB heuristic)."""
        with patch('ci_limits.os.getenv', return_value='4096'): # 4096 MB
            limit = get_memory_limit_gb()
            # Heuristic: if > 1000, divide by 1024
            assert abs(limit - 4.0) < 0.1

    def test_uses_resource_limit(self):
        """Test detection via resource module."""
        mock_limit = 2 * 1024 * 1024 * 1024 # 2 GB in bytes
        with patch('ci_limits.os.getenv', return_value=None):
            with patch('ci_limits.HAS_RESOURCE', True):
                with patch('ci_limits.resource.getrlimit', return_value=(mock_limit, mock_limit)):
                    limit = get_memory_limit_gb()
                    assert limit == 2.0

class TestEnvironmentReport:
    def test_report_structure(self):
        """Test that the report contains expected keys."""
        with patch('ci_limits.get_cpu_count', return_value=2):
            with patch('ci_limits.get_memory_limit_gb', return_value=4.0):
                with patch('ci_limits.enforce_limits', return_value={
                    "cpu_limit": 2,
                    "ram_limit_gb": 4.0,
                    "cpu_count_physical": 4,
                    "has_resource_module": True
                }):
                    report = get_environment_report()
                    assert "cpu_limit" in report
                    assert "ram_limit_gb" in report
                    assert "cpu_count_physical" in report
                    assert "has_resource_module" in report
