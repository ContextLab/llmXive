"""
Unit test for sandbox timeout enforcement (T022).

This test verifies that the sandbox execution environment correctly
enforces timeouts for code execution, preventing infinite loops or
hung processes.
"""
import pytest
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.model.sandbox import execute_code, ExecutionError, TimeoutError


class TestSandboxTimeout:
    """Test suite for sandbox timeout functionality."""

    def test_timeout_enforcement(self):
        """Verify that code execution is terminated after the specified timeout."""
        # Code that runs forever
        infinite_code = """
        while True:
            pass
        """

        # Should raise TimeoutError after 1 second
        start_time = time.time()
        with pytest.raises(ExecutionError) as exc_info:
            execute_code(infinite_code, timeout=1)

        elapsed = time.time() - start_time
        # Execution should not take significantly longer than timeout
        assert elapsed < 3.0, f"Timeout enforcement took too long: {elapsed}s"
        assert "timeout" in str(exc_info.value).lower() or "timed out" in str(exc_info.value).lower()

    def test_normal_execution_within_timeout(self):
        """Verify that normal code completes successfully within timeout."""
        normal_code = """
        result = sum(range(1000))
        print(result)
        """

        # Should complete successfully
        result = execute_code(normal_code, timeout=5)
        assert result["status"] == "pass"
        assert "500500" in result["output"]

    def test_timeout_parameter_validation(self):
        """Verify that invalid timeout values are handled."""
        with pytest.raises(ValueError):
            execute_code("print(1)", timeout=-1)

        with pytest.raises(ValueError):
            execute_code("print(1)", timeout=0)

    def test_code_with_deliberate_delay(self):
        """Verify timeout catches code that exceeds limit but isn't infinite."""
        delayed_code = """
        import time
        time.sleep(2)
        print("done")
        """

        # Should timeout before completing
        with pytest.raises(ExecutionError) as exc_info:
            execute_code(delayed_code, timeout=1)

        assert "timeout" in str(exc_info.value).lower() or "timed out" in str(exc_info.value).lower()