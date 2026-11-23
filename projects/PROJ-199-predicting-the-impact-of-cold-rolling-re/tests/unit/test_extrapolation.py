"""
Unit tests for extrapolation flagging logic.
"""

import pytest
import numpy as np
import pandas as pd

from models.extrapolation import (
    is_extrapolation,
    apply_confidence_penalty,
    flag_predictions,
    MIN_PLAUSIBLE_REDUCTION,
    MAX_PLAUSIBLE_REDUCTION,
    EXTRAPOLATION_PENALTY_FACTOR,
    NEAR_BOUNDARY_PENALTY_FACTOR
)


class TestIsExtrapolation:
    def test_within_range(self):
        """Test values well within the valid range."""
        is_ext, reason = is_extrapolation(50.0)
        assert not is_ext
        assert "safe interpolation range" in reason.lower()

    def test_below_minimum(self):
        """Test values below minimum plausible reduction."""
        is_ext, reason = is_extrapolation(-5.0)
        assert is_ext
        assert "below minimum" in reason.lower()

    def test_above_maximum(self):
        """Test values above maximum plausible reduction."""
        is_ext, reason = is_extrapolation(100.0)
        assert is_ext
        assert "above maximum" in reason.lower()

    def test_near_lower_boundary(self):
        """Test values near the lower boundary."""
        # Default min is 0.0, margin is 5.0, so 3.0 should trigger near-boundary
        is_ext, reason = is_extrapolation(3.0)
        assert not is_ext  # Not extrapolation, just near boundary
        assert "near lower boundary" in reason.lower()

    def test_near_upper_boundary(self):
        """Test values near the upper boundary."""
        # Default max is 95.0, margin is 5.0, so 92.0 should trigger near-boundary
        is_ext, reason = is_extrapolation(92.0)
        assert not is_ext
        assert "near upper boundary" in reason.lower()


class TestApplyConfidencePenalty:
    def test_no_penalty_interpolation(self):
        """Test confidence remains unchanged in safe range."""
        original_conf = 0.9
        adj_conf, reason, is_ext = apply_confidence_penalty(original_conf, 50.0)
        assert adj_conf == original_conf
        assert not is_ext
        assert "no penalty" in reason.lower()

    def test_extrapolation_penalty_applied(self):
        """Test confidence is reduced for extrapolated values."""
        original_conf = 0.9
        adj_conf, reason, is_ext = apply_confidence_penalty(original_conf, 100.0)
        expected = original_conf * EXTRAPOLATION_PENALTY_FACTOR
        assert np.isclose(adj_conf, expected)
        assert is_ext
        assert "extrapolation penalty" in reason.lower()

    def test_near_boundary_penalty_applied(self):
        """Test confidence is reduced for near-boundary values."""
        original_conf = 0.9
        adj_conf, reason, is_ext = apply_confidence_penalty(original_conf, 3.0)
        expected = original_conf * NEAR_BOUNDARY_PENALTY_FACTOR
        assert np.isclose(adj_conf, expected)
        assert not is_ext  # Near boundary is not extrapolation
        assert "near-boundary penalty" in reason.lower()


class TestFlagPredictions:
    def test_flag_predictions_dataframe(self):
        """Test flagging on a sample DataFrame."""
        data = {
            'reduction': [10.0, 50.0, 98.0, -2.0],
            'confidence': [0.9, 0.8, 0.7, 0.6]
        }
        df = pd.DataFrame(data)

        result = flag_predictions(df)

        assert 'adjusted_confidence' in result.columns
        assert 'extrapolation_flags' in result.columns

        # Check specific rows
        # Row 0: 10.0 -> safe
        assert result.iloc[0]['adjusted_confidence'] == 0.9
        assert not result.iloc[0]['extrapolation_flags']['is_extrapolation']

        # Row 2: 98.0 -> extrapolation (above 95.0)
        assert result.iloc[2]['adjusted_confidence'] < 0.7
        assert result.iloc[2]['extrapolation_flags']['is_extrapolation']

        # Row 3: -2.0 -> extrapolation (below 0.0)
        assert result.iloc[3]['adjusted_confidence'] < 0.6
        assert result.iloc[3]['extrapolation_flags']['is_extrapolation']

    def test_missing_column_raises_error(self):
        """Test that missing required columns raise ValueError."""
        data = {'reduction': [10.0]}
        df = pd.DataFrame(data)

        with pytest.raises(ValueError):
            flag_predictions(df)

    def test_custom_column_names(self):
        """Test using custom column names."""
        data = {
            'red_val': [50.0],
            'conf_score': [0.85]
        }
        df = pd.DataFrame(data)

        result = flag_predictions(
            df,
            reduction_col='red_val',
            confidence_col='conf_score',
            output_col='new_conf',
            flags_col='new_flags'
        )

        assert 'new_conf' in result.columns
        assert 'new_flags' in result.columns