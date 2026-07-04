"""
Unit tests for frequentist aggregation models.

Tests:
- simple_average: Arithmetic mean calculation
- weighted_average: Inverse RMSE weighted mean
- Edge cases: single poll, missing weights, zero RMSE
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from src.models.frequentist import simple_average, weighted_average

class TestSimpleAverage:
    def test_basic_calculation(self):
        """Test arithmetic mean with known values."""
        data = [
            {"week_bin": "1", "vote_share": 40.0},
            {"week_bin": "1", "vote_share": 50.0},
            {"week_bin": "1", "vote_share": 60.0},
        ]
        result = simple_average(data)
        
        assert len(result) == 1
        assert result[0]["week_bin"] == "1"
        assert result[0]["simple_avg_forecast"] == 50.0  # (40+50+60)/3
        assert result[0]["n_polls"] == 3

    def test_multiple_bins(self):
        """Test calculation across multiple weekly bins."""
        data = [
            {"week_bin": "1", "vote_share": 40.0},
            {"week_bin": "2", "vote_share": 50.0},
            {"week_bin": "2", "vote_share": 60.0},
        ]
        result = simple_average(data)
        
        assert len(result) == 2
        # Check bin 1
        bin1 = next(r for r in result if r["week_bin"] == "1")
        assert bin1["simple_avg_forecast"] == 40.0
        # Check bin 2
        bin2 = next(r for r in result if r["week_bin"] == "2")
        assert bin2["simple_avg_forecast"] == 55.0

    def test_single_poll(self):
        """Test with a single poll (edge case)."""
        data = [
            {"week_bin": "1", "vote_share": 45.5},
        ]
        result = simple_average(data)
        
        assert len(result) == 1
        assert result[0]["simple_avg_forecast"] == 45.5
        assert result[0]["n_polls"] == 1

    def test_empty_data(self):
        """Test with empty input."""
        result = simple_average([])
        assert result == []

    def test_missing_vote_share(self):
        """Test handling of missing vote_share."""
        data = [
            {"week_bin": "1", "vote_share": 40.0},
            {"week_bin": "1"},  # Missing vote_share
            {"week_bin": "1", "vote_share": 60.0},
        ]
        result = simple_average(data)
        
        assert len(result) == 1
        # Should average only the valid values: (40+60)/2 = 50
        assert result[0]["simple_avg_forecast"] == 50.0
        assert result[0]["n_polls"] == 2

    def test_invalid_vote_share(self):
        """Test handling of invalid vote_share values."""
        data = [
            {"week_bin": "1", "vote_share": 40.0},
            {"week_bin": "1", "vote_share": "invalid"},
            {"week_bin": "1", "vote_share": 60.0},
        ]
        result = simple_average(data)
        
        assert len(result) == 1
        assert result[0]["simple_avg_forecast"] == 50.0
        assert result[0]["n_polls"] == 2

class TestWeightedAverage:
    def test_basic_calculation(self):
        """Test inverse RMSE weighted mean."""
        data = [
            {"week_bin": "1", "vote_share": 40.0, "historical_rmse": 2.0},
            {"week_bin": "1", "vote_share": 50.0, "historical_rmse": 1.0},
        ]
        # Weights: w1 = (1/2) / (1/2 + 1/1) = 0.5 / 1.5 = 1/3
        #          w2 = (1/1) / (1/2 + 1/1) = 1.0 / 1.5 = 2/3
        # Forecast: (1/3)*40 + (2/3)*50 = 13.33 + 33.33 = 46.66...
        result = weighted_average(data)
        
        assert len(result) == 1
        expected = (1/3)*40 + (2/3)*50
        assert abs(result[0]["weighted_avg_forecast"] - expected) < 0.0001

    def test_multiple_bins(self):
        """Test calculation across multiple bins."""
        data = [
            {"week_bin": "1", "vote_share": 40.0, "historical_rmse": 2.0},
            {"week_bin": "2", "vote_share": 50.0, "historical_rmse": 1.0},
            {"week_bin": "2", "vote_share": 60.0, "historical_rmse": 2.0},
        ]
        result = weighted_average(data)
        
        assert len(result) == 2
        bin1 = next(r for r in result if r["week_bin"] == "1")
        assert bin1["weighted_avg_forecast"] == 40.0  # Only one poll
        
        # Bin 2: weights 1/1=1 and 1/2=0.5 -> total 1.5
        # w1 = 1/1.5 = 2/3, w2 = 0.5/1.5 = 1/3
        # Forecast = (2/3)*50 + (1/3)*60 = 33.33 + 20 = 53.33
        bin2 = next(r for r in result if r["week_bin"] == "2")
        expected = (2/3)*50 + (1/3)*60
        assert abs(bin2["weighted_avg_forecast"] - expected) < 0.0001

    def test_single_poll(self):
        """Test with a single poll."""
        data = [
            {"week_bin": "1", "vote_share": 45.5, "historical_rmse": 1.5},
        ]
        result = weighted_average(data)
        
        assert len(result) == 1
        assert result[0]["weighted_avg_forecast"] == 45.5

    def test_empty_data(self):
        """Test with empty input."""
        result = weighted_average([])
        assert result == []

    def test_zero_rmse_fallback(self):
        """Test handling of zero RMSE (should fallback to simple average)."""
        data = [
            {"week_bin": "1", "vote_share": 40.0, "historical_rmse": 0.0},
            {"week_bin": "1", "vote_share": 50.0, "historical_rmse": 0.0},
        ]
        result = weighted_average(data)
        
        assert len(result) == 1
        # Fallback to simple average: (40+50)/2 = 45
        assert result[0]["weighted_avg_forecast"] == 45.0

    def test_negative_rmse_skipped(self):
        """Test handling of negative RMSE (should be skipped)."""
        data = [
            {"week_bin": "1", "vote_share": 40.0, "historical_rmse": -1.0},
            {"week_bin": "1", "vote_share": 50.0, "historical_rmse": 1.0},
        ]
        result = weighted_average(data)
        
        assert len(result) == 1
        # Only the valid poll should be used
        assert result[0]["weighted_avg_forecast"] == 50.0
        assert result[0]["n_polls"] == 1

    def test_missing_weight_column(self):
        """Test handling of missing weight column."""
        data = [
            {"week_bin": "1", "vote_share": 40.0},  # Missing historical_rmse
            {"week_bin": "1", "vote_share": 50.0, "historical_rmse": 1.0},
        ]
        result = weighted_average(data)
        
        assert len(result) == 1
        # Only the valid poll should be used
        assert result[0]["weighted_avg_forecast"] == 50.0

    def test_weight_normalization(self):
        """Test that weights sum to 1.0."""
        data = [
            {"week_bin": "1", "vote_share": 40.0, "historical_rmse": 2.0},
            {"week_bin": "1", "vote_share": 50.0, "historical_rmse": 1.0},
            {"week_bin": "1", "vote_share": 60.0, "historical_rmse": 2.0},
        ]
        # Weights: 1/2, 1/1, 1/2 -> 0.5, 1.0, 0.5 -> total 2.0
        # Normalized: 0.25, 0.5, 0.25
        # Forecast: 0.25*40 + 0.5*50 + 0.25*60 = 10 + 25 + 15 = 50
        result = weighted_average(data)
        
        assert len(result) == 1
        assert result[0]["weighted_avg_forecast"] == 50.0