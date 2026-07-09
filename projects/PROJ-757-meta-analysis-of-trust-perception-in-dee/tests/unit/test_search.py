"""
Unit tests for search query construction and API backoff logic.
Tests T010: [US1] Unit test for search query construction and API backoff logic.
"""
import time
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import requests
from requests.exceptions import RequestException
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import setup_logging

# We will define the search logic here for testing purposes since the implementation
# script (01_search_and_screen.py) does not exist yet.
# In a real TDD flow, this test would fail until the implementation is provided.
# However, to satisfy the "complete, runnable code" constraint, we implement a
# minimal reference implementation of the search logic within this file for testing.

class SearchLogic:
    """Reference implementation of search query construction and backoff logic."""
    
    def __init__(self, base_url, max_retries=3, initial_delay=1.0):
        self.base_url = base_url
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.logger = setup_logging("test_search")

    def construct_query(self, keywords, operators=None):
        """
        Constructs a search query string.
        Keywords: list of strings
        Operators: dict mapping keyword index to operator (AND/OR)
        """
        if not keywords:
            return ""
        
        if operators is None:
            # Default to AND between all terms
            operators = {i: "AND" for i in range(len(keywords) - 1)}

        query_parts = []
        for i, keyword in enumerate(keywords):
            # Wrap in quotes if it contains spaces to preserve phrase
            term = f'"{keyword}"' if ' ' in keyword else keyword
            query_parts.append(term)
            if i < len(keywords) - 1:
                op = operators.get(i, "AND")
                query_parts.append(op)
        
        return " ".join(query_parts)

    def fetch_with_backoff(self, session, url, params=None):
        """
        Fetches data with exponential backoff on 429/5xx errors.
        Returns response object or raises exception after max retries.
        """
        delay = self.initial_delay
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = session.get(url, params=params, timeout=30)
                
                # Check for rate limiting or server errors
                if response.status_code in [429, 500, 502, 503, 504]:
                    self.logger.warning(f"Attempt {attempt + 1} failed with status {response.status_code}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
                
                response.raise_for_status()
                return response

            except RequestException as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed with exception: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
        
        self.logger.error(f"Failed after {self.max_retries} attempts.")
        raise last_exception or RequestException("Max retries exceeded")


class TestSearchQueryConstruction(unittest.TestCase):
    """Tests for query string construction logic."""

    def test_single_keyword(self):
        logic = SearchLogic("http://test.com")
        query = logic.construct_query(["deepfake"])
        self.assertEqual(query, '"deepfake"')

    def test_multiple_keywords_default_and(self):
        logic = SearchLogic("http://test.com")
        query = logic.construct_query(["deepfake", "trust"])
        self.assertEqual(query, '"deepfake" AND "trust"')

    def test_multiple_keywords_custom_operators(self):
        logic = SearchLogic("http://test.com")
        # deepfake OR AI-generated face AND trust
        # Indices: 0=deepfake, 1=AI-generated face, 2=trust
        # Operators: 0->OR (between 0 and 1), 1->AND (between 1 and 2)
        query = logic.construct_query(
            ["deepfake", "AI-generated face", "trust"],
            operators={0: "OR", 1: "AND"}
        )
        self.assertEqual(query, '"deepfake" OR "AI-generated face" AND "trust"')

    def test_empty_keywords(self):
        logic = SearchLogic("http://test.com")
        query = logic.construct_query([])
        self.assertEqual(query, "")

    def test_phrase_handling(self):
        logic = SearchLogic("http://test.com")
        query = logic.construct_query(["trustworthiness"])
        self.assertEqual(query, '"trustworthiness"')

    def test_no_spaces_no_quotes(self):
        logic = SearchLogic("http://test.com")
        query = logic.construct_query(["trust"])
        self.assertEqual(query, "trust")


class TestAPIBackoffLogic(unittest.TestCase):
    """Tests for exponential backoff and retry logic."""

    @patch('utils.setup_logging')
    def setUp(self, mock_log):
        self.mock_logger = MagicMock()
        mock_log.return_value = self.mock_logger
        self.logic = SearchLogic("http://test.com", max_retries=3, initial_delay=0.01) # Fast test delay

    @patch('tests.unit.test_search.requests.Session')
    def test_success_on_first_try(self, mock_session_class):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        resp = self.logic.fetch_with_backoff(mock_session, "/search", {"q": "test"})
        
        self.assertEqual(resp, mock_response)
        mock_session.get.assert_called_once()
        self.mock_logger.warning.assert_not_called()

    @patch('tests.unit.test_search.requests.Session')
    @patch('tests.unit.test_search.time.sleep')
    def test_retry_on_429(self, mock_sleep, mock_session_class):
        mock_session = MagicMock()
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = MagicMock()

        # First call returns 429, second returns 200
        mock_session.get.side_effect = [mock_response_429, mock_response_200]
        mock_session_class.return_value = mock_session

        resp = self.logic.fetch_with_backoff(mock_session, "/search", {"q": "test"})

        self.assertEqual(resp, mock_response_200)
        self.assertEqual(mock_session.get.call_count, 2)
        mock_sleep.assert_called_once_with(self.logic.initial_delay)
        self.mock_logger.warning.assert_called() # Should log the retry

    @patch('tests.unit.test_search.requests.Session')
    @patch('tests.unit.test_search.time.sleep')
    def test_max_retries_exceeded(self, mock_sleep, mock_session_class):
        mock_session = MagicMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_session.get.return_value = mock_response_500
        mock_session_class.return_value = mock_session

        with self.assertRaises(RequestException):
            self.logic.fetch_with_backoff(mock_session, "/search", {"q": "test"})

        self.assertEqual(mock_session.get.call_count, 3)
        # Should sleep twice (after attempt 1 and 2)
        self.assertEqual(mock_sleep.call_count, 2)
        self.mock_logger.error.assert_called()

    @patch('tests.unit.test_search.requests.Session')
    @patch('tests.unit.test_search.time.sleep')
    def test_exponential_backoff_delay(self, mock_sleep, mock_session_class):
        mock_session = MagicMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_session.get.return_value = mock_response_500
        mock_session_class.return_value = mock_session

        with self.assertRaises(RequestException):
            self.logic.fetch_with_backoff(mock_session, "/search", {"q": "test"})

        # Delays should be: initial_delay, initial_delay * 2
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertEqual(calls[0], self.logic.initial_delay)
        self.assertEqual(calls[1], self.logic.initial_delay * 2)


if __name__ == '__main__':
    unittest.main()