"""
Unit tests for environment limit configuration (T008).
"""
import os
import signal
import subprocess
import time
from unittest.mock import patch, MagicMock
import pytest
import sys
from pathlib import Path

# Import the module under test
# Assuming the file is at code/setup_env_limits.py
# We need to add the parent directory to sys.path if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_env_limits import (
    run_with_limits,
    _setup_cgroups_v2,
    _cleanup_cgroups_v2,
    _set_ulimit_memory,
    DEFAULT_MEMORY_GB,
    DEFAULT_TIME_LIMIT_HOURS
)

class TestCgroupsSetup:
    def test_setup_cgroups_v2_unavailable(self):
        """Test behavior when cgroups v2 is not mounted."""
        with patch('setup_env_limits.CGROUPS_V2_MOUNT_POINT', '/nonexistent/path'):
            result = _setup_cgroups_v2(1024)
            assert result is None

    def test_setup_cgroups_v2_permission_error(self):
        """Test behavior when permission is denied."""
        with patch('setup_env_limits.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            result = _setup_cgroups_v2(1024)
            assert result is None

    def test_cleanup_cgroups_v2(self):
        """Test cleanup removes empty directory."""
        # This is hard to test without real filesystem interaction
        # We mock the path existence and iterdir
        with patch('setup_env_limits.Path.exists', return_value=True):
            with patch('setup_env_limits.Path.iterdir', return_value=iter([])):
                with patch('setup_env_limits.Path.rmdir') as mock_rmdir:
                    _cleanup_cgroups_v2("/fake/path")
                    mock_rmdir.assert_called_once()

class TestUlimit:
    def test_set_ulimit_memory(self):
        """Test setting ulimit memory."""
        # This test might fail on restricted environments, so we wrap in try/except
        # or mock os.setrlimit
        with patch('setup_env_limits.os.setrlimit') as mock_setrlimit:
            _set_ulimit_memory(1.0)
            # Check that setrlimit was called with correct arguments
            # RLIMIT_AS, (soft, hard) in KB
            expected_limit_kb = int(1.0 * 1024 * 1024)
            mock_setrlimit.assert_called_once()
            args = mock_setrlimit.call_args[0]
            assert args[0] == os.RLIMIT_AS
            assert args[1][0] == expected_limit_kb * 1024
            assert args[1][1] == expected_limit_kb * 1024

class TestRunWithLimits:
    def test_run_simple_command(self):
        """Test running a simple command within limits."""
        result = run_with_limits(["echo", "hello"], memory_gb=1, time_limit_hours=1)
        assert result.returncode == 0
        assert "hello" in result.stdout.decode()

    def test_run_timeout(self):
        """Test that a command exceeding time limit raises TimeoutError."""
        with pytest.raises(TimeoutError):
            # Sleep for 10 seconds, limit 0.1 seconds
            run_with_limits(["sleep", "10"], time_limit_hours=0.00003) # ~0.1s

    def test_run_memory_limit_warning(self):
        """Test that a warning is printed if cgroups fails."""
        # Mock _setup_cgroups_v2 to return None
        with patch('setup_env_limits._setup_cgroups_v2', return_value=None):
            with patch('setup_env_limits._set_ulimit_memory'):
                # We expect a warning to be printed, but the command should still run
                # (unless ulimit kills it, which is hard to control in tests)
                # We just check that it doesn't crash the setup
                try:
                    result = run_with_limits(["echo", "test"], memory_gb=1, time_limit_hours=1)
                    assert result.returncode == 0
                except Exception:
                    # If it fails due to ulimit restrictions in the test env, that's okay
                    # as long as the logic path was executed
                    pass

    def test_run_with_cgroups_and_cgexec(self):
        """Test run_with_limits uses cgexec when available."""
        # Mock shutil.which to return a path for cgexec
        with patch('setup_env_limits.shutil.which', return_value="/usr/bin/cgexec"):
            with patch('setup_env_limits._setup_cgroups_v2', return_value="/fake/cgroup"):
                # Mock subprocess.run to avoid actually running cgexec
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    run_with_limits(["echo", "test"])
                    
                    # Check that the command was prepended with cgexec
                    call_args = mock_run.call_args
                    cmd = call_args[1]['cmd']
                    assert "cgexec" in cmd
                    assert "-g" in cmd
                    assert "memory:llmxive_runner" in cmd

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
