import pytest
import time
from unittest.mock import patch, MagicMock
from code.test_executor import retry_compile, CompilationFailedError

class TestRetryLogic:
    """Unit tests for the retry logic in test_executor.py."""

    def test_retry_logic_retries_3_times_before_failure(self):
        """
        Verifying the retry loop executes exactly 3 attempts before failure.
        
        This test mocks a scenario where the compilation function always fails.
        It asserts that:
        1. The underlying compile function is called exactly 3 times.
        2. The function raises CompilationFailedError after the 3rd attempt.
        """
        mock_compile_func = MagicMock(side_effect=CompilationFailedError("Compilation failed"))
        
        # We expect 3 attempts total (initial + 2 retries)
        with pytest.raises(CompilationFailedError):
            # Call retry_compile with the mock function that always fails
            # The retry logic should call it 3 times total
            retry_compile(mock_compile_func)
        
        # Verify the mock was called exactly 3 times
        assert mock_compile_func.call_count == 3, (
            f"Expected 3 attempts, but the function was called {mock_compile_func.call_count} times"
        )

    def test_retry_logic_succeeds_on_first_attempt(self):
        """
        Verifying that if compilation succeeds on the first try, 
        no retries occur and the result is returned.
        """
        mock_compile_func = MagicMock(return_value="Success")
        
        result = retry_compile(mock_compile_func)
        
        # Verify the mock was called exactly once
        assert mock_compile_func.call_count == 1
        assert result == "Success"

    def test_retry_logic_succeeds_on_second_attempt(self):
        """
        Verifying that if compilation fails once but succeeds on the second try,
        the function returns the success result and total attempts are 2.
        """
        call_count = 0
        
        def mock_compile_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise CompilationFailedError("First attempt failed")
            return "Success on second attempt"
        
        result = retry_compile(mock_compile_func)
        
        # Verify the function was called exactly twice
        assert call_count == 2
        assert result == "Success on second attempt"

    def test_retry_logic_waits_between_attempts(self):
        """
        Verifying that the retry logic includes a delay between attempts.
        This ensures we don't spam the system immediately.
        """
        mock_compile_func = MagicMock(side_effect=CompilationFailedError("Failed"))
        
        start_time = time.time()
        
        with pytest.raises(CompilationFailedError):
            retry_compile(mock_compile_func)
        
        elapsed = time.time() - start_time
        
        # The retry logic should have at least 2 delays (between attempt 1-2 and 2-3)
        # Assuming a 1 second delay per retry as per implementation
        assert elapsed >= 1.5, f"Expected at least 1.5 seconds of delay, but only {elapsed:.2f}s elapsed"

    def test_retry_logic_raises_after_max_attempts(self):
        """
        Verifying that the specific exception type is raised after max attempts.
        """
        mock_compile_func = MagicMock(side_effect=CompilationFailedError("Persistent failure"))
        
        with pytest.raises(CompilationFailedError) as exc_info:
            retry_compile(mock_compile_func)
        
        assert str(exc_info.value) == "Persistent failure"
        assert mock_compile_func.call_count == 3