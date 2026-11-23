"""
Unit tests for the resource monitoring wrapper (T008).

These tests verify that the resource_monitor context manager correctly
detects and raises exceptions when resource limits are exceeded.
"""
import pytest
import time
import sys
import os
from unittest.mock import patch, MagicMock
from contextlib import nullcontext

# Import the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from resource_monitor import (
    ResourceLimitExceeded,
    resource_monitor,
    get_current_ram_mb,
    get_current_cpu_time,
    enforce_resource_limits
)


class TestResourceLimitExceeded:
    """Tests for the ResourceLimitExceeded exception."""

    def test_exception_instantiation(self):
        """Test that the exception can be instantiated with a message."""
        msg = "CPU time exceeded"
        exc = ResourceLimitExceeded(msg)
        assert str(exc) == msg
        assert exc.args[0] == msg


class TestResourceFunctions:
    """Tests for helper functions."""

    def test_get_current_ram_mb_returns_number(self):
        """Test that get_current_ram_mb returns a numeric value."""
        ram = get_current_ram_mb()
        assert isinstance(ram, (int, float))
        assert ram >= 0

    def test_get_current_cpu_time_returns_number(self):
        """Test that get_current_cpu_time returns a numeric value."""
        cpu = get_current_cpu_time()
        assert isinstance(cpu, (int, float))
        assert cpu >= 0


class TestResourceMonitorContextManager:
    """Tests for the resource_monitor context manager."""

    @pytest.mark.skipif(sys.platform == 'win32', reason="rlimit not available on Windows")
    def test_monitor_exceeds_cpu_limit(self):
        """Test that exceeding CPU limit raises ResourceLimitExceeded."""
        # Mock get_current_cpu_time to simulate rapid CPU usage
        with patch('resource_monitor.get_current_cpu_time') as mock_cpu:
            mock_cpu.return_value = 100.0  # Simulate 100s CPU usage
            
            with pytest.raises(ResourceLimitExceeded, match="CPU time limit exceeded"):
                with resource_monitor(cpu_limit=1.0, check_interval=0.0):
                    pass  # Immediate check

    @pytest.mark.skipif(sys.platform == 'win32', reason="rlimit not available on Windows")
    def test_monitor_exceeds_ram_limit(self):
        """Test that exceeding RAM limit raises ResourceLimitExceeded."""
        # Mock get_current_ram_mb to simulate high memory usage
        with patch('resource_monitor.get_current_ram_mb') as mock_ram:
            mock_ram.return_value = 10000.0  # Simulate 10GB usage
            
            with pytest.raises(ResourceLimitExceeded, match="RAM limit exceeded"):
                with resource_monitor(ram_limit=1 * 1024 * 1024 * 1024, check_interval=0.0):
                    pass  # Immediate check

    def test_monitor_within_limits(self):
        """Test that normal execution within limits completes successfully."""
        # Mock functions to return low values
        with patch('resource_monitor.get_current_cpu_time', return_value=1.0):
            with patch('resource_monitor.get_current_ram_mb', return_value=100.0):
                # Should not raise
                with resource_monitor(cpu_limit=10.0, ram_limit=1024*1024*1024, check_interval=0.0):
                    pass
    
    def test_monitor_keyboard_interrupt(self):
        """Test that KeyboardInterrupt is propagated correctly."""
        with patch('resource_monitor.get_current_cpu_time', return_value=1.0):
            with patch('resource_monitor.get_current_ram_mb', return_value=100.0):
                with patch('time.sleep', side_effect=KeyboardInterrupt):
                    with pytest.raises(KeyboardInterrupt):
                        with resource_monitor(check_interval=0.0):
                            pass

    def test_monitor_logs_progress(self, caplog):
        """Test that the monitor logs progress periodically."""
        import logging
        caplog.set_level(logging.INFO)
        
        with patch('resource_monitor.get_current_cpu_time', return_value=1.0):
            with patch('resource_monitor.get_current_ram_mb', return_value=100.0):
                with patch('time.time', side_effect=[0, 60, 120]):  # Simulate 60s intervals
                    with resource_monitor(check_interval=60.0):
                        pass
        
        # Check that log messages were generated
        assert any("Resource check" in record.message for record in caplog.records)


