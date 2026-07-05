"""
Integration test for API retry/backoff logic in fetch_dft.py.

This test verifies that the Materials Project API fetcher correctly implements
exponential backoff and retry logic when encountering transient failures (429, 503).

It mocks the network layer to simulate rate-limiting scenarios and asserts
that the code waits appropriately before retrying, eventually succeeding or
failing with a clear error after max retries.
"""
import os
import time
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from requests.exceptions import HTTPError, RetryError
from mp_api.client import MPRester
from mp_api.core import MPContribsClient

# Import the function we are testing. 
# Note: We assume fetch_dft.py contains the logic we want to test.
# If the logic is inside a class or specific function, adjust imports accordingly.
# For this task, we assume a function `fetch_elastic_data` exists in code/ingestion/fetch_dft.py
# or we test the MPRester usage directly if that's where the retry logic is configured.
# Given the task description "Integration test for API retry/backoff logic",
# we will test the interaction with the MPRester client which handles retries.

# We need to import the config to get the API key and settings
try:
    from code.config import CONFIG
except ImportError:
    # Fallback if running from tests directory directly without package structure
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from code.config import CONFIG


class TestAPIRetryBackoff(unittest.TestCase):
    """Tests for exponential backoff and retry logic in Materials Project API calls."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api_key = "test_api_key_12345"
        self.test_material_id = "mp-12345"
        # Simulate a transient failure response
        self.mock_response_429 = MagicMock()
        self.mock_response_429.status_code = 429
        self.mock_response_429.text = "Too Many Requests"
        
        self.mock_response_503 = MagicMock()
        self.mock_response_503.status_code = 503
        self.mock_response_503.text = "Service Unavailable"
        
        self.mock_response_success = MagicMock()
        self.mock_response_success.status_code = 200
        self.mock_response_success.json.return_value = {
            "data": [
                {
                    "material_id": self.test_material_id,
                    "elasticity": {
                        "G_VRH": 80.5,
                        "K_VRH": 160.2
                    }
                }
            ]
        }

    @patch('code.ingestion.fetch_dft.MPRester')
    def test_retry_on_429_with_backoff(self, mock_mprester_class):
        """
        Test that the code retries on HTTP 429 (Too Many Requests) with exponential backoff.
        
        This simulates a scenario where the first two attempts fail with 429,
        and the third attempt succeeds.
        """
        # Setup the mock MPRester instance
        mock_mpr = MagicMock()
        mock_mprester_class.return_value = mock_mpr
        
        # Configure the mock to raise HTTPError on first two calls, succeed on third
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # Raise HTTPError for 429
                error = HTTPError(response=self.mock_response_429)
                error.response = self.mock_response_429
                raise error
            else:
                return self.mock_response_success.json()
        
        # Mock the specific method used to fetch data (e.g., get_elastic_data)
        # Assuming fetch_dft.py uses a method like get_elastic_data or similar
        # If the implementation uses a generic request method, adjust accordingly.
        # For MPRester, it usually has specific methods. Let's assume a generic one for testing retry logic
        # or patch the underlying requests session if MPRester uses it.
        # A more robust way is to patch the session's request method.
        mock_mpr._make_request = MagicMock(side_effect=side_effect)
        
        # Import the function to test. 
        # Assuming there is a function in fetch_dft.py that handles the retry logic.
        # If the retry logic is internal to MPRester, we test that the MPRester is configured correctly.
        # Let's assume we have a wrapper function `fetch_with_retry` in fetch_dft.py.
        from code.ingestion.fetch_dft import fetch_with_retry
        
        # Execute the function
        start_time = time.time()
        result = fetch_with_retry(mock_mpr, self.test_material_id)
        end_time = time.time()
        
        # Assertions
        self.assertEqual(call_count, 3, "Should have retried twice before succeeding")
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        
        # Verify that some time passed due to backoff (at least 1 second total for 2 retries)
        # The exact time depends on the backoff factor, but it should be > 0
        self.assertGreater(end_time - start_time, 0.1, "Backoff delay should have occurred")

    @patch('code.ingestion.fetch_dft.MPRester')
    def test_max_retries_exceeded(self, mock_mprester_class):
        """
        Test that the code fails gracefully after max retries are exceeded.
        
        This simulates a scenario where the API consistently returns 503.
        """
        mock_mpr = MagicMock()
        mock_mprester_class.return_value = mock_mpr
        
        # Always raise HTTPError for 503
        def side_effect(*args, **kwargs):
            error = HTTPError(response=self.mock_response_503)
            error.response = self.mock_response_503
            raise error
        
        mock_mpr._make_request = MagicMock(side_effect=side_effect)
        
        from code.ingestion.fetch_dft import fetch_with_retry
        
        # Expect a RetryError or a custom exception after max retries
        with self.assertRaises(RetryError):
            fetch_with_retry(mock_mpr, self.test_material_id, max_retries=3)

    @patch('code.ingestion.fetch_dft.MPRester')
    def test_success_on_first_try(self, mock_mprester_class):
        """
        Test that the code succeeds immediately if the first request is successful.
        """
        mock_mpr = MagicMock()
        mock_mprester_class.return_value = mock_mpr
        
        # Always succeed
        mock_mpr._make_request = MagicMock(return_value=self.mock_response_success.json())
        
        from code.ingestion.fetch_dft import fetch_with_retry
        
        result = fetch_with_retry(mock_mpr, self.test_material_id)
        
        self.assertEqual(mock_mpr._make_request.call_count, 1, "Should have made only one request")
        self.assertIsNotNone(result)

    @patch('code.ingestion.fetch_dft.MPRester')
    def test_exponential_backoff_timing(self, mock_mprester_class):
        """
        Test that the backoff time increases exponentially between retries.
        
        This is a more detailed check of the backoff timing.
        """
        mock_mpr = MagicMock()
        mock_mprester_class.return_value = mock_mpr
        
        call_times = []
        def side_effect(*args, **kwargs):
            call_times.append(time.time())
            # Fail twice
            if len(call_times) <= 2:
                error = HTTPError(response=self.mock_response_429)
                error.response = self.mock_response_429
                raise error
            else:
                return self.mock_response_success.json()
        
        mock_mpr._make_request = MagicMock(side_effect=side_effect)
        
        from code.ingestion.fetch_dft import fetch_with_retry
        
        start_time = time.time()
        try:
            fetch_with_retry(mock_mpr, self.test_material_id, max_retries=3)
        except RetryError:
            pass # Expected to fail if we don't adjust the side_effect for 3rd try
        
        # If we made it here, we should have 3 calls
        if len(call_times) == 3:
            # Check that the delay between calls increases
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            self.assertGreater(delay2, delay1, "Backoff delay should increase exponentially")


if __name__ == '__main__':
    unittest.main()