import unittest
from unittest.mock import patch, MagicMock
import time
import requests
import sys
import os
import csv
import tempfile
import json

# Add the project code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingestion import fetch_osf_data_with_backoff, parse_study_metadata, IngestionError
from config import MAX_ITERATIONS

class TestOSFBackoffLogic(unittest.TestCase):
    """
    Unit tests for the OSF API backoff logic in ingestion.py.
    
    Tests verify:
    1. Successful requests return immediately without delay.
    2. 429 errors trigger exponential backoff with correct delays.
    3. Max retries are respected and raise an exception if exceeded.
    4. Non-429 errors are handled (re-raised or skipped based on implementation).
    """

    def setUp(self):
        self.osf_id = "abc123"
        self.test_url = "https://osf.io/api/v1/projects/abc123/files"
        self.max_retries = 3
        self.base_delay = 1.0  # Using 1s for testing speed, config might differ

    @patch('ingestion.requests.get')
    def test_successful_request_no_delay(self, mock_get):
        """Test that a successful 200 response returns immediately."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        start_time = time.time()
        result = fetch_osf_data_with_backoff(
            self.test_url, 
            max_retries=self.max_retries, 
            base_delay=self.base_delay
        )
        elapsed = time.time() - start_time

        mock_get.assert_called_once()
        self.assertEqual(result, {"data": []})
        # Should not wait for backoff
        self.assertLess(elapsed, 0.1)

    @patch('ingestion.requests.get')
    def test_429_triggers_exponential_backoff(self, mock_get):
        """Test that 429 errors cause exponential backoff delays."""
        # Setup mock to return 429 twice, then 200
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {'Retry-After': '1'}
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": [1, 2, 3]}

        mock_get.side_effect = [
            mock_response_429, 
            mock_response_429, 
            mock_response_200
        ]

        start_time = time.time()
        # We expect 2 retries (3 total calls)
        # Delays: 1s, 2s (approx, depending on implementation logic)
        result = fetch_osf_data_with_backoff(
            self.test_url, 
            max_retries=self.max_retries, 
            base_delay=0.1  # Use small delay for unit test speed
        )
        elapsed = time.time() - start_time

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(result, {"data": [1, 2, 3]})
        # Should have waited for backoff (approx 0.1 + 0.2 = 0.3s)
        self.assertGreaterEqual(elapsed, 0.25)

    @patch('ingestion.requests.get')
    def test_max_retries_exceeded_raises_error(self, mock_get):
        """Test that exceeding max retries raises a RuntimeError."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {}
        
        # Always return 429
        mock_get.return_value = mock_response_429

        with self.assertRaises(RuntimeError) as context:
            fetch_osf_data_with_backoff(
                self.test_url, 
                max_retries=2, # 1 initial + 2 retries = 3 calls
                base_delay=0.01
            )

        self.assertIn("Max retries exceeded", str(context.exception))
        self.assertEqual(mock_get.call_count, 3)

    @patch('ingestion.requests.get')
    def test_non_429_error_raises_immediately(self, mock_get):
        """Test that non-429 errors (e.g., 404, 500) are not retried."""
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_get.return_value = mock_response_404

        # Depending on implementation, this might raise HTTPError or return None
        # Assuming the ingestion logic raises for non-429s or handles them specifically
        # For this test, we verify it doesn't loop infinitely on non-429
        try:
            fetch_osf_data_with_backoff(
                self.test_url,
                max_retries=self.max_retries,
                base_delay=self.base_delay
            )
            # If it returns, it handled the error gracefully (e.g. returned None)
            # But typically 404/500 should raise or be handled differently than 429
        except requests.HTTPError:
            pass # Expected behavior for 404

        # Ensure it didn't retry 3 times for a 404 (should be 1 call)
        # If the logic retries all errors, this test needs adjustment to match spec
        # Spec says "429 backoff", implying other errors might be fatal or handled differently.
        # Assuming strict 429 backoff:
        self.assertEqual(mock_get.call_count, 1)

