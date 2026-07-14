import pytest
import numpy as np
from src.data.process import calculate_expected_probability, calculate_outcome_deviation

class TestEloProbability:
    """Unit tests for Elo expected probability calculation."""

    def test_equal_ratings(self):
        """When ratings are equal, probability should be 0.5."""
        prob = calculate_expected_probability(1500, 1500)
        assert abs(prob - 0.5) < 1e-6

    def test_white_stronger(self):
        """White with higher rating should have probability > 0.5."""
        prob = calculate_expected_probability(1600, 1500)
        assert prob > 0.5
        # Rough check: 100 point diff should be around 0.64
        assert 0.6 < prob < 0.7

    def test_black_stronger(self):
        """White with lower rating should have probability < 0.5."""
        prob = calculate_expected_probability(1400, 1500)
        assert prob < 0.5
        # Symmetric to white stronger case
        assert 0.3 < prob < 0.4

    def test_clamping_upper(self):
        """Extreme rating differences should be clamped to max probability."""
        # Very large rating difference
        prob = calculate_expected_probability(2500, 1000)
        assert prob <= 0.99

    def test_clamping_lower(self):
        """Extreme rating differences should be clamped to min probability."""
        # Very large rating difference favoring black
        prob = calculate_expected_probability(1000, 2500)
        assert prob >= 0.01

    def test_nan_handling(self):
        """NaN inputs should return NaN."""
        assert np.isnan(calculate_expected_probability(np.nan, 1500))
        assert np.isnan(calculate_expected_probability(1500, np.nan))

class TestOutcomeDeviation:
    """Unit tests for outcome deviation calculation."""

    def test_white_win_equal_rated(self):
        """White win with equal ratings: 1.0 - 0.5 = 0.5."""
        deviation = calculate_outcome_deviation(1.0, 0.5)
        assert abs(deviation - 0.5) < 1e-6

    def test_draw_equal_rated(self):
        """Draw with equal ratings: 0.5 - 0.5 = 0.0."""
        deviation = calculate_outcome_deviation(0.5, 0.5)
        assert abs(deviation - 0.0) < 1e-6

    def test_black_win_equal_rated(self):
        """Black win with equal ratings: 0.0 - 0.5 = -0.5."""
        deviation = calculate_outcome_deviation(0.0, 0.5)
        assert abs(deviation - (-0.5)) < 1e-6

    def test_white_win_high_expectation(self):
        """White win when expected to win: 1.0 - 0.8 = 0.2."""
        deviation = calculate_outcome_deviation(1.0, 0.8)
        assert abs(deviation - 0.2) < 1e-6

    def test_white_loss_high_expectation(self):
        """White loss when expected to win: 0.0 - 0.8 = -0.8."""
        deviation = calculate_outcome_deviation(0.0, 0.8)
        assert abs(deviation - (-0.8)) < 1e-6

    def test_nan_handling(self):
        """NaN inputs should return NaN."""
        assert np.isnan(calculate_outcome_deviation(np.nan, 0.5))
        assert np.isnan(calculate_outcome_deviation(1.0, np.nan))
        assert np.isnan(calculate_outcome_deviation(np.nan, np.nan))

    def test_integer_inputs(self):
        """Function should handle integer inputs correctly."""
        deviation = calculate_outcome_deviation(1, 0)
        assert abs(deviation - 1.0) < 1e-6

        deviation = calculate_outcome_deviation(0, 1)
        assert abs(deviation - (-1.0)) < 1e-6