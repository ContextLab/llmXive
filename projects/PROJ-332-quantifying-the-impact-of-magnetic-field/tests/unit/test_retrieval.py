"""
Unit tests for MDSplus connection retry logic in code/data/retrieval.py.

This module verifies that the retrieval logic correctly implements:
1. Multiple connection attempts on failure
2. Fixed time intervals between retries
3. Proper exception handling and logging
"""
import unittest
from unittest.mock import patch, MagicMock, call
import time
import logging
from typing import Dict, Any, List, Tuple, Optional

# Import the functions under test
from code.data.retrieval import (
    get_efit_data, 
    fetch_island_width, 
    fetch_data_for_discharge,
    derive_island_width
)
from code.utils.logger import get_logger
from code.utils.limits import timeout_guard, TimeoutError

class TestMDSplusRetryLogic(unittest.TestCase):
    """Test cases for MDSplus connection retry mechanisms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_logger(__name__)
        self.discharge_id = 165432
        self.max_retries = 3
        self.retry_delay = 0.1  # Short delay for testing
        
        # Mock data structure for successful retrieval
        self.mock_efit_data = {
            'q_profile': [0.8, 1.2, 1.5, 2.0],
            'r_major': 1.67,
            'b_toroidal': 2.1,
            'plasma_current': 1.4e6,
            'local_shear': 1.5,
            'minor_radius': 0.67
        }
        
        self.mock_island_width = 0.005  # 5mm
        
        # Configure logging for tests
        logging.basicConfig(level=logging.INFO)

    @patch('code.data.retrieval._connect_to_mdsplus')
    def test_successful_connection_on_first_attempt(self, mock_connect):
        """Test that a successful connection on first attempt returns data immediately."""
        # Setup mock to succeed immediately
        mock_conn = MagicMock()
        mock_conn.connect.return_value = True
        mock_conn.get.return_value = self.mock_efit_data
        mock_connect.return_value = mock_conn
        
        # Execute
        with patch('time.sleep'):  # Skip actual sleep in tests
            result = get_efit_data(self.discharge_id, max_retries=self.max_retries, retry_delay=self.retry_delay)
        
        # Verify
        self.assertEqual(result, self.mock_efit_data)
        mock_connect.assert_called_once()
        mock_conn.get.assert_called_once()

    @patch('code.data.retrieval._connect_to_mdsplus')
    def test_retry_on_connection_failure(self, mock_connect):
        """Test that connection failures trigger retry logic with proper delays."""
        # Setup mock to fail twice, then succeed
        mock_conn = MagicMock()
        mock_conn.connect.side_effect = [
            ConnectionError("Connection refused"),
            ConnectionError("Connection refused"),
            True  # Success on third attempt
        ]
        mock_conn.get.return_value = self.mock_efit_data
        mock_connect.return_value = mock_conn
        
        # Execute
        with patch('time.sleep') as mock_sleep:
            result = get_efit_data(self.discharge_id, max_retries=self.max_retries, retry_delay=self.retry_delay)
        
        # Verify
        self.assertEqual(result, self.mock_efit_data)
        self.assertEqual(mock_conn.connect.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Sleep before 2nd and 3rd attempt
        mock_sleep.assert_has_calls([call(self.retry_delay), call(self.retry_delay)])

    @patch('code.data.retrieval._connect_to_mdsplus')
    def test_max_retries_exceeded_raises_exception(self, mock_connect):
        """Test that exceeding max retries raises an appropriate exception."""
        # Setup mock to always fail
        mock_conn = MagicMock()
        mock_conn.connect.side_effect = ConnectionError("Connection refused")
        mock_connect.return_value = mock_conn
        
        # Execute and verify exception
        with patch('time.sleep'):
            with self.assertRaises(ConnectionError):
                get_efit_data(self.discharge_id, max_retries=2, retry_delay=self.retry_delay)
        
        # Verify retry count
        self.assertEqual(mock_conn.connect.call_count, 2)

    @patch('code.data.retrieval.get_efit_data')
    def test_fetch_island_width_with_retry(self, mock_get_efit):
        """Test island width fetching with retry logic."""
        # Setup mock to fail once, then succeed
        mock_get_efit.side_effect = [
            ConnectionError("Temporary failure"),
            self.mock_efit_data
        ]
        
        # Mock the derive function
        with patch('code.data.retrieval.derive_island_width', return_value=self.mock_island_width):
            with patch('time.sleep'):
                result = fetch_island_width(self.discharge_id, max_retries=2, retry_delay=self.retry_delay)
        
        # Verify
        self.assertEqual(result, self.mock_island_width)
        self.assertEqual(mock_get_efit.call_count, 2)

    @patch('code.data.retrieval._connect_to_mdsplus')
    def test_fixed_delay_between_retries(self, mock_connect):
        """Test that retries use fixed time intervals, not exponential backoff."""
        mock_conn = MagicMock()
        mock_conn.connect.side_effect = [
            ConnectionError("Fail 1"),
            ConnectionError("Fail 2"),
            True
        ]
        mock_conn.get.return_value = self.mock_efit_data
        mock_connect.return_value = mock_conn
        
        # Track actual sleep times
        actual_sleep_times = []
        original_sleep = time.sleep
        def track_sleep(duration):
            actual_sleep_times.append(duration)
            original_sleep(0)  # Don't actually sleep
        
        with patch('time.sleep', side_effect=track_sleep):
            get_efit_data(self.discharge_id, max_retries=3, retry_delay=0.5)
        
        # Verify all delays are equal (fixed interval)
        self.assertEqual(len(actual_sleep_times), 2)
        self.assertEqual(actual_sleep_times[0], 0.5)
        self.assertEqual(actual_sleep_times[1], 0.5)

    @patch('code.data.retrieval.get_efit_data')
    def test_fetch_data_for_discharge_retry_logic(self, mock_get_efit):
        """Test the main fetch function's retry behavior."""
        # Setup: fail twice, succeed on third
        mock_get_efit.side_effect = [
            ConnectionError("Network issue"),
            ConnectionError("Network issue"),
            self.mock_efit_data
        ]
        
        with patch('time.sleep'):
            result = fetch_data_for_discharge(
                self.discharge_id, 
                fields=['q_profile', 'b_toroidal'],
                max_retries=3,
                retry_delay=self.retry_delay
            )
        
        # Verify
        self.assertEqual(result, self.mock_efit_data)
        self.assertEqual(mock_get_efit.call_count, 3)

    @patch('code.data.retrieval.get_efit_data')
    def test_timeout_handling_during_retry(self, mock_get_efit):
        """Test that timeout errors are handled as retryable failures."""
        # Setup: timeout twice, then success
        mock_get_efit.side_effect = [
            TimeoutError("Read timeout"),
            TimeoutError("Read timeout"),
            self.mock_efit_data
        ]
        
        with patch('time.sleep'):
            result = get_efit_data(self.discharge_id, max_retries=3, retry_delay=self.retry_delay)
        
        # Verify retry occurred
        self.assertEqual(result, self.mock_efit_data)
        self.assertEqual(mock_get_efit.call_count, 3)

    def test_derive_island_width_with_valid_inputs(self):
        """Test island width derivation with valid EFIT data."""
        efit_data = {
            'q_profile': [0.8, 1.2, 1.5, 2.0],
            'r_major': 1.67,
            'b_toroidal': 2.1,
            'plasma_current': 1.4e6,
            'local_shear': 1.5,
            'minor_radius': 0.67
        }
        
        result = derive_island_width(efit_data)
        
        # Verify result is a positive float
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
        self.assertLess(result, efit_data['minor_radius'])

    @patch('code.data.retrieval.get_logger')
    def test_logging_on_retry_attempts(self, mock_get_logger):
        """Test that retry attempts are properly logged."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        mock_connect = MagicMock()
        mock_connect.connect.side_effect = [
            ConnectionError("Fail 1"),
            True
        ]
        mock_connect.get.return_value = self.mock_efit_data
        
        with patch('code.data.retrieval._connect_to_mdsplus', return_value=mock_connect):
            with patch('time.sleep'):
                get_efit_data(self.discharge_id, max_retries=2, retry_delay=self.retry_delay)
        
        # Verify log messages were created for retry
        # The logger should have been called with retry information
        self.assertTrue(mock_logger.info.called or mock_logger.warning.called)

if __name__ == '__main__':
    unittest.main()