class TestParsingMissingPValue(unittest.TestCase):
    """
    Unit tests for parsing logic specifically handling missing or malformed p-values.
    
    Tests verify:
    1. Valid metadata with p-value parses correctly.
    2. Missing p-value in metadata triggers 'missing_p_value' flag.
    3. Non-numeric p-value triggers 'ambiguous_model' or 'missing_p_value'.
    4. Missing required fields (osf_id, discipline) raise IngestionError.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_parse_valid_metadata(self):
        """Test parsing metadata with a valid p-value."""
        raw_data = {
            "osf_id": "valid123",
            "discipline": "psychology",
            "title": "Test Study",
            "p_value": 0.03,
            "sample_size": 150,
            "model_description": "t-test"
        }
        
        result = parse_study_metadata(raw_data)
        
        self.assertEqual(result['osf_id'], 'valid123')
        self.assertEqual(result['discipline'], 'psychology')
        self.assertEqual(result['original_p_value'], 0.03)
        self.assertEqual(result['sample_size'], 150)
        self.assertIsNone(result.get('flags'))

    def test_parse_missing_p_value_field(self):
        """Test parsing when p_value key is absent."""
        raw_data = {
            "osf_id": "missing_p",
            "discipline": "economics",
            "title": "No P Study",
            "sample_size": 200
        }
        
        result = parse_study_metadata(raw_data)
        
        self.assertEqual(result['osf_id'], 'missing_p')
        self.assertIsNone(result['original_p_value'])
        self.assertIn('missing_p_value', result.get('flags', []))

    def test_parse_null_p_value(self):
        """Test parsing when p_value is explicitly null."""
        raw_data = {
            "osf_id": "null_p",
            "discipline": "biology",
            "title": "Null P Study",
            "p_value": None,
            "sample_size": 100
        }
        
        result = parse_study_metadata(raw_data)
        
        self.assertIsNone(result['original_p_value'])
        self.assertIn('missing_p_value', result.get('flags', []))

    def test_parse_non_numeric_p_value(self):
        """Test parsing when p_value is a string or invalid format."""
        raw_data = {
            "osf_id": "bad_p",
            "discipline": "psychology",
            "title": "Bad P Study",
            "p_value": "p < 0.05",
            "sample_size": 120
        }
        
        result = parse_study_metadata(raw_data)
        
        self.assertIsNone(result['original_p_value'])
        self.assertIn('ambiguous_model', result.get('flags', []))

    def test_parse_missing_required_fields(self):
        """Test parsing when required fields like osf_id are missing."""
        raw_data = {
            "discipline": "psychology",
            "p_value": 0.05
        }
        
        with self.assertRaises(IngestionError) as context:
            parse_study_metadata(raw_data)
        
        self.assertIn("Missing required field: osf_id", str(context.exception))

    def test_parse_missing_discipline(self):
        """Test parsing when discipline is missing."""
        raw_data = {
            "osf_id": "no_disc",
            "p_value": 0.05
        }
        
        with self.assertRaises(IngestionError) as context:
            parse_study_metadata(raw_data)
        
        self.assertIn("Missing required field: discipline", str(context.exception))

    def test_parse_empty_string_p_value(self):
        """Test parsing when p_value is an empty string."""
        raw_data = {
            "osf_id": "empty_p",
            "discipline": "economics",
            "p_value": "",
            "sample_size": 80
        }
        
        result = parse_study_metadata(raw_data)
        
        self.assertIsNone(result['original_p_value'])
        self.assertIn('ambiguous_model', result.get('flags', []))

    def test_parse_p_value_out_of_range(self):
        """Test parsing when p_value is outside [0, 1]."""
        raw_data = {
            "osf_id": "out_range",
            "discipline": "biology",
            "p_value": 1.5,
            "sample_size": 90
        }
        
        result = parse_study_metadata(raw_data)
        
        # Depending on strictness, this might be flagged or clamped.
        # Spec implies we want to detect "ambiguous" or "missing" for bad data.
        # We'll flag it as ambiguous if it's not a valid probability.
        self.assertIsNone(result['original_p_value'])
        self.assertIn('ambiguous_model', result.get('flags', []))

if __name__ == '__main__':
    unittest.main()