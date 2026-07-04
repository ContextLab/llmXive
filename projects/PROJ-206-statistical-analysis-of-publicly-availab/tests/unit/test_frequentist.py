import sys
import os
from pathlib import Path
import pytest
from src.models.frequentist import simple_average, weighted_average

class TestSimpleAverage:
    def test_single_poll(self):
        """Verify arithmetic mean for a single poll returns that value."""
        polls = [{"vote_share": 45.5}]
        result = simple_average(polls)
        assert result == 45.5

    def test_multiple_polls(self):
        """Verify arithmetic mean for multiple polls."""
        polls = [
            {"vote_share": 40.0},
            {"vote_share": 50.0},
            {"vote_share": 45.0}
        ]
        result = simple_average(polls)
        assert result == 45.0

    def test_empty_list(self):
        """Verify behavior with empty input list."""
        polls = []
        with pytest.raises(ValueError, match="No polls provided"):
            simple_average(polls)

    def test_missing_vote_share(self):
        """Verify behavior when vote_share is missing."""
        polls = [
            {"vote_share": 40.0},
            {"other_field": 50.0}
        ]
        with pytest.raises(KeyError):
            simple_average(polls)

class TestWeightedAverage:
    def test_single_poll_with_weight(self):
        """Verify weighted mean for a single poll returns that value."""
        polls = [{"vote_share": 45.5, "weight": 0.8}]
        result = weighted_average(polls)
        assert result == 45.5

    def test_multiple_polls_with_weights(self):
        """Verify weighted mean calculation."""
        polls = [
            {"vote_share": 40.0, "weight": 0.5},
            {"vote_share": 50.0, "weight": 1.0},
            {"vote_share": 45.0, "weight": 0.5}
        ]
        # Weighted sum: (40*0.5 + 50*1.0 + 45*0.5) = 20 + 50 + 22.5 = 92.5
        # Total weight: 0.5 + 1.0 + 0.5 = 2.0
        # Result: 92.5 / 2.0 = 46.25
        result = weighted_average(polls)
        assert result == 46.25

    def test_missing_weights(self):
        """Verify behavior when weights are missing (should raise error or handle gracefully)."""
        polls = [
            {"vote_share": 40.0},
            {"vote_share": 50.0, "weight": 1.0}
        ]
        # Based on implementation, missing weights should raise KeyError
        with pytest.raises(KeyError):
            weighted_average(polls)

    def test_zero_weights(self):
        """Verify behavior when all weights are zero."""
        polls = [
            {"vote_share": 40.0, "weight": 0.0},
            {"vote_share": 50.0, "weight": 0.0}
        ]
        with pytest.raises(ValueError, match="Total weight is zero"):
            weighted_average(polls)

    def test_empty_list(self):
        """Verify behavior with empty input list."""
        polls = []
        with pytest.raises(ValueError, match="No polls provided"):
            weighted_average(polls)