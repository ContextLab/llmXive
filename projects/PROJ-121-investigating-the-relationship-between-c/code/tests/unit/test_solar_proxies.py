"""
Unit tests for solar_proxies module.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import time
from src.solar_proxies import (
    fetch_solar_proxy,
    _calculate_backoff,
    _fetch_text_with_retry,
    _parse_silso_sunspot,
    _parse_noaa_sw_data
)
import requests


class TestFetchWithBackoff:
    """Tests for exponential backoff and retry logic."""

    def test_calculate_backoff_first_attempt(self):
        """Test backoff calculation for the first attempt (0)."""
        delay = _calculate_backoff(0)
        # Base delay is 1.0, plus jitter (10% of 1.0 = 0.1)
        # Delay should be between 1.0 and 1.1
        assert 1.0 <= delay <= 1.1

    def test_calculate_backoff_second_attempt(self):
        """Test backoff calculation for the second attempt (1)."""
        delay = _calculate_backoff(1)
        # Base delay 2.0, plus jitter
        assert 2.0 <= delay <= 2.2

    def test_calculate_backoff_exceeds_max(self):
        """Test that backoff does not exceed MAX_DELAY."""
        # MAX_DELAY is 10.0
        delay = _calculate_backoff(10) # 2^10 is way larger than 10
        assert delay <= 10.0

    @patch('src.solar_proxies.time.sleep')
    @patch('src.solar_proxies.requests.Session.get')
    def test_fetch_with_retry_success(self, mock_get, mock_sleep):
        """Test that fetch succeeds on first try."""
        mock_response = MagicMock()
        mock_response.text = "data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _fetch_text_with_retry("http://example.com")
        assert result == "data"
        mock_get.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('src.solar_proxies.time.sleep')
    @patch('src.solar_proxies.requests.Session.get')
    def test_fetch_with_retry_failure_then_success(self, mock_get, mock_sleep):
        """Test retry logic: fails first, succeeds second."""
        mock_response = MagicMock()
        mock_response.text = "data"
        mock_response.raise_for_status = MagicMock()

        # First call raises, second succeeds
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            mock_response
        ]

        result = _fetch_text_with_retry("http://example.com")
        assert result == "data"
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once() # Should sleep once

    @patch('src.solar_proxies.time.sleep')
    @patch('src.solar_proxies.requests.Session.get')
    def test_fetch_with_retry_max_attempts(self, mock_get, mock_sleep):
        """Test that fetch raises after MAX_RETRIES (3) attempts."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(requests.exceptions.ConnectionError):
            _fetch_text_with_retry("http://example.com")

        # Should have tried 3 times
        assert mock_get.call_count == 3
        # Should have slept twice (after 1st and 2nd failure)
        assert mock_sleep.call_count == 2


class TestFetchSolarProxy:
    """Tests for the main fetch_solar_proxy function."""

    @patch('src.solar_proxies._fetch_text_with_retry')
    def test_fetch_sunspot(self, mock_fetch):
        """Test fetching sunspot data."""
        mock_fetch.return_value = """2020 1 1 50 10 0 0 0 0 0 0 0 0 0 0 0 0 0
        2020 1 2 60 10 0 0 0 0 0 0 0 0 0 0 0 0 0
        # Comment
        2020 1 3 -1 10 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        """
        data = fetch_solar_proxy('sunspot', start_date=datetime(2020, 1, 1))
        assert len(data) == 3
        assert data[0]['date'] == datetime(2020, 1, 1)
        assert data[0]['sunspot_number'] == 50.0
        assert data[2]['sunspot_number'] is None # -1.0 should be None

    @patch('src.solar_proxies._fetch_text_with_retry')
    def test_fetch_invalid_type(self, mock_fetch):
        """Test that invalid proxy type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid proxy_type"):
            fetch_solar_proxy('invalid_type')

    @patch('src.solar_proxies._fetch_text_with_retry')
    def test_fetch_solar_wind(self, mock_fetch):
        """Test fetching solar wind data."""
        # Mock a simplified tabular response
        mock_fetch.return_value = """
        # Header
        2020 1 1 12 0 0 400.0 5.0 1.0
        2020 1 1 13 0 0 410.0 5.0 1.0
        2020 1 2 12 0 0 420.0 5.0 1.0
        """
        data = fetch_solar_proxy('solar_wind', start_date=datetime(2020, 1, 1))
        # Should aggregate 12 and 13 hour entries for Jan 1
        assert len(data) == 2 # Jan 1 and Jan 2
        # Jan 1 average should be (400+410)/2 = 405
        assert data[0]['date'] == datetime(2020, 1, 1)
        assert data[0]['solar_wind_speed'] == 405.0

    @patch('src.solar_proxies._fetch_text_with_retry')
    def test_fetch_imf(self, mock_fetch):
        """Test fetching IMF data."""
        mock_fetch.return_value = """
        # Header
        2020 1 1 12 0 0 5.0 1.0
        2020 1 2 12 0 0 6.0 1.0
        """
        data = fetch_solar_proxy('imf', start_date=datetime(2020, 1, 1))
        assert len(data) == 2
        assert data[0]['imf_bt'] == 5.0
        assert data[1]['imf_bt'] == 6.0

class TestParsers:
    """Tests for parsing functions."""

    def test_parse_silso_sunspot_empty(self):
        """Test parsing empty string."""
        result = _parse_silso_sunspot("")
        assert result == []

    def test_parse_silso_sunspot_comments(self):
        """Test parsing ignores comments."""
        text = "# This is a comment\n2020 1 1 50 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
        result = _parse_silso_sunspot(text)
        assert len(result) == 1
        assert result[0]['date'] == datetime(2020, 1, 1)

    def test_parse_noaa_sw_data_empty(self):
        """Test parsing empty NOAA data."""
        result = _parse_noaa_sw_data("", "solar_wind_speed")
        assert result == []
    
    def test_parse_noaa_sw_data_missing_value(self):
        """Test handling of missing values (-999.0)."""
        text = "2020 1 1 12 0 0 -999.0 1.0"
        result = _parse_noaa_sw_data(text, "solar_wind_speed")
        assert len(result) == 1
        assert result[0]['solar_wind_speed'] is None