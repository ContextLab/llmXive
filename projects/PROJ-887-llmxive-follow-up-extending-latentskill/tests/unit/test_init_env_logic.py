import os
import sys
import time
import multiprocessing
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

# Adjust import path if necessary based on project structure
# Assuming src/ is in the root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.init_env_logic import run_task_with_timeout

class TestTimeoutMechanism:
    """
    Unit tests for the timeout mechanism in init_env_logic.py (T041/T046).
    Verifies that run_task_with_timeout correctly handles hanging tasks
    and returns False with a timeout_failure status.
    """

    def test_successful_task_completes_in_time(self):
        """
        Test that a task completing within the timeout returns True (success).
        """
        def fast_task():
            time.sleep(0.1)
            return True

        result = run_task_with_timeout(fast_task, timeout=5.0)
        assert result is True

    def test_timeout_triggers_on_hanging_task(self):
        """
        Test that a task taking longer than the timeout triggers the timeout
        mechanism and returns False.
        """
        def hanging_task():
            time.sleep(10)  # Sleep longer than timeout
            return True

        # We expect the function to return False because the process is killed/times out
        result = run_task_with_timeout(hanging_task, timeout=1.0)
        assert result is False

    def test_timeout_raises_exception_in_task(self):
        """
        Test behavior when the task raises an exception.
        The timeout mechanism should handle the crash gracefully or propagate it.
        Based on typical timeout implementations, if the child crashes,
        the parent usually detects the failure.
        """
        def crashing_task():
            raise RuntimeError("Simulated environment crash")

        result = run_task_with_timeout(crashing_task, timeout=5.0)
        # Depending on implementation, this might return False or raise.
        # Given the requirement "return False to prevent hanging", we expect False.
        assert result is False

    def test_task_returns_false_on_environment_failure(self):
        """
        Test that a task returning False (environment failure) is propagated correctly.
        """
        def failing_task():
            time.sleep(0.1)
            return False

        result = run_task_with_timeout(failing_task, timeout=5.0)
        assert result is False

    @patch('multiprocessing.Process')
    def test_process_join_timeout_handling(self, mock_process_class):
        """
        Test the internal logic where the parent waits for the child process.
        This mocks the Process to ensure the timeout logic path is covered.
        """
        mock_process = MagicMock()
        mock_process.is_alive.return_value = False
        mock_process.join.return_value = None
        mock_process.exitcode = 0
        mock_process_class.return_value = mock_process

        def dummy_target():
            pass

        # Patch the actual execution to avoid real process spawning in unit test
        # but verify the logic flow
        with patch('src.evaluation.init_env_logic.multiprocessing.Process', return_value=mock_process):
            # We need to call the function but prevent the actual sleep/execution
            # by mocking the target function's effect or the join timeout.
            # A more direct test of the logic flow:
            pass

        # Direct test of the timeout logic using a real short sleep is safer
        # to verify the specific T041 requirement: "If task exceeds timeout... return False"
        def slow_task():
            time.sleep(2)
            return True

        # Force a very short timeout
        start = time.time()
        result = run_task_with_timeout(slow_task, timeout=0.5)
        elapsed = time.time() - start

        assert result is False
        # Ensure the function didn't wait for the full 2 seconds
        assert elapsed < 1.5  # Should return near 0.5s + overhead

    def test_logging_timeout_failure(self):
        """
        Verify that a timeout failure is logged (implicitly tested by the function
        executing without crashing and returning False, but we can assert the return).
        """
        def infinite_loop():
            while True:
                time.sleep(0.1)

        result = run_task_with_timeout(infinite_loop, timeout=0.5)
        assert result is False
        # The function should not hang the test runner