class TestEnforceResourceLimitsDecorator:
    """Tests for the enforce_resource_limits decorator."""

    def test_decorator_wraps_function(self):
        """Test that the decorator correctly wraps a function."""
        @enforce_resource_limits
        def dummy_func():
            return "success"
        
        # Should execute successfully
        result = dummy_func()
        assert result == "success"
        assert dummy_func.__name__ == "dummy_func"

    def test_decorator_raises_on_limit_exceeded(self):
        """Test that the decorator raises if limits are exceeded."""
        with patch('resource_monitor.get_current_cpu_time', return_value=100.0):
            @enforce_resource_limits
            def dummy_func():
                return "should not reach here"
            
            with pytest.raises(ResourceLimitExceeded):
                dummy_func()

class TestEnvOverride:
    """Tests for environment variable override logic (T008d)."""

    def test_env_override(self):
        """
        Confirm success when env vars are set higher than defaults.
        
        This test verifies that if RUNTIME_LIMIT_H and MEMORY_LIMIT_GB
        are set in the environment, the decorator uses those values
        instead of the defaults, allowing a function that would otherwise
        fail to succeed.
        """
        # We mock the resource checks to return values that would
        # exceed the DEFAULT limits but NOT the ENV override limits.
        
        # Defaults are typically: runtime 6h (21600s), memory 7GB (7168MB)
        # We set env vars to much higher values: 100h, 100GB
        # We mock the usage to be: 50h (180000s), 50GB (51200MB)
        # 50h > 6h (Default Fail) BUT 50h < 100h (Env Pass)
        # 50GB > 7GB (Default Fail) BUT 50GB < 100GB (Env Pass)
        
        env_runtime = 100.0 * 3600  # 100 hours in seconds
        env_memory = 100.0 * 1024   # 100 GB in MB
        
        mock_cpu_usage = 50.0 * 3600  # 50 hours
        mock_ram_usage = 50.0 * 1024  # 50 GB

        with patch.dict(os.environ, {
            'RUNTIME_LIMIT_H': '100',
            'MEMORY_LIMIT_GB': '100'
        }):
            # Re-import or reload if necessary, but since we are testing
            # the decorator logic which reads env vars at call time (or
            # decorator definition time depending on implementation),
            # we ensure the patch is active.
            # Assuming the decorator reads env vars when applied or called.
            # Based on T008b spec, it reads env vars.
            
            # We need to patch the resource functions to simulate the usage
            with patch('resource_monitor.get_current_cpu_time', return_value=mock_cpu_usage):
                with patch('resource_monitor.get_current_ram_mb', return_value=mock_ram_usage):
                    # The decorator should read the env vars (100h/100GB)
                    # and allow the 50h/50GB usage to pass.
                    # If it used defaults (6h/7GB), it would raise.
                    
                    @enforce_resource_limits
                    def heavy_function():
                        return "success"
                    
                    # This should NOT raise ResourceLimitExceeded
                    # because the env override allows it.
                    result = heavy_function()
                    assert result == "success"

    def test_env_override_prevents_default_failure(self):
        """
        Confirm that without env vars, the same usage would fail.
        This ensures the test is actually checking the override logic.
        """
        # Ensure env vars are NOT set (or reset to defaults if the module cached them)
        # In a real test runner, we might need to reload the module to clear cached defaults
        # if the decorator reads env vars at definition time.
        # However, standard pattern is reading at call time or decorator init time.
        # We will simulate the scenario where defaults are strict.
        
        # Mock usage that exceeds defaults (6h, 7GB)
        mock_cpu_usage = 10.0 * 3600  # 10 hours
        mock_ram_usage = 10.0 * 1024  # 10 GB

        # Ensure env vars are not set to override
        with patch.dict(os.environ, {}, clear=True):
            # Clear any specific keys if they exist
            for key in ['RUNTIME_LIMIT_H', 'MEMORY_LIMIT_GB']:
                if key in os.environ:
                    del os.environ[key]
            
            # We must reload the module to ensure it picks up the missing env vars
            # and re-evaluates defaults.
            import importlib
            import resource_monitor
            importlib.reload(resource_monitor)
            
            from resource_monitor import enforce_resource_limits, ResourceLimitExceeded
            
            with patch.object(resource_monitor, 'get_current_cpu_time', return_value=mock_cpu_usage):
                with patch.object(resource_monitor, 'get_current_ram_mb', return_value=mock_ram_usage):
                    @enforce_resource_limits
                    def failing_function():
                        return "should not reach here"
                    
                    with pytest.raises(ResourceLimitExceeded):
                        failing_function()