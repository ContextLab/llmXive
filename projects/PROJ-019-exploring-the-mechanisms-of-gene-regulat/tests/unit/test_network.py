import pytest
import time
from code.utils.network import exponential_backoff_request, MaxRetriesError

def test_retry_exponential_backoff():
    """
    Test that the network utility retries exactly 3 times with exponential delays 
    before raising MaxRetriesError.
    Covers: US1-FR-006 (Exponential backoff retry logic)
    
    This test verifies the retry mechanism by simulating a failing request.
    """
    call_count = 0
    max_calls = 3
    
    def failing_request():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Simulated network failure")
    
    # Test with max_retries=3 (should attempt 4 times total: 1 initial + 3 retries)
    with pytest.raises(MaxRetriesError) as exc_info:
        exponential_backoff_request(
            failing_request,
            max_retries=max_calls,
            base_delay=0.1,  # Small delay for testing
            max_delay=1.0
        )
    
    # Verify that the function was called exactly max_calls + 1 times
    assert call_count == max_calls + 1, \
        f"Expected {max_calls + 1} calls, got {call_count}"
    
    # Verify that MaxRetriesError was raised
    assert isinstance(exc_info.value, MaxRetriesError), \
        f"Expected MaxRetriesError, got {type(exc_info.value)}"

def test_retry_success_after_failure():
    """
    Test that the function succeeds after a few failures.
    """
    call_count = 0
    
    def eventually_successful_request():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Simulated network failure")
        return "success"
    
    result = exponential_backoff_request(
        eventually_successful_request,
        max_retries=5,
        base_delay=0.01,
        max_delay=0.1
    )
    
    assert result == "success", f"Expected 'success', got {result}"
    assert call_count == 3, f"Expected 3 calls, got {call_count}"

def test_retry_delay_exponential():
    """
    Test that delays between retries are exponential.
    """
    call_times = []
    
    def failing_with_timing():
        call_times.append(time.time())
        raise ConnectionError("Simulated failure")
    
    with pytest.raises(MaxRetriesError):
        exponential_backoff_request(
            failing_with_timing,
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0
        )
    
    # Verify that at least 3 calls were made
    assert len(call_times) >= 4, f"Expected at least 4 calls, got {len(call_times)}"
    
    # Verify exponential delay pattern (delays should increase)
    if len(call_times) >= 3:
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        # Delay should roughly double (within tolerance for timing noise)
        assert delay2 >= delay1 * 0.8, \
            f"Delay should be exponential: {delay1} -> {delay2}"