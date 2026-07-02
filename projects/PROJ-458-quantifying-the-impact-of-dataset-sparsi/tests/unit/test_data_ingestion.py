import unittest
from unittest.mock import patch, MagicMock, call
import time
import requests
from requests.exceptions import RequestException, HTTPError

# Import the module under test.
# Assuming data_ingestion.py is at code/data_ingestion.py relative to project root.
# The test is at tests/unit/test_data_ingestion.py.
# sys.path manipulation to allow importing 'code' as a package or direct module.
import sys
import os
from pathlib import Path

# Add the project root to the path so we can import 'code' modules if needed,
# or specifically import the function we are testing if it's exposed.
# Since the task asks to test 'api_backoff_retries_on_rate_limit', we assume
# this function exists in code/data_ingestion.py.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from code.data_ingestion import api_backoff_retries_on_rate_limit
except ImportError:
    # Fallback if the module structure is different or function not yet implemented.
    # In a real TDD flow, this import would fail initially until implementation.
    # For the purpose of this task, we define a mock function if missing to satisfy
    # the test structure, but the task requires the test to be written for the REAL function.
    # We will assume the implementation exists as per the "Implement the task for real" constraint
    # which implies the function signature is known or standard.
    # However, strictly following "Write tests FIRST, ensure they FAIL", we write the test
    # against the expected interface.
    
    # Define a stub if import fails to allow the test file to be syntactically valid
    # for the purpose of the "write test" task, but the actual execution would fail
    # if the real function isn't there.
    def api_backoff_retries_on_rate_limit(url, max_retries=3):
        raise NotImplementedError("Implementation pending")

class TestApiBackoffRetries(unittest.TestCase):
    """
    Unit test for test_api_backoff_retries_on_rate_limit in code/data_ingestion.py.
    
    This test verifies that the function implements exponential backoff and
    retries correctly when a 429 (Too Many Requests) status code is received.
    """

    @patch('code.data_ingestion.requests.get')
    def test_api_backoff_retries_on_rate_limit(self, mock_get):
        """
        Test that the function retries on 429 status code with exponential backoff.
        """
        # Arrange
        test_url = "https://materialsproject.org/api/v1/materials"
        max_retries = 3
        
        # Simulate a sequence of failures followed by a success.
        # 429 on first call, 429 on second call, 200 on third call.
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = HTTPError(response=mock_response_429)
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "success"}
        mock_response_200.raise_for_status.return_value = None

        # Configure the mock to return these responses in order
        mock_get.side_effect = [
            mock_response_429,
            mock_response_429,
            mock_response_200
        ]

        # Act
        # We expect the function to retry. 
        # Note: The actual sleep time is mocked or we just verify call count.
        with patch('time.sleep') as mock_sleep:
            result = api_backoff_retries_on_rate_limit(test_url, max_retries=max_retries)

        # Assert
        # 1. requests.get should be called 3 times (2 failures + 1 success)
        self.assertEqual(mock_get.call_count, 3)
        
        # 2. time.sleep should be called 2 times (after 1st failure, after 2nd failure)
        # Exponential backoff: sleep(1), sleep(2), etc. (base 1s usually)
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Verify sleep arguments roughly match exponential backoff (e.g., 1s, 2s)
        # We don't assert exact seconds as implementation details vary, but we assert it was called.
        mock_sleep.assert_any_call(1) 
        mock_sleep.assert_any_call(2)

        # 3. The result should be the successful response
        self.assertEqual(result.json(), {"data": "success"})

    @patch('code.data_ingestion.requests.get')
    def test_api_backoff_raises_after_max_retries(self, mock_get):
        """
        Test that the function raises an exception if max_retries are exhausted.
        """
        # Arrange
        test_url = "https://materialsproject.org/api/v1/materials"
        max_retries = 2
        
        # Simulate persistent 429 errors
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = HTTPError(response=mock_response_429)
        
        mock_get.side_effect = [mock_response_429, mock_response_429]

        # Act & Assert
        with patch('time.sleep'):
            with self.assertRaises(HTTPError):
                api_backoff_retries_on_rate_limit(test_url, max_retries=max_retries)

        # Verify requests.get was called exactly max_retries times
        self.assertEqual(mock_get.call_count, max_retries)

    @patch('code.data_ingestion.requests.get')
    def test_api_backoff_success_first_try(self, mock_get):
        """
        Test that the function returns immediately if the first request succeeds.
        """
        # Arrange
        test_url = "https://materialsproject.org/api/v1/materials"
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "success"}
        mock_response_200.raise_for_status.return_value = None
        
        mock_get.return_value = mock_response_200

        # Act
        with patch('time.sleep') as mock_sleep:
            result = api_backoff_retries_on_rate_limit(test_url)

        # Assert
        self.assertEqual(mock_get.call_count, 1)
        mock_sleep.assert_not_called()
        self.assertEqual(result.json(), {"data": "success"})

if __name__ == '__main__':
    unittest.main()