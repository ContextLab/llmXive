import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from scripts.run_analysis import benjamini_hochberg, calculate_cohens_d

def test_benjamini_hochberg():
    """Test Benjamini-Hochberg FDR correction."""
    p_values = [0.01, 0.03, 0.04, 0.005, 0.02]
    corrected = benjamini_hochberg(p_values)
    
    # Check that corrected values are in [0, 1]
    assert all(0 <= p <= 1 for p in corrected), "Corrected p-values must be in [0, 1]"
    
    # Check that corrected values are monotonic when sorted
    sorted_corrected = sorted(corrected)
    assert all(sorted_corrected[i] <= sorted_corrected[i+1] for i in range(len(sorted_corrected)-1)), \
        "Corrected p-values should be monotonic"

def test_cohens_d():
    """Test Cohen's d calculation."""
    # Identical groups should have d = 0
    group1 = [1, 2, 3, 4, 5]
    group2 = [1, 2, 3, 4, 5]
    d = calculate_cohens_d(group1, group2)
    assert np.isclose(d, 0.0), f"Expected d=0 for identical groups, got {d}"
    
    # Different groups should have non-zero d
    group1 = [1, 2, 3, 4, 5]
    group2 = [10, 11, 12, 13, 14]
    d = calculate_cohens_d(group1, group2)
    assert d < 0, "Expected negative d when group1 < group2"
    
    # Check magnitude
    group1 = [1, 2, 3, 4, 5]
    group2 = [2, 3, 4, 5, 6]
    d = calculate_cohens_d(group1, group2)
    assert np.isclose(d, -1.0, atol=0.1), f"Expected d≈-1.0, got {d}"
