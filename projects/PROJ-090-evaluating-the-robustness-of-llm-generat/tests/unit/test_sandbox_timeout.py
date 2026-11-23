"""
Unit test for sandbox timeout enforcement.

Verifies that subprocess.run raises TimeoutExpired after a specified timeout duration.
"""
import subprocess
import time
import sys
import os
from pathlib import Path


def test_sandbox_timeout_enforcement():
    """
    Verify that subprocess.run raises TimeoutExpired after a specified timeout duration.
    
    This test runs a long-running command in a subprocess and ensures that:
    1. The subprocess is terminated after the timeout.
    2. subprocess.TimeoutExpired exception is raised.
    3. The elapsed time is close to the timeout duration (not the sleep duration).
    """
    timeout_duration = 1  # 1 second timeout
    # Command that sleeps for 10 seconds (much longer than timeout)
    sleep_command = [sys.executable, "-c", "import time; time.sleep(10)"]
    
    start_time = time.time()
    
    try:
        # Run with a short timeout
        subprocess.run(
            sleep_command,
            timeout=timeout_duration,
            capture_output=True,
            text=True,
            check=False
        )
        # If we get here, the test failed (no exception raised)
        raise AssertionError("Expected subprocess.TimeoutExpired to be raised")
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start_time
        # Verify the timeout was enforced (allow some tolerance for system overhead)
        # The elapsed time should be close to the timeout, not the full sleep time
        assert elapsed < timeout_duration + 2, (
            f"Timeout not enforced properly, took {elapsed:.2f}s (expected ~{timeout_duration}s)"
        )
        # Verify we didn't wait the full 10 seconds
        assert elapsed < 5, f"Process was not terminated after timeout, took {elapsed:.2f}s"
        print(f"✓ Timeout enforced correctly after {elapsed:.2f}s (expected ~{timeout_duration}s)")
    except Exception as e:
        raise AssertionError(f"Unexpected exception: {type(e).__name__}: {e}")


def test_sandbox_timeout_with_custom_message():
    """
    Verify that TimeoutExpired contains useful information about the command.
    """
    timeout_duration = 1
    sleep_command = [sys.executable, "-c", "import time; time.sleep(10)"]
    
    try:
        subprocess.run(
            sleep_command,
            timeout=timeout_duration,
            capture_output=True,
            text=True
        )
        raise AssertionError("Expected subprocess.TimeoutExpired to be raised")
    except subprocess.TimeoutExpired as e:
        # Verify the exception has the command and timeout info
        assert e.cmd is not None, "TimeoutExpired should contain the command"
        assert e.timeout == timeout_duration, "TimeoutExpired should contain the timeout value"
        print(f"✓ TimeoutExpired contains correct command and timeout info")


if __name__ == "__main__":
    test_sandbox_timeout_enforcement()
    test_sandbox_timeout_with_custom_message()
    print("\n✓ All sandbox timeout tests passed.")