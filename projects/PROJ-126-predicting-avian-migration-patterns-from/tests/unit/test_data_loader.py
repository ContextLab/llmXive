"""
Unit tests for data_loader.py.
Tests the "Fail Loudly" behavior when data fetch fails.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the functions we are testing
from code.data_loader import (
    _fetch_ebird_data,
    _fetch_modis_data,
    load_ebird_data,
    load_modis_data,
)

class TestDataLoaderFailLoudly:
    """Tests that ensure the data loader fails loudly on connection errors."""

    def test_fetch_ebird_fails_on_connection_error(self):
        """
        Test that _fetch_ebird_data raises ConnectionError when the fetch fails.
        """
        with patch('code.data_loader.load_dataset', side_effect=Exception("Network Error")):
            with patch('code.data_logger.requests.get', side_effect=Exception("Connection Refused")):
                with pytest.raises(ConnectionError):
                    _fetch_ebird_data()

    def test_fetch_modis_fails_on_connection_error(self):
        """
        Test that _fetch_modis_data raises ConnectionError when the fetch fails.
        """
        with patch('code.data_loader.requests.get', side_effect=Exception("Connection Refused")):
            with pytest.raises(ConnectionError):
                _fetch_modis_data()

    def test_load_ebird_propagates_connection_error(self):
        """
        Test that load_ebird_data propagates ConnectionError from the fetch function.
        """
        with patch('code.data_loader._fetch_ebird_data', side_effect=ConnectionError("Fetch failed")):
            with pytest.raises(ConnectionError):
                load_ebird_data()

    def test_load_modis_propagates_connection_error(self):
        """
        Test that load_modis_data propagates ConnectionError from the fetch function.
        """
        with patch('code.data_loader._fetch_modis_data', side_effect=ConnectionError("Fetch failed")):
            with pytest.raises(ConnectionError):
                load_modis_data()

    def test_no_synthetic_fallback_in_ebird(self):
        """
        Test that no synthetic data is returned when fetch fails.
        This test ensures that the loader does not have a fallback to mock data.
        """
        # We expect a ConnectionError, not a dataframe with synthetic data
        with patch('code.data_loader._fetch_ebird_data', side_effect=ConnectionError("Fetch failed")):
            with pytest.raises(ConnectionError):
                load_ebird_data()
                # If we reach here, the test fails because we expected an error
                assert False, "Expected ConnectionError, but function returned data"

    def test_no_synthetic_fallback_in_modis(self):
        """
        Test that no synthetic data is returned when fetch fails.
        """
        # We expect a ConnectionError, not a dataframe with synthetic data
        with patch('code.data_loader._fetch_modis_data', side_effect=ConnectionError("Fetch failed")):
            with pytest.raises(ConnectionError):
                load_modis_data()
                # If we reach here, the test fails because we expected an error
                assert False, "Expected ConnectionError, but function returned data"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
