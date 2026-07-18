import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.evaluate import calculate_tvd

class TestSplitValidation:
    """Unit tests for stratified split logic and TVD calculation."""

    def test_calculate_tvd_identical_distribution(self):
        """TVD should be 0.0 for identical distributions."""
        train_dist = {'A': 0.5, 'B': 0.5}
        val_dist = {'A': 0.5, 'B': 0.5}
        
        tvd = calculate_tvd(train_dist, val_dist)
        assert tvd == 0.0, f"Expected TVD 0.0, got {tvd}"

    def test_calculate_tvd_disjoint_distribution(self):
        """TVD should be 1.0 for completely disjoint distributions."""
        train_dist = {'A': 1.0}
        val_dist = {'B': 1.0}
        
        tvd = calculate_tvd(train_dist, val_dist)
        assert tvd == 1.0, f"Expected TVD 1.0, got {tvd}"

    def test_calculate_tvd_partial_overlap(self):
        """TVD should be 0.25 for partial overlap."""
        # Train: A=0.6, B=0.4
        # Val: A=0.4, B=0.6
        # |0.6-0.4| + |0.4-0.6| = 0.2 + 0.2 = 0.4
        # TVD = 0.5 * 0.4 = 0.2
        train_dist = {'A': 0.6, 'B': 0.4}
        val_dist = {'A': 0.4, 'B': 0.6}
        
        tvd = calculate_tvd(train_dist, val_dist)
        assert abs(tvd - 0.2) < 1e-6, f"Expected TVD 0.2, got {tvd}"

    def test_calculate_tvd_with_missing_keys(self):
        """TVD should handle missing keys in one distribution."""
        # Train: A=0.7, B=0.3
        # Val: A=0.7, C=0.3 (B is missing in Val, C is missing in Train)
        # Train: A=0.7, B=0.3, C=0.0
        # Val: A=0.7, B=0.0, C=0.3
        # |0.7-0.7| + |0.3-0.0| + |0.0-0.3| = 0 + 0.3 + 0.3 = 0.6
        # TVD = 0.5 * 0.6 = 0.3
        train_dist = {'A': 0.7, 'B': 0.3}
        val_dist = {'A': 0.7, 'C': 0.3}
        
        tvd = calculate_tvd(train_dist, val_dist)
        assert abs(tvd - 0.3) < 1e-6, f"Expected TVD 0.3, got {tvd}"

    def test_calculate_tvd_empty_distribution(self):
        """TVD should handle empty distributions gracefully or raise error."""
        # If both are empty, TVD is 0? Or undefined?
        # Let's test with one empty and one non-empty -> TVD should be 1.0
        train_dist = {}
        val_dist = {'A': 1.0}
        
        # The calculate_tvd function should handle this.
        # If it raises, we catch it. If it returns 1.0, we check.
        try:
            tvd = calculate_tvd(train_dist, val_dist)
            assert tvd == 1.0, f"Expected TVD 1.0 for empty vs non-empty, got {tvd}"
        except ValueError:
            # If the function raises ValueError for empty distributions, that's acceptable.
            pass

    def test_calculate_tvd_threshold_check(self):
        """Test that TVD calculation can be used to check against a threshold."""
        train_dist = {'A': 0.9, 'B': 0.1}
        val_dist = {'A': 0.8, 'B': 0.2}
        
        tvd = calculate_tvd(train_dist, val_dist)
        # |0.9-0.8| + |0.1-0.2| = 0.1 + 0.1 = 0.2
        # TVD = 0.1
        assert tvd <= 0.05, f"TVD {tvd} should be <= 0.05 for good split"
        
        # Now a bad split
        train_dist_bad = {'A': 0.9, 'B': 0.1}
        val_dist_bad = {'A': 0.5, 'B': 0.5}
        
        tvd_bad = calculate_tvd(train_dist_bad, val_dist_bad)
        # |0.9-0.5| + |0.1-0.5| = 0.4 + 0.4 = 0.8
        # TVD = 0.4
        assert tvd_bad > 0.05, f"TVD {tvd_bad} should be > 0.05 for bad split"