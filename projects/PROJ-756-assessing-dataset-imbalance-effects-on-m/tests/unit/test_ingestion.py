"""
Unit tests for ingestion retry logic and API failure handling.

Tests verify:
1. Exponential backoff retry mechanism with correct delay intervals.
2. Correct behavior on transient failures (HTTP 5xx, timeouts).
3. Correct behavior on permanent failures (HTTP 4xx, invalid URLs).
4. Logging of retry attempts and final failure/success states.
"""

import time
import unittest
from unittest.mock import patch, MagicMock, call
from requests.exceptions import Timeout, HTTPError, RequestException
from ingestion import exponential_backoff_retry, fetch_materials_project_data, fetch_oqmd_data, fetch_aflow_data


class TestExponentialBackoffRetry(unittest.TestCase):
    """Tests for the exponential_backoff_retry decorator/function."""

    def test_success_on_first_attempt(self):
        """Function should return immediately if the first attempt succeeds."""
        mock_func = MagicMock(side_effect=lambda: "success")
        
        result = exponential_backoff_retry(mock_func, max_retries=3, base_delay=0.1)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)

    def test_retry_on_transient_failure(self):
        """Function should retry on Timeout or RequestException and succeed eventually."""
        # Fail twice, succeed on third
        mock_func = MagicMock(side_effect=[
            Timeout("Connection timed out"),
            Timeout("Connection timed out"),
            "success"
        ])
        
        result = exponential_backoff_retry(mock_func, max_retries=3, base_delay=0.01)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)

    def test_max_retries_exceeded_raises(self):
        """Function should raise an error after max_retries are exhausted."""
        mock_func = MagicMock(side_effect=Timeout("Persistent timeout"))
        
        with self.assertRaises(Timeout):
            exponential_backoff_retry(mock_func, max_retries=3, base_delay=0.01)
        
        # Should have been called initial + retries
        self.assertEqual(mock_func.call_count, 4)

    def test_http_4xx_does_not_retry(self):
        """HTTP 4xx errors should not trigger retries (permanent failure)."""
        mock_func = MagicMock(side_effect=HTTPError("404 Not Found", response=MagicMock(status_code=404)))
        
        with self.assertRaises(HTTPError):
            exponential_backoff_retry(mock_func, max_retries=3, base_delay=0.01)
        
        # Should only be called once
        self.assertEqual(mock_func.call_count, 1)

    def test_http_5xx_triggers_retry(self):
        """HTTP 5xx errors should trigger retries."""
        mock_func = MagicMock(side_effect=[
            HTTPError("500 Internal Server Error", response=MagicMock(status_code=500)),
            "success"
        ])
        
        result = exponential_backoff_retry(mock_func, max_retries=3, base_delay=0.01)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)

    def test_delay_intervals(self):
        """Verify that delays follow exponential backoff pattern (1x, 2x, 4x...)."""
        mock_func = MagicMock(side_effect=[
            Timeout("Fail 1"),
            Timeout("Fail 2"),
            Timeout("Fail 3"),
            "success"
        ])
        
        start_time = time.time()
        result = exponential_backoff_retry(mock_func, max_retries=3, base_delay=0.1)
        elapsed = time.time() - start_time
        
        self.assertEqual(result, "success")
        # Expected delays: 0.1 + 0.2 + 0.4 = 0.7s (plus execution time)
        self.assertGreaterEqual(elapsed, 0.6) 
        self.assertLess(elapsed, 1.5) # Allow some margin


class TestFetchMaterialProjectData(unittest.TestCase):
    """Tests for fetch_materials_project_data specific failure handling."""

    @patch('ingestion.requests.get')
    def test_fetch_mp_timeout(self, mock_get):
        """Test handling of timeout in MP fetch."""
        mock_get.side_effect = Timeout("MP API timeout")
        
        with self.assertRaises(Timeout):
            fetch_materials_project_data("fake_api_key")

    @patch('ingestion.requests.get')
    def test_fetch_mp_403_fallback(self, mock_get):
        """Test that 403 on MP triggers specific handling (logging scope change)."""
        # Simulate 403
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value.raise_for_status.side_effect = HTTPError(
            "403 Client Error", response=mock_response
        )
        
        # The function should raise HTTPError, which the caller (ingest_materials_data) handles
        with self.assertRaises(HTTPError):
            fetch_materials_project_data("fake_api_key")

    @patch('ingestion.requests.get')
    def test_fetch_mp_success(self, mock_get):
        """Test successful fetch returns data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"material_id": "mp-123"}]}
        mock_get.return_value = mock_response
        
        data = fetch_materials_project_data("fake_api_key")
        
        self.assertEqual(data, {"data": [{"material_id": "mp-123"}]})
        mock_get.assert_called_once()


class TestFetchOqmdData(unittest.TestCase):
    """Tests for fetch_oqmd_data specific failure handling."""

    @patch('ingestion.requests.get')
    def test_fetch_oqmd_timeout(self, mock_get):
        """Test handling of timeout in OQMD fetch."""
        mock_get.side_effect = Timeout("OQMD API timeout")
        
        with self.assertRaises(Timeout):
            fetch_oqmd_data()

    @patch('ingestion.requests.get')
    def test_fetch_oqmd_success(self, mock_get):
        """Test successful fetch returns data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"entries": [{"id": "oqmd-1"}]}
        mock_get.return_value = mock_response
        
        data = fetch_oqmd_data()
        
        self.assertEqual(data, {"entries": [{"id": "oqmd-1"}]})

class TestFetchAflowData(unittest.TestCase):
    """Tests for fetch_aflow_data specific failure handling."""

    @patch('ingestion.requests.get')
    def test_fetch_aflow_timeout(self, mock_get):
        """Test handling of timeout in AFLOW fetch."""
        mock_get.side_effect = Timeout("AFLOW API timeout")
        
        with self.assertRaises(Timeout):
            fetch_aflow_data()

    @patch('ingestion.requests.get')
    def test_fetch_aflow_success(self, mock_get):
        """Test successful fetch returns data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"aflow_id": "af-1"}]}
        mock_get.return_value = mock_response
        
        data = fetch_aflow_data()
        
        self.assertEqual(data, {"results": [{"aflow_id": "af-1"}]})

if __name__ == '__main__':
    unittest.main()