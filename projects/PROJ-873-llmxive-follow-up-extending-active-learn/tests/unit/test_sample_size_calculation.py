import pytest
import math
from metrics import calculate_dynamic_sample_size, DEFAULT_LLM_CONSENSUS_UPPER_BOUND, DEFERRED_FRACTION

class TestDynamicSampleSizeCalculation:
    """
    Unit tests for T013c: Calculate the dynamic sample size for LLM consensus validation.
    Formula: min([deferred] of total flagged calls, a predefined upper bound)
    """

    def test_calculate_sample_size_basic(self):
        """Test basic calculation where deferred is less than upper bound."""
        total_flagged = 1000
        upper_bound = 200
        deferred_fraction = 0.10
        
        # deferred = 1000 * 0.10 = 100
        # result = min(100, 200) = 100
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 100

    def test_calculate_sample_size_capped_by_upper_bound(self):
        """Test that sample size is capped by the upper bound when deferred is large."""
        total_flagged = 5000
        upper_bound = 200
        deferred_fraction = 0.10
        
        # deferred = 5000 * 0.10 = 500
        # result = min(500, 200) = 200
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 200

    def test_calculate_sample_size_small_dataset(self):
        """Test calculation on a small dataset where total is less than deferred."""
        total_flagged = 50
        upper_bound = 200
        deferred_fraction = 0.10
        
        # deferred = 50 * 0.10 = 5
        # result = min(5, 200) = 5
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 5

    def test_calculate_sample_size_zero_flagged(self):
        """Test calculation when there are no flagged calls."""
        result = calculate_dynamic_sample_size(0, 200, 0.10)
        assert result == 0

    def test_calculate_sample_size_fractional_deferred(self):
        """Test that fractional deferred values are handled correctly (integer conversion)."""
        total_flagged = 15
        upper_bound = 200
        deferred_fraction = 0.10
        
        # deferred = 15 * 0.10 = 1.5 -> int(1.5) = 1
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 1

    def test_calculate_sample_size_high_fraction(self):
        """Test with a high deferred fraction."""
        total_flagged = 100
        upper_bound = 200
        deferred_fraction = 0.50
        
        # deferred = 100 * 0.50 = 50
        # result = min(50, 200) = 50
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 50

    def test_calculate_sample_size_upper_bound_less_than_deferred(self):
        """Test when upper bound is smaller than the calculated deferred amount."""
        total_flagged = 1000
        upper_bound = 50
        deferred_fraction = 0.10
        
        # deferred = 1000 * 0.10 = 100
        # result = min(100, 50) = 50
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 50

    def test_calculate_sample_size_default_parameters(self):
        """Test using default parameters."""
        # Simulating a scenario with default upper bound and fraction
        total_flagged = 3000
        result = calculate_dynamic_sample_size(total_flagged)
        
        # deferred = 3000 * 0.10 = 300
        # result = min(300, 200) = 200
        assert result == 200

    def test_calculate_sample_size_exact_boundary(self):
        """Test when deferred exactly equals the upper bound."""
        total_flagged = 2000
        upper_bound = 200
        deferred_fraction = 0.10
        
        # deferred = 2000 * 0.10 = 200
        # result = min(200, 200) = 200
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 200

    def test_calculate_sample_size_very_small_total(self):
        """Test with a very small total flagged count."""
        total_flagged = 5
        upper_bound = 200
        deferred_fraction = 0.10
        
        # deferred = 5 * 0.10 = 0.5 -> int(0.5) = 0
        result = calculate_dynamic_sample_size(total_flagged, upper_bound, deferred_fraction)
        assert result == 0