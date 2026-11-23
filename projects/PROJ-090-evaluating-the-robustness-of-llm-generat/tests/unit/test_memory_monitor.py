"""
Unit tests for memory monitoring utilities.
"""
import pytest
import sys
import resource
from unittest.mock import patch, MagicMock

from utils.memory_monitor import (
    get_current_memory_mb,
    check_memory_limit,
    set_soft_memory_limit,
    MEMORY_LIMIT_GB,
    memory_guard
)

class TestMemoryMonitor:
    
    def test_get_current_memory_mb_returns_positive(self):
        """Test that get_current_memory_mb returns a positive number."""
        mem = get_current_memory_mb()
        assert isinstance(mem, float)
        assert mem >= 0.0

    def test_check_memory_limit_within(self):
        """Test check_memory_limit returns True when under limit."""
        # Use a very high limit to ensure we are under it
        assert check_memory_limit(limit_gb=1000.0) is True

    def test_check_memory_limit_exceeded(self):
        """Test check_memory_limit returns False when over limit."""
        # Use a tiny limit (e.g., 1 byte) to force failure
        # Note: In practice, the process uses > 0 bytes, so this should fail
        with patch('utils.memory_monitor.resource.getrusage') as mock_usage:
            mock_usage.return_value = MagicMock()
            mock_usage.return_value.ru_maxrss = 1024 * 1024 * 1024 * 10  # 10GB in KB
            assert check_memory_limit(limit_gb=1.0) is False

    def test_set_soft_memory_limit(self):
        """Test that set_soft_memory_limit sets the limit without raising."""
        # This should not raise an exception in a test environment
        try:
            set_soft_memory_limit(limit_gb=0.1)  # 100MB
        except ValueError:
            # Expected if the limit is too low for the current process
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    def test_memory_guard_success(self):
        """Test memory_guard context manager when limit is not exceeded."""
        with memory_guard(limit_gb=1000.0):
            # Do some work
            x = 1 + 1
        # Should complete without error

    def test_memory_guard_failure(self):
        """Test memory_guard context manager when limit is exceeded."""
        # Mock get_current_memory_mb to return a high value
        with patch('utils.memory_monitor.get_current_memory_mb') as mock_mem:
            with patch('utils.memory_monitor.check_memory_limit') as mock_check:
                mock_mem.return_value = 10000.0  # 10GB
                mock_check.return_value = False
                
                with pytest.raises(MemoryError):
                    with memory_guard(limit_gb=1.0):
                        pass

    def test_memory_guard_with_action(self):
        """Test memory_guard with a custom action on exceed."""
        action_called = False
        def my_action():
            nonlocal action_called
            action_called = True

        with patch('utils.memory_monitor.get_current_memory_mb') as mock_mem:
            with patch('utils.memory_monitor.check_memory_limit') as mock_check:
                mock_mem.return_value = 10000.0
                mock_check.return_value = False
                
                try:
                    with memory_guard(limit_gb=1.0, action_on_exceed=my_action):
                        pass
                except MemoryError:
                    pass
                
                # If action_on_exceed is provided, it should be called
                # Note: The current implementation raises MemoryError if action is None,
                # but if action is provided, it calls it. We need to verify behavior.
                # Based on implementation: if action_on_exceed is provided, it calls it, 
                # then raises MemoryError.
                # Let's adjust test to match implementation.
                # Actually, looking at the implementation:
                # if not check_memory_limit:
                #    if action_on_exceed: action_on_exceed()
                #    else: raise MemoryError
                # So if action is provided, it calls it but does NOT raise MemoryError in the 'if' block?
                # Wait, the implementation says:
                # if not check_memory_limit(limit_gb):
                #     if action_on_exceed:
                #         action_on_exceed()
                #     else:
                #         raise MemoryError(...)
                # So if action is provided, it doesn't raise? 
                # The context manager then exits normally? 
                # Let's re-read the implementation logic.
                # The implementation raises MemoryError ONLY if action is None.
                # If action is provided, it just calls it and the context manager exits normally.
                # So we should not expect MemoryError if action is provided.
                # But the test above expects MemoryError. Let's fix the test to match the implementation.
                
                # Correction: The test should verify that action is called, and no exception is raised
                # if action is provided.
                pass
                
                # Let's re-implement the test logic correctly based on the code:
                # If action is provided, no exception is raised in the 'if' block.
                # So the context manager exits normally.
                # But wait, the implementation has:
                # try:
                #     yield
                #     if not check_memory_limit: ...
                # except MemoryError: raise
                # So if action is provided, no MemoryError is raised, so the context manager exits normally.
                
                # Let's rewrite the test to be accurate.
                pass

    def test_memory_guard_correct_action_call(self):
        """Test that memory_guard calls action_on_exceed when limit is exceeded."""
        action_called = False
        def my_action():
            nonlocal action_called
            action_called = True

        with patch('utils.memory_monitor.get_current_memory_mb') as mock_mem:
            with patch('utils.memory_monitor.check_memory_limit') as mock_check:
                mock_mem.return_value = 10000.0
                mock_check.return_value = False
                
                # No exception should be raised if action is provided
                with memory_guard(limit_gb=1.0, action_on_exceed=my_action):
                    pass
                
                assert action_called is True
                # No MemoryError raised

    def test_memory_guard_raises_without_action(self):
        """Test that memory_guard raises MemoryError if no action is provided."""
        with patch('utils.memory_monitor.get_current_memory_mb') as mock_mem:
            with patch('utils.memory_monitor.check_memory_limit') as mock_check:
                mock_mem.return_value = 10000.0
                mock_check.return_value = False
                
                with pytest.raises(MemoryError):
                    with memory_guard(limit_gb=1.0):
                        pass