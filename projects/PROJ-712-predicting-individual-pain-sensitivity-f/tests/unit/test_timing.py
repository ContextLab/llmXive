"""
Unit tests for timing instrumentation (Task T026a).
Verifies SC-005 enforcement: execution time < 6 hours.
"""
import time
import pytest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.utils import (
    start_timer,
    stop_timer,
    measure_duration,
    assert_duration_limit,
    validate_pipeline_duration,
    MAX_EXECUTION_SECONDS
)


class TestTimingInstrumentation:
    """Tests for the timing instrumentation functions."""

    def test_measure_duration_basic(self):
        """Test basic duration calculation."""
        start = time.time()
        time.sleep(0.1)  # Sleep for 100ms
        duration = measure_duration(start)
        assert duration >= 0.1
        assert duration < 0.5  # Should not take more than 500ms

    def test_assert_duration_limit_pass(self):
        """Test that assert_duration_limit passes for short durations."""
        # 1 second should pass easily
        assert_duration_limit(1.0)
        assert_duration_limit(3600.0)  # 1 hour should pass

    def test_assert_duration_limit_fail(self):
        """Test that assert_duration_limit raises AssertionError for long durations."""
        # 7 hours (25200 seconds) should fail given default limit of 6 hours (21600 seconds)
        with pytest.raises(AssertionError) as exc_info:
            assert_duration_limit(25200.0)
        
        assert "SC-005 VIOLATION" in str(exc_info.value)

    def test_assert_duration_limit_custom_limit(self):
        """Test assert_duration_limit with a custom limit."""
        # 10 seconds should pass with a 20 second limit
        assert_duration_limit(10.0, limit_seconds=20.0)
        
        # 30 seconds should fail with a 20 second limit
        with pytest.raises(AssertionError):
            assert_duration_limit(30.0, limit_seconds=20.0)

    def test_start_stop_timer_sequence(self):
        """Test starting and stopping the global timer."""
        start = start_timer()
        assert start is not None
        time.sleep(0.05)
        duration = stop_timer()
        
        assert duration >= 0.05
        assert duration < 1.0  # Should be very fast

    def test_stop_timer_without_start_raises(self):
        """Test that stopping an unstarted timer raises RuntimeError."""
        # Reset state if necessary (though usually handled by global state)
        # For this test, we assume a clean state or rely on the function's internal check
        # Since we can't easily reset global state in a test without side effects,
        # we rely on the function logic.
        # However, if a previous test started a timer, this might fail.
        # A more robust test would mock the global state.
        
        # Mocking the global state to simulate "not started"
        import code.utils as utils
        original_start = utils._start_time
        utils._start_time = None
        
        try:
            with pytest.raises(RuntimeError) as exc_info:
                stop_timer()
            assert "Timer was not started" in str(exc_info.value)
        finally:
            utils._start_time = original_start

    def test_validate_pipeline_duration_integration(self):
        """Integration test for validate_pipeline_duration."""
        start = start_timer()
        time.sleep(0.01)
        # Should pass
        validate_pipeline_duration(start)
        
        # Force a failure by mocking the duration check
        with patch('code.utils.assert_duration_limit', side_effect=AssertionError("Mocked")):
            with pytest.raises(AssertionError):
                validate_pipeline_duration(start)

    def test_duration_less_than_6_hours(self):
        """Verify the default limit is 6 hours in seconds."""
        # 6 hours = 21600 seconds
        assert MAX_EXECUTION_SECONDS == 21600
        assert_duration_limit(21599.0)  # Just under limit
        with pytest.raises(AssertionError):
            assert_duration_limit(21601.0)  # Just over limit