"""
Unit tests for download logic in code/download.py.
Specifically tests retry behavior on HTTP errors.
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import ConnectionError
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

# Import the module to test.
# We assume download.py exists as per T006/T011 completion.
# If download.py is not fully implemented yet, we mock the necessary parts
# or import the specific function if it exists.
try:
    from download import download_file
except ImportError:
    # Fallback for testing environment if download.py is not fully ready
    # In a real run, this would be the actual module.
    # We define a minimal mock structure here to satisfy the test logic
    # if the actual file isn't fully ready, but the task implies T006 is done.
    # Since T006 is marked completed, we assume download_file exists.
    # If the import fails, we raise a clear error.
    raise ImportError("Could not import download module. Ensure T006/T011 is implemented.")


@pytest.fixture
def mock_session():
    """Create a mock requests.Session."""
    session = MagicMock()
    return session


def test_download_retries_on__error():
    """
    Verify that download_file retries multiple times on HTTP 404
    and raises ConnectionError on final failure.
    """
    url = "https://example.com/nonexistent_file.nii"
    output_path = "/tmp/test_output.nii"
    max_retries = 3

    # Create a mock response that raises HTTPError (404)
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=MagicMock(status_code=404)
    )

    # We need to patch the session.get method to return our failing mock
    # We will simulate the loop behavior by patching the internal logic
    # or the session.get call directly.

    # Strategy: Patch requests.Session.get to return a response that raises HTTPError
    # We need to ensure it raises 404 exactly 'max_retries' times.
    
    call_count = 0
    
    def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= max_retries:
            # Simulate 404 error
            resp = MagicMock()
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                response=MagicMock(status_code=404, text="Not Found")
            )
            return resp
        else:
            # Should not reach here if logic is correct
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            return resp

    with patch('requests.Session') as MockSession:
        mock_session_instance = MagicMock()
        MockSession.return_value = mock_session_instance
        mock_session_instance.get.side_effect = mock_get
        mock_session_instance.__enter__ = MagicMock(return_value=mock_session_instance)
        mock_session_instance.__exit__ = MagicMock(return_value=False)

        # We also need to mock the actual file write to avoid IO errors in test
        with patch('builtins.open', MagicMock()):
            with patch('os.makedirs', MagicMock()):
                with pytest.raises(ConnectionError) as exc_info:
                    download_file(url, output_path, max_retries=max_retries)

                # Verify the error message mentions the URL or the failure
                assert "ConnectionError" in str(type(exc_info.value)) or "Failed" in str(exc_info.value)

    # Verify that get was called exactly max_retries times
    assert mock_session_instance.get.call_count == max_retries, \
        f"Expected {max_retries} calls, got {mock_session_instance.get.call_count}"