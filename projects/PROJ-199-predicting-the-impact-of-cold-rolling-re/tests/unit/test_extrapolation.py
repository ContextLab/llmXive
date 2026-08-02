"""
Unit tests for extrapolation flagging module (T028).
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.extrapolation import (
    get_plausible_reduction_range,
    calculate_confidence_penalty,
    flag_extrapolation,
    validate_prediction_bounds
)
from config import ConfigurationError


class TestGetPlausibleReductionRange:
    """Tests for get_plausible_reduction_range function."""

    @patch('code.models.extrapolation.get_reductions')
    def test_returns_correct_range_with_reductions(self, mock_get_reductions):
        """Test that function returns correct range with valid reductions."""
        mock_get_reductions.return_value = [10, 20, 30, 40, 50]

        min_val, max_val = get_plausible_reduction_range()

        # Expected: 10 * 0.9 = 9.0, 50 * 1.1 = 55.0
        assert abs(min_val - 9.0) < 0.01
        assert abs(max_val - 55.0) < 0.01

    @patch('code.models.extrapolation.get_reductions')
    def test_raises_error_when_no_reductions(self, mock_get_reductions):
        """Test that function raises ConfigurationError when no reductions."""
        mock_get_reductions.return_value = []

        with pytest.raises(ConfigurationError, match="No reduction levels defined"):
            get_plausible_reduction_range()

    @patch('code.models.extrapolation.get_reductions')
    def test_raises_error_when_none_reductions(self, mock_get_reductions):
        """Test that function raises ConfigurationError when reductions is None."""
        mock_get_reductions.return_value = None

        with pytest.raises(ConfigurationError, match="No reduction levels defined"):
            get_plausible_reduction_range()


class TestCalculateConfidencePenalty:
    """Tests for calculate_confidence_penalty function."""

    def test_zero_penalty_inside_range(self):
        """Test that penalty is zero inside plausible range."""
        penalty = calculate_confidence_penalty(30.0, (20.0, 40.0))
        assert penalty == 0.0

    def test_positive_penalty_below_range(self):
        """Test that penalty is positive when below range."""
        penalty = calculate_confidence_penalty(10.0, (20.0, 40.0), penalty_factor=0.1)
        # Distance = 20 - 10 = 10, penalty = 10 * 0.1 = 1.0
        assert abs(penalty - 1.0) < 0.01

    def test_positive_penalty_above_range(self):
        """Test that penalty is positive when above range."""
        penalty = calculate_confidence_penalty(50.0, (20.0, 40.0), penalty_factor=0.1)
        # Distance = 50 - 40 = 10, penalty = 10 * 0.1 = 1.0
        assert abs(penalty - 1.0) < 0.01

    def test_penalty_capped_at_one(self):
        """Test that penalty is capped at 1.0."""
        # Very large distance should still result in penalty <= 1.0
        penalty = calculate_confidence_penalty(200.0, (20.0, 40.0), penalty_factor=0.1)
        assert penalty <= 1.0

    def test_custom_penalty_factor(self):
        """Test that custom penalty factor is applied correctly."""
        penalty = calculate_confidence_penalty(10.0, (20.0, 40.0), penalty_factor=0.05)
        # Distance = 10, penalty = 10 * 0.05 = 0.5
        assert abs(penalty - 0.5) < 0.01


class TestFlagExtrapolation:
    """Tests for flag_extrapolation function."""

    @patch('code.models.extrapolation.get_plausible_reduction_range')
    def test_flags_extrapolated_predictions(self, mock_get_range):
        """Test that extrapolated predictions are correctly flagged."""
        mock_get_range.return_value = (20.0, 40.0)

        data = {
            'reduction': [10.0, 30.0, 50.0],
            'confidence': [0.9, 0.8, 0.7]
        }
        df = pd.DataFrame(data)

        result = flag_extrapolation(df)

        # First and third should be flagged
        assert result['is_extrapolation'].iloc[0] is True
        assert result['is_extrapolation'].iloc[1] is False
        assert result['is_extrapolation'].iloc[2] is True

        # Penalties should be non-zero for flagged
        assert result['extrapolation_penalty'].iloc[0] > 0
        assert result['extrapolation_penalty'].iloc[1] == 0.0
        assert result['extrapolation_penalty'].iloc[2] > 0

    @patch('code.models.extrapolation.get_plausible_reduction_range')
    def test_adjusts_confidence_when_present(self, mock_get_range):
        """Test that confidence is adjusted when confidence column exists."""
        mock_get_range.return_value = (20.0, 40.0)

        data = {
            'reduction': [10.0, 30.0],
            'confidence': [0.9, 0.8]
        }
        df = pd.DataFrame(data)

        result = flag_extrapolation(df)

        # Adjusted confidence should exist
        assert 'confidence_adjusted' in result.columns

        # First row should have lower adjusted confidence
        assert result['confidence_adjusted'].iloc[0] < result['confidence'].iloc[0]
        # Second row should be unchanged (inside range)
        assert result['confidence_adjusted'].iloc[1] == result['confidence'].iloc[1]


class TestValidatePredictionBounds:
    """Tests for validate_prediction_bounds function."""

    @patch('code.models.extrapolation.get_plausible_reduction_range')
    def test_validation_passes_when_all_in_bounds(self, mock_get_range):
        """Test validation passes when all predictions are in bounds."""
        mock_get_range.return_value = (20.0, 40.0)

        data = {
            'reduction': [25.0, 30.0, 35.0]
        }
        df = pd.DataFrame(data)

        results = validate_prediction_bounds(df)

        assert results['validation_passed'] is True
        assert results['in_bounds'] == 3
        assert results['below_min'] == 0
        assert results['above_max'] == 0

    @patch('code.models.extrapolation.get_plausible_reduction_range')
    def test_validation_fails_when_out_of_bounds(self, mock_get_range):
        """Test validation fails when predictions are out of bounds."""
        mock_get_range.return_value = (20.0, 40.0)

        data = {
            'reduction': [10.0, 50.0, 30.0]  # 10 below, 50 above
        }
        df = pd.DataFrame(data)

        results = validate_prediction_bounds(df)

        assert results['validation_passed'] is False
        assert results['below_min'] == 1
        assert results['above_max'] == 1
        assert results['in_bounds'] == 1

    @patch('code.models.extrapolation.get_plausible_reduction_range')
    def test_handles_empty_dataframe(self, mock_get_range):
        """Test validation handles empty dataframe gracefully."""
        mock_get_range.return_value = (20.0, 40.0)

        df = pd.DataFrame(columns=['reduction'])

        results = validate_prediction_bounds(df)

        assert results['validation_passed'] is False
        assert results['reason'] == "No predictions to validate"