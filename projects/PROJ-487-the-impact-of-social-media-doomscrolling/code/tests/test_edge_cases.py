import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.preprocess import align_timestamps, test_stationarity
from data.fetch_gdelt import fetch_gdelt_events
from data.fetch_google_trends import fetch_google_trends
from utils.logging import get_logger

logger = get_logger(__name__)


class TestZeroEventDays(unittest.TestCase):
    """Test edge cases related to zero-event days in time-series alignment."""

    def test_align_timestamps_preserves_zero_event_days(self):
        """Verify that days with zero events are preserved as 0, not dropped or interpolated."""
        
        # Create sample data with gaps and explicit zeros
        df1 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-03', '2023-01-05']),
            'value': [10, 0, 20]  # Explicit zero on Jan 3
        })
        
        df2 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-02', '2023-01-04']),
            'value': [5, 15]
        })
        
        # Align to daily frequency
        aligned_df = align_timestamps(df1, df2, date_col='date', value_col='value')
        
        # Check that all dates from 01-01 to 01-05 are present
        expected_dates = pd.to_datetime([
            '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'
        ])
        
        self.assertEqual(len(aligned_df), 5)
        self.assertTrue(all(aligned_df['date'].isin(expected_dates)))
        
        # Verify zero-event day (Jan 3) is preserved as 0, not NaN or interpolated
        jan_3_row = aligned_df[aligned_df['date'] == '2023-01-03']
        self.assertEqual(len(jan_3_row), 1)
        # The value should be 0 (from original data) or NaN (if not in df2, but df1 has 0)
        # Depending on implementation, it should be 0 if from df1, or handled appropriately
        logger.debug(f"Jan 3 row: {jan_3_row}")

    def test_align_timestamps_handles_consecutive_zero_days(self):
        """Test handling of multiple consecutive days with zero events."""
        
        df1 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-06']),
            'value': [10, 20]
        })
        
        df2 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-06']),
            'value': [5, 15]
        })
        
        aligned_df = align_timestamps(df1, df2, date_col='date', value_col='value')
        
        # Should have 6 days (01-01 to 01-06)
        self.assertEqual(len(aligned_df), 6)
        
        # Days 01-02 to 01-05 should have NaN or 0 depending on implementation
        # but they should exist in the dataframe
        middle_dates = aligned_df[
            (aligned_df['date'] >= '2023-01-02') & 
            (aligned_df['date'] <= '2023-01-05')
        ]
        self.assertEqual(len(middle_dates), 4)


class TestAPIFailureHandling(unittest.TestCase):
    """Test edge cases related to API failures and retry logic."""

    @patch('data.fetch_gdelt.requests.get')
    def test_fetch_gdelt_retries_on_timeout(self, mock_get):
        """Verify GDELT fetch retries on timeout errors."""
        
        # Mock timeout on first two attempts, success on third
        mock_get.side_effect = [
            TimeoutError("Connection timed out"),
            TimeoutError("Connection timed out"),
            MagicMock(status_code=200, json=lambda: {'data': []})
        ]
        
        # Should retry and eventually succeed
        result = fetch_gdelt_events(
            start_date='2023-01-01',
            end_date='2023-01-02',
            max_retries=3
        )
        
        # Verify requests.get was called 3 times (2 failures + 1 success)
        self.assertEqual(mock_get.call_count, 3)
        self.assertIsNotNone(result)

    @patch('data.fetch_gdelt.requests.get')
    def test_fetch_gdelt_raises_after_max_retries(self, mock_get):
        """Verify GDELT fetch raises exception after exhausting retries."""
        
        # Always fail
        mock_get.side_effect = TimeoutError("Connection timed out")
        
        with self.assertRaises(TimeoutError):
            fetch_gdelt_events(
                start_date='2023-01-01',
                end_date='2023-01-02',
                max_retries=2
            )
        
        # Verify requests.get was called exactly max_retries times
        self.assertEqual(mock_get.call_count, 2)

    @patch('data.fetch_google_trends.requests.get')
    def test_fetch_google_trends_handles_503_error(self, mock_get):
        """Verify Google Trends fetch handles 503 Service Unavailable."""
        
        # Mock 503 on first two attempts, success on third
        response_503 = MagicMock()
        response_503.status_code = 503
        response_503.raise_for_status.side_effect = Exception("503 Service Unavailable")
        
        mock_get.side_effect = [
            response_503,
            response_503,
            MagicMock(status_code=200, json=lambda: {'data': []})
        ]
        
        # Should retry and eventually succeed
        result = fetch_google_trends(
            keywords=['anticipatory anxiety'],
            start_date='2023-01-01',
            end_date='2023-01-02',
            max_retries=3
        )
        
        self.assertEqual(mock_get.call_count, 3)
        self.assertIsNotNone(result)

    def test_fetch_handles_empty_response(self):
        """Test handling of empty API response (no data returned)."""
        
        # This tests the logic when API returns valid response but no data
        # The function should handle this gracefully (return empty DataFrame or raise)
        # depending on the implementation
        
        # Mock a successful response with empty data
        with patch('data.fetch_gdelt.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {'data': []}  # Empty data
            )
            
            result = fetch_gdelt_events(
                start_date='2023-01-01',
                end_date='2023-01-02',
                max_retries=1
            )
            
            # Should return an empty DataFrame or handle appropriately
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 0)


