import pytest
import math
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from calculate_effect_sizes import calculate_cohen_d, calculate_ci_95_cohen_d

class TestEffectSizes:
    def test_cohen_d_identical_groups(self):
        """Test Cohen's d for identical groups should be 0."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]
        d = calculate_cohen_d(group1, group2)
        assert math.isclose(d, 0.0, abs_tol=1e-6)

    def test_cohen_d_large_difference(self):
        """Test Cohen's d for significantly different groups."""
        group1 = [10.0, 11.0, 12.0]
        group2 = [1.0, 2.0, 3.0]
        d = calculate_cohen_d(group1, group2)
        # Mean diff = 9, Pooled std approx 1.
        assert d > 5.0  # Large effect

    def test_cohen_d_empty_group(self):
        """Test that empty groups raise an error."""
        with pytest.raises(ValueError):
            calculate_cohen_d([], [1.0, 2.0])

    def test_ci_95_cohen_d(self):
        """Test confidence interval calculation."""
        group1 = [10.0, 12.0, 14.0]
        group2 = [2.0, 4.0, 6.0]
        d = calculate_cohen_d(group1, group2)
        ci_lower, ci_upper = calculate_ci_95_cohen_d(group1, group2, d)
        
        assert ci_lower < d
        assert ci_upper > d
        assert isinstance(ci_lower, float)
        assert isinstance(ci_upper, float)

    def test_ci_95_insufficient_data(self):
        """Test CI calculation with insufficient data points."""
        group1 = [1.0]
        group2 = [2.0]
        d = calculate_cohen_d(group1, group2)
        with pytest.raises(ValueError):
            calculate_ci_95_cohen_d(group1, group2, d)
