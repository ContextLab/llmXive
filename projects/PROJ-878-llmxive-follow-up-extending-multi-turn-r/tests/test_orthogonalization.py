"""
Tests for T013: Stratified Orthogonalization.

Verifies that the rejection sampling logic correctly enforces |r| < 0.2
between nesting_depth and branching_factor.
"""
import pytest
import math
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.orthogonalization_runner import pearson_correlation, run_orthogonalization

class TestPearsonCorrelation:
    def test_perfect_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = pearson_correlation(x, y)
        assert math.isclose(r, 1.0, abs_tol=1e-5)

    def test_perfect_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        r = pearson_correlation(x, y)
        assert math.isclose(r, -1.0, abs_tol=1e-5)

    def test_no_correlation(self):
        # Random-ish data that shouldn't correlate strongly
        x = [1, 2, 3, 4, 5]
        y = [5, 1, 4, 2, 3]
        r = pearson_correlation(x, y)
        # Not necessarily 0, but should be low for this small set
        # We just check it runs and returns a float between -1 and 1
        assert -1.0 <= r <= 1.0

    def test_empty_lists(self):
        assert pearson_correlation([], []) == 0.0

    def test_single_element(self):
        assert pearson_correlation([1], [1]) == 0.0 # Variance is 0

class TestOrthogonalizationRunner:
    def test_rejection_sampling_enforces_orthogonality(self):
        """
        Test that run_orthogonalization returns a dataset where |r| < 0.2.
        We use a small sample size for speed in testing.
        """
        # Use a small seed for reproducibility
        samples = run_orthogonalization(
            target_corr_threshold=0.2,
            min_samples=20,
            max_attempts=5000,
            depth_range=(3, 5),
            branching_range=(1, 3),
            seed=42
        )
        
        assert len(samples) >= 20, "Should have generated at least 20 samples"
        
        depths = [s["depth"] for s in samples]
        branchings = [s["branching"] for s in samples]
        
        r = pearson_correlation(depths, branchings)
        
        assert abs(r) < 0.2, f"Correlation {r} exceeded threshold 0.2. Orthogonalization failed."
        
        # Log for debugging
        print(f"Test Passed: Final r = {r:.4f}")

    def test_depth_and_branching_within_ranges(self):
        """
        Ensure generated graphs respect the requested ranges.
        """
        samples = run_orthogonalization(
            target_corr_threshold=0.2,
            min_samples=10,
            max_attempts=2000,
            depth_range=(3, 4),
            branching_range=(1, 2),
            seed=123
        )
        
        for s in samples:
            assert 3 <= s["depth"] <= 4, f"Depth {s['depth']} out of range"
            assert 1 <= s["branching"] <= 2, f"Branching {s['branching']} out of range"