import pytest
import time
from unittest.mock import patch, MagicMock, call
from urllib.error import URLError

from code.utils.network import MaxRetriesError, exponential_backoff_request

class TestRetryExponentialBackoff:
    """
    Unit test for T011: Assert network utility retries exactly 3 times 
    with exponential delays before raising MaxRetriesError.
    """

    def test_retry_exponential_backoff_retries_exactly_3_times(self):
        """
        Assert that the function attempts the operation exactly 3 times 
        (initial + 2 retries) before raising MaxRetriesError.
        """
        mock_func = MagicMock(side_effect=URLError("Connection failed"))
        
        # Base delay of 1 second for easier testing
        base_delay = 1.0
        max_retries = 3
        
        with pytest.raises(MaxRetriesError) as exc_info:
            exponential_backoff_request(
                mock_func, 
                max_retries=max_retries, 
                base_delay=base_delay
            )
        
        # Verify the function was called exactly 3 times
        assert mock_func.call_count == 3
        assert "MaxRetriesError" in str(type(exc_info.value))
        assert "Failed after 3 attempts" in str(exc_info.value)

    def test_retry_exponential_backoff_delays(self):
        """
        Assert that the delays between retries follow exponential backoff.
        Delays should be: base_delay * 2^0, base_delay * 2^1
        (No delay after the final failure, as we just raise)
        """
        mock_func = MagicMock(side_effect=URLError("Connection failed"))
        base_delay = 0.1  # Use small delay for faster test execution
        max_retries = 3
        
        # We need to measure time or check sleep calls. 
        # Since time.sleep is blocking, we mock it to record calls.
        with patch('code.utils.network.time.sleep') as mock_sleep:
            with pytest.raises(MaxRetriesError):
                exponential_backoff_request(
                    mock_func, 
                    max_retries=max_retries, 
                    base_delay=base_delay
                )
            
            # Expect 2 sleep calls: before 2nd attempt and before 3rd attempt
            # Attempt 1: fail -> sleep (delay = 0.1 * 2^0 = 0.1)
            # Attempt 2: fail -> sleep (delay = 0.1 * 2^1 = 0.2)
            # Attempt 3: fail -> raise (no sleep)
            assert mock_sleep.call_count == 2
            
            # Check the first delay (2^0)
            mock_sleep.assert_any_call(base_delay * (2 ** 0))
            # Check the second delay (2^1)
            mock_sleep.assert_any_call(base_delay * (2 ** 1))

    def test_retry_exponential_backoff_success_on_second_attempt(self):
        """
        Assert that if the function succeeds on the 2nd attempt, 
        no MaxRetriesError is raised and subsequent sleeps are skipped.
        """
        mock_func = MagicMock(side_effect=[
            URLError("First try failed"), 
            "Success"
        ])
        
        base_delay = 0.1
        max_retries = 3
        
        with patch('code.utils.network.time.sleep') as mock_sleep:
            result = exponential_backoff_request(
                mock_func, 
                max_retries=max_retries, 
                base_delay=base_delay
            )
            
            assert result == "Success"
            assert mock_func.call_count == 2
            # Only one sleep should have occurred (after first failure)
            assert mock_sleep.call_count == 1

    def test_retry_exponential_backoff_success_on_first_attempt(self):
        """
        Assert that if the function succeeds immediately, no retries or sleeps occur.
        """
        mock_func = MagicMock(return_value="Immediate Success")
        
        base_delay = 0.1
        max_retries = 3
        
        with patch('code.utils.network.time.sleep') as mock_sleep:
            result = exponential_backoff_request(
                mock_func, 
                max_retries=max_retries, 
                base_delay=base_delay
            )
            
            assert result == "Immediate Success"
            assert mock_func.call_count == 1
            assert mock_sleep.call_count == 0