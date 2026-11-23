import pytest
import math
import json
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.stats import two_proportion_z_test, ZTestResult

class TestZTestConfidenceIntervals:
    """Tests for T044: Confidence interval calculation in two-proportion z-test."""

    def test_z_test_basic_ci(self):
        """Test that z-test returns valid confidence intervals."""
        # Group 1: 50/100, Group 2: 30/100
        result = two_proportion_z_test(50, 100, 30, 100)
        
        assert isinstance(result, ZTestResult)
        assert result.ci_lower is not None
        assert result.ci_upper is not None
        assert result.ci_lower <= result.diff_proportion <= result.ci_upper
        assert result.ci_lower < result.ci_upper

    def test_z_test_significant_difference(self):
        """Test CI does not contain 0 when difference is significant."""
        # Large difference: 80/100 vs 20/100
        result = two_proportion_z_test(80, 100, 20, 100)
        
        assert result.is_significant
        # 95% CI should not contain 0
        assert result.ci_lower > 0 or result.ci_upper < 0

    def test_z_test_non_significant_difference(self):
        """Test CI contains 0 when difference is not significant."""
        # Small difference: 51/100 vs 49/100
        result = two_proportion_z_test(51, 100, 49, 100)
        
        assert not result.is_significant
        # 95% CI should contain 0
        assert result.ci_lower <= 0 <= result.ci_upper

    def test_ci_width_scales_with_sample_size(self):
        """Test that CI narrows as sample size increases."""
        # Same proportion, different sample sizes
        result_small = two_proportion_z_test(50, 100, 30, 100)
        result_large = two_proportion_z_test(500, 1000, 300, 1000)
        
        width_small = result_small.ci_upper - result_small.ci_lower
        width_large = result_large.ci_upper - result_large.ci_lower
        
        # Larger sample should have narrower CI
        assert width_large < width_small

    def test_ci_bounds_reasonable(self):
        """Test that CI bounds are within [-1, 1]."""
        result = two_proportion_z_test(90, 100, 10, 100)
        
        assert -1.0 <= result.ci_lower <= 1.0
        assert -1.0 <= result.ci_upper <= 1.0

    def test_ci_format_in_json(self):
        """Test that CI is correctly serialized to JSON (for T031a)."""
        result = two_proportion_z_test(60, 100, 40, 100)
        
        data = {
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "p_value": result.p_value
        }
        
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        
        assert "ci_lower" in loaded
        assert "ci_upper" in loaded
        assert isinstance(loaded["ci_lower"], float)
        assert isinstance(loaded["ci_upper"], float)