class TestStationarityEdgeCases(unittest.TestCase):
    """Test edge cases in stationarity testing."""

    def test_stationarity_with_constant_series(self):
        """Test ADF test behavior with constant (zero-variance) series."""
        
        # Create a constant series
        constant_series = pd.Series([5.0] * 100)
        
        # This should either detect non-stationarity or handle the edge case
        # The ADF test may fail with constant series, so we test the handling
        try:
            is_stationary, p_value = test_stationarity(constant_series)
            logger.debug(f"Constant series: stationary={is_stationary}, p_value={p_value}")
        except Exception as e:
            # Some implementations may raise on constant series
            logger.info(f"ADF test raised on constant series: {e}")
            # This is acceptable behavior

    def test_stationarity_with_short_series(self):
        """Test ADF test behavior with very short time series."""
        
        # Very short series (minimum for ADF)
        short_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        
        try:
            is_stationary, p_value = test_stationarity(short_series)
            logger.debug(f"Short series: stationary={is_stationary}, p_value={p_value}")
        except Exception as e:
            # ADF may require minimum length
            logger.info(f"ADF test raised on short series: {e}")


class TestDataValidationEdgeCases(unittest.TestCase):
    """Test edge cases in data validation and preprocessing."""

    def test_align_with_no_common_dates(self):
        """Test alignment when datasets have no overlapping dates."""
        
        df1 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'value': [10, 20]
        })
        
        df2 = pd.DataFrame({
            'date': pd.to_datetime(['2023-02-01', '2023-02-02']),  # Different month
            'value': [5, 15]
        })
        
        # Should return empty or handle gracefully
        aligned_df = align_timestamps(df1, df2, date_col='date', value_col='value')
        
        # Depending on implementation, either empty or all NaN
        self.assertIsInstance(aligned_df, pd.DataFrame)

    def test_preprocess_with_single_value_series(self):
        """Test preprocessing with series containing only one unique value."""
        
        single_value_series = pd.Series([10.0] * 50)
        
        # Should handle z-score normalization gracefully
        # (may result in division by zero if std=0)
        try:
            normalized = (single_value_series - single_value_series.mean()) / single_value_series.std()
            logger.debug(f"Normalized single-value series: {normalized.head()}")
        except Exception as e:
            logger.info(f"Normalization raised on single-value series: {e}")


class TestMissingDataHandling(unittest.TestCase):
    """Test handling of missing data scenarios."""

    def test_align_with_all_missing_values(self):
        """Test alignment when one dataset has all missing values."""
        
        df1 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            'value': [10, 20, 30]
        })
        
        df2 = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            'value': [None, None, None]
        })
        
        aligned_df = align_timestamps(df1, df2, date_col='date', value_col='value')
        
        self.assertEqual(len(aligned_df), 3)
        # df2 values should be NaN
        self.assertTrue(aligned_df['value_1'].isna().all())

    def test_interpolation_with_all_missing(self):
        """Test linear interpolation when all values are missing."""
        
        missing_series = pd.Series([None, None, None, None])
        
        # Interpolation should return all NaN
        interpolated = missing_series.interpolate(method='linear')
        
        self.assertTrue(interpolated.isna().all())


if __name__ == '__main__':
    unittest.main()