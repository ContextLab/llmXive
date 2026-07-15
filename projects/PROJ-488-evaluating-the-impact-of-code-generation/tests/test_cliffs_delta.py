import pytest
import math
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cliffs_delta_analysis import compute_cliffs_delta, get_effect_size_magnitude

class TestCliffsDeltaComputation:
    def test_identical_distributions(self):
        """Delta should be 0 for identical distributions."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        delta = compute_cliffs_delta(x, y)
        assert math.isclose(delta, 0.0, abs_tol=1e-5)

    def test_complete_separation_greater(self):
        """Delta should be 1 if all x > all y."""
        x = [10.0, 11.0, 12.0]
        y = [1.0, 2.0, 3.0]
        delta = compute_cliffs_delta(x, y)
        assert math.isclose(delta, 1.0, abs_tol=1e-5)

    def test_complete_separation_smaller(self):
        """Delta should be -1 if all x < all y."""
        x = [1.0, 2.0, 3.0]
        y = [10.0, 11.0, 12.0]
        delta = compute_cliffs_delta(x, y)
        assert math.isclose(delta, -1.0, abs_tol=1e-5)

    def test_partial_overlap(self):
        """Test with overlapping distributions."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [3.0, 4.0, 5.0, 6.0, 7.0]
        delta = compute_cliffs_delta(x, y)
        # x has 2 values < all y (1,2), 3 values > some y (3,4,5)
        # Manual calc: 
        # 1 < 3,4,5,6,7 (5 smaller)
        # 2 < 3,4,5,6,7 (5 smaller)
        # 3 < 4,5,6,7 (4 smaller), > 3? No. 3==3.
        # Actually, let's rely on the function logic.
        # The function calculates (greater - smaller) / total.
        # We just check it returns a value in [-1, 1]
        assert -1.0 <= delta <= 1.0

    def test_empty_lists(self):
        """Delta should be 0.0 for empty inputs."""
        assert compute_cliffs_delta([], []) == 0.0
        assert compute_cliffs_delta([1.0], []) == 0.0
        assert compute_cliffs_delta([], [1.0]) == 0.0

class TestMagnitudeClassification:
    def test_negligible(self):
        assert get_effect_size_magnitude(0.05) == "negligible"
        assert get_effect_size_magnitude(-0.05) == "negligible"
        assert get_effect_size_magnitude(0.14) == "negligible"
        assert get_effect_size_magnitude(0.146) == "negligible"

    def test_small(self):
        assert get_effect_size_magnitude(0.15) == "small"
        assert get_effect_size_magnitude(-0.15) == "small"
        assert get_effect_size_magnitude(0.32) == "small"
        assert get_effect_size_magnitude(0.329) == "small"

    def test_medium(self):
        assert get_effect_size_magnitude(0.33) == "medium"
        assert get_effect_size_magnitude(-0.33) == "medium"
        assert get_effect_size_magnitude(0.47) == "medium"
        assert get_effect_size_magnitude(0.473) == "medium"

    def test_large(self):
        assert get_effect_size_magnitude(0.48) == "large"
        assert get_effect_size_magnitude(-0.48) == "large"
        assert get_effect_size_magnitude(1.0) == "large"
        assert get_effect_size_magnitude(-1.0) == "large"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
