"""
Unit tests for Elo probability and outcome deviation calculations.
"""
import pytest
import pandas as pd
import numpy as np
from src.data.process import (
    calculate_elo_expected_prob,
    calculate_outcome_deviation,
    process_game_record,
    PROBABILITY_MIN,
    PROBABILITY_MAX
)


class TestEloExpectedProb:
    """Tests for Elo expected probability calculation."""

    def test_equal_ratings(self):
        """When ratings are equal, expected probability should be 0.5."""
        prob = calculate_elo_expected_prob(1500, 1500)
        assert prob == 0.5

    def test_100_point_advantage(self):
        """White with 100 point advantage should have ~0.64 probability."""
        # Expected: 1 / (1 + 10^(-100/400)) = 1 / (1 + 10^(-0.25)) ≈ 0.640
        prob = calculate_elo_expected_prob(1600, 1500)
        assert 0.63 < prob < 0.65

    def test_100_point_disadvantage(self):
        """White with 100 point disadvantage should have ~0.36 probability."""
        prob = calculate_elo_expected_prob(1500, 1600)
        assert 0.35 < prob < 0.37

    def test_large_rating_difference(self):
        """Large rating difference should yield probability near bounds."""
        prob_high = calculate_elo_expected_prob(2500, 1500)
        prob_low = calculate_elo_expected_prob(1500, 2500)
        
        assert prob_high > 0.95
        assert prob_low < 0.05

    def test_probability_capping_upper(self):
        """Probability should be capped at 0.99 for extreme ratings."""
        # 3000 vs 0 rating difference
        prob = calculate_elo_expected_prob(3000, 0)
        assert prob <= PROBABILITY_MAX

    def test_probability_capping_lower(self):
        """Probability should be capped at 0.01 for extreme ratings."""
        prob = calculate_elo_expected_prob(0, 3000)
        assert prob >= PROBABILITY_MIN

    def test_float_ratings(self):
        """Should handle float ratings correctly."""
        prob = calculate_elo_expected_prob(1500.5, 1500.5)
        assert prob == 0.5


class TestOutcomeDeviation:
    """Tests for outcome deviation calculation."""

    def test_white_win_expected(self):
        """White wins when expected: deviation = 1 - expected."""
        deviation = calculate_outcome_deviation(1.0, 0.7)
        assert deviation == 0.3

    def test_white_loss_expected(self):
        """White loses when expected: deviation = 0 - expected."""
        deviation = calculate_outcome_deviation(0.0, 0.3)
        assert deviation == -0.3

    def test_draw_expected(self):
        """Draw when expected 0.5: deviation = 0."""
        deviation = calculate_outcome_deviation(0.5, 0.5)
        assert deviation == 0.0

    def test_draw_not_expected(self):
        """Draw when expected 0.7: deviation = 0.5 - 0.7 = -0.2."""
        deviation = calculate_outcome_deviation(0.5, 0.7)
        assert deviation == -0.2

    def test_upset_win(self):
        """Upset win: white wins with low expected probability."""
        deviation = calculate_outcome_deviation(1.0, 0.1)
        assert deviation == 0.9


class TestProcessGameRecord:
    """Tests for the full processing pipeline."""

    def test_process_dataframe(self):
        """Test processing a valid DataFrame."""
        data = {
            'white_rating': [1500, 1600, 1500],
            'black_rating': [1500, 1500, 1600],
            'outcome': ['1-0', '1/2-1/2', '0-1']
        }
        df = pd.DataFrame(data)
        
        result = process_game_record(df)
        
        assert 'elo_expected_prob' in result.columns
        assert 'outcome_deviation' in result.columns
        assert 'actual_result' in result.columns
        assert len(result) == 3

    def test_process_with_numeric_outcomes(self):
        """Test processing with numeric outcome values."""
        data = {
            'white_rating': [1500, 1500],
            'black_rating': [1500, 1500],
            'outcome': [1.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        result = process_game_record(df)
        
        assert result['elo_expected_prob'].iloc[0] == 0.5
        assert result['outcome_deviation'].iloc[0] == 0.5
        assert result['outcome_deviation'].iloc[1] == -0.5

    def test_missing_columns(self):
        """Test that missing columns are handled gracefully."""
        data = {
            'white_rating': [1500],
            'outcome': ['1-0']
        }
        df = pd.DataFrame(data)
        
        # Should not raise, but the function expects black_rating
        # This test documents the expected behavior
        with pytest.raises(KeyError):
            process_game_record(df)

    def test_probability_bounds_in_dataframe(self):
        """Test that probabilities in DataFrame are within bounds."""
        data = {
            'white_rating': [3000, 0],
            'black_rating': [0, 3000],
            'outcome': ['1-0', '0-1']
        }
        df = pd.DataFrame(data)
        
        result = process_game_record(df)
        
        assert result['elo_expected_prob'].min() >= PROBABILITY_MIN
        assert result['elo_expected_prob'].max() <= PROBABILITY_MAX
