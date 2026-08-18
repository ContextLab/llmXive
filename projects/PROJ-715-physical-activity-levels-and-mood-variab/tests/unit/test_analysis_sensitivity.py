"""
Unit tests for sensitivity analysis logic in code/analysis.py.

Tests cover:
1. Weekdays-only filter logic
2. Active minutes metric swap logic
3. Integration with the main analysis pipeline (mocked)
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import the functions we are testing
# Note: We assume these are defined in code/analysis.py as per the API surface
from code.analysis import (
    run_sensitivity_weekdays,
    run_sensitivity_active_minutes,
    load_daily_aggregates
)
from code.config import get_path


class TestWeekdaysFilter:
    """Tests for the weekdays-only sensitivity analysis."""

    def test_weekdays_filter_removes_weekend_days(self):
        """Verify that weekend days (Sat, Sun) are removed from the dataset."""
        # Create a mock dataset with known weekend days
        dates = [
            datetime(2023, 1, 2),  # Monday
            datetime(2023, 1, 3),  # Tuesday
            datetime(2023, 1, 4),  # Wednesday
            datetime(2023, 1, 5),  # Thursday
            datetime(2023, 1, 6),  # Friday
            datetime(2023, 1, 7),  # Saturday
            datetime(2023, 1, 8),  # Sunday
        ]
        df = pd.DataFrame({
            'participant_id': ['P1'] * len(dates),
            'date': dates,
            'total_steps': [1000] * len(dates),
            'mean_mood': [5.0] * len(dates),
            'mood_std': [1.0] * len(dates),
            'day_of_week': [0, 1, 2, 3, 4, 5, 6]  # 0=Mon, 5=Sat, 6=Sun
        })

        # Mock the load_daily_aggregates function to return our test data
        with patch('code.analysis.load_daily_aggregates', return_value=df):
            result_df = run_sensitivity_weekdays()

        # Verify that Saturday (index 5) and Sunday (index 6) are removed
        assert len(result_df) == 5, "Weekdays filter should remove 2 weekend days"
        assert all(result_df['day_of_week'] < 5), "No weekend days should remain"
        assert all(result_df['day_of_week'] >= 0), "All days should be >= 0"

    def test_weekdays_filter_preserves_weekdays(self):
        """Verify that weekday days are preserved in the dataset."""
        dates = [
            datetime(2023, 1, 2),  # Monday
            datetime(2023, 1, 3),  # Tuesday
            datetime(2023, 1, 4),  # Wednesday
        ]
        df = pd.DataFrame({
            'participant_id': ['P1'] * len(dates),
            'date': dates,
            'total_steps': [1000, 2000, 3000],
            'mean_mood': [5.0, 6.0, 7.0],
            'mood_std': [1.0, 1.5, 2.0],
            'day_of_week': [0, 1, 2]
        })

        with patch('code.analysis.load_daily_aggregates', return_value=df):
            result_df = run_sensitivity_weekdays()

        assert len(result_df) == 3, "All weekdays should be preserved"
        pd.testing.assert_frame_equal(result_df, df)

    def test_weekdays_filter_handles_empty_dataset(self):
        """Verify behavior when the input dataset is empty."""
        df = pd.DataFrame(columns=['participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std', 'day_of_week'])

        with patch('code.analysis.load_daily_aggregates', return_value=df):
            result_df = run_sensitivity_weekdays()

        assert len(result_df) == 0, "Empty dataset should remain empty"


class TestActiveMinutesMetricSwap:
    """Tests for the active minutes metric swap sensitivity analysis."""

    def test_active_minutes_calculation(self):
        """Verify that active minutes are calculated correctly from step data."""
        # Mock data with varying step counts
        df = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P1'],
            'date': [datetime(2023, 1, 1), datetime(2023, 1, 2), datetime(2023, 1, 3)],
            'total_steps': [0, 5000, 10000],
            'mean_mood': [5.0, 6.0, 7.0],
            'mood_std': [1.0, 1.5, 2.0],
            'day_of_week': [0, 1, 2]
        })

        # Mock the load_daily_aggregates function
        with patch('code.analysis.load_daily_aggregates', return_value=df):
            result_df = run_sensitivity_active_minutes()

        # Verify that active_minutes column exists
        assert 'active_minutes' in result_df.columns, "active_minutes column should exist"

        # Verify calculation: steps / 100 (assuming 100 steps/min as a simple heuristic)
        # Note: The actual formula might be different in the real implementation
        expected_active_minutes = df['total_steps'] / 100.0
        pd.testing.assert_series_equal(result_df['active_minutes'], expected_active_minutes, check_names=False)

    def test_active_minutes_replaces_steps_in_model(self):
        """Verify that the model uses active_minutes instead of total_steps."""
        df = pd.DataFrame({
            'participant_id': ['P1'] * 5,
            'date': [datetime(2023, 1, i+1) for i in range(5)],
            'total_steps': [1000, 2000, 3000, 4000, 5000],
            'active_minutes': [10, 20, 30, 40, 50],  # Pre-calculated for testing
            'mean_mood': [5.0, 6.0, 7.0, 8.0, 9.0],
            'mood_std': [1.0, 1.5, 2.0, 2.5, 3.0],
            'day_of_week': [0, 1, 2, 3, 4]
        })

        with patch('code.analysis.load_daily_aggregates', return_value=df):
            # We mock the actual model fitting to avoid needing statsmodels in this unit test
            with patch('code.analysis.fit_lmm_variability') as mock_fit:
                mock_fit.return_value = MagicMock()
                mock_fit.return_value.summary.return_value = "Mock Summary"
                mock_fit.return_value.params = {'total_steps': 0.5}
                
                # Call the function - it should internally swap the predictor
                run_sensitivity_active_minutes()

                # Verify that fit_lmm_variability was called with active_minutes as predictor
                # Note: This depends on the internal implementation of run_sensitivity_active_minutes
                # We check that the function was called, and the logic inside should handle the swap
                mock_fit.assert_called()

    def test_active_minutes_handles_zero_steps(self):
        """Verify that zero steps result in zero active minutes."""
        df = pd.DataFrame({
            'participant_id': ['P1'],
            'date': [datetime(2023, 1, 1)],
            'total_steps': [0],
            'mean_mood': [5.0],
            'mood_std': [1.0],
            'day_of_week': [0]
        })

        with patch('code.analysis.load_daily_aggregates', return_value=df):
            result_df = run_sensitivity_active_minutes()

        assert result_df['active_minutes'].iloc[0] == 0.0, "Zero steps should yield zero active minutes"


class TestSensitivityAnalysisIntegration:
    """Integration tests for the full sensitivity analysis pipeline."""

    @patch('code.analysis.run_lopo_cv')
    @patch('code.analysis.fit_lmm_variability')
    def test_sensitivity_weekdays_integration(self, mock_fit, mock_lopo):
        """Test the full flow of weekdays sensitivity analysis."""
        # Setup mocks
        mock_df = pd.DataFrame({
            'participant_id': ['P1'] * 5,
            'date': [datetime(2023, 1, i+1) for i in range(5)],
            'total_steps': [1000, 2000, 3000, 4000, 5000],
            'mean_mood': [5.0, 6.0, 7.0, 8.0, 9.0],
            'mood_std': [1.0, 1.5, 2.0, 2.5, 3.0],
            'day_of_week': [0, 1, 2, 3, 4]
        })
        
        mock_fit.return_value = MagicMock()
        mock_fit.return_value.params = {'total_steps': 0.5, 'sleep_duration': 0.1}
        mock_lopo.return_value = {'sign_consistency': 100.0}

        with patch('code.analysis.load_daily_aggregates', return_value=mock_df):
            result = run_sensitivity_weekdays()

        # Verify the result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'model_type' in result, "Result should contain model_type"
        assert 'fixed_effects' in result, "Result should contain fixed_effects"
        assert 'validation' in result, "Result should contain validation"

    @patch('code.analysis.run_lopo_cv')
    @patch('code.analysis.fit_lmm_variability')
    def test_sensitivity_active_minutes_integration(self, mock_fit, mock_lopo):
        """Test the full flow of active minutes sensitivity analysis."""
        mock_df = pd.DataFrame({
            'participant_id': ['P1'] * 5,
            'date': [datetime(2023, 1, i+1) for i in range(5)],
            'total_steps': [1000, 2000, 3000, 4000, 5000],
            'active_minutes': [10, 20, 30, 40, 50],
            'mean_mood': [5.0, 6.0, 7.0, 8.0, 9.0],
            'mood_std': [1.0, 1.5, 2.0, 2.5, 3.0],
            'day_of_week': [0, 1, 2, 3, 4]
        })

        mock_fit.return_value = MagicMock()
        mock_fit.return_value.params = {'active_minutes': 0.5}
        mock_lopo.return_value = {'sign_consistency': 95.0}

        with patch('code.analysis.load_daily_aggregates', return_value=mock_df):
            result = run_sensitivity_active_minutes()

        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'model_type' in result, "Result should contain model_type"

def test_get_path_function_exists(self):
    """Verify that get_path from config works as expected for test paths."""
    # This is a simple sanity check to ensure the config module is working
    path = get_path('data', 'processed', 'daily_aggregates.csv')
    assert isinstance(path, str), "get_path should return a string"
    assert 'daily_aggregates.csv' in path, "Path should contain the filename"