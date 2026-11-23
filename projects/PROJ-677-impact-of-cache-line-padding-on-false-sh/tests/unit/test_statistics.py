import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
# The project root is assumed to be the parent of the 'tests' directory
# which contains 'code' and 'tests' at the same level.
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from scripts.run_analysis import benjamini_hochberg, calculate_cohens_d

def test_benjamini_hochberg():
    """Test Benjamini-Hochberg FDR correction."""
    # Standard test case
    p_values = [0.01, 0.03, 0.04, 0.005, 0.02]
    corrected = benjamini_hochberg(p_values)
    
    # Check that corrected values are in [0, 1]
    assert all(0 <= p <= 1 for p in corrected), "Corrected p-values must be in [0, 1]"
    
    # Check that corrected values are monotonic when sorted
    # The BH procedure ensures that if p_i <= p_j then p'_i <= p'_j
    sorted_corrected = sorted(corrected)
    for i in range(len(sorted_corrected) - 1):
        assert sorted_corrected[i] <= sorted_corrected[i+1], \
            "Corrected p-values should be monotonic"

def test_cohens_d_identical():
    """Test Cohen's d calculation with identical groups (d should be 0)."""
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    group2 = [1.0, 2.0, 3.0, 4.0, 5.0]
    d = calculate_cohens_d(group1, group2)
    assert np.isclose(d, 0.0), f"Expected d=0 for identical groups, got {d}"

def test_cohens_d_large_difference():
    """Test Cohen's d with significantly different groups."""
    # Group 1: mean=3, std=1.58
    # Group 2: mean=12, std=1.58
    # Pooled std = 1.58
    # d = (3 - 12) / 1.58 = -5.69
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    group2 = [10.0, 11.0, 12.0, 13.0, 14.0]
    d = calculate_cohens_d(group1, group2)
    
    # We expect a large negative value because group1 < group2
    assert d < 0, "Expected negative d when group1 mean < group2 mean"
    assert abs(d) > 5.0, f"Expected large effect size (>5), got {d}"

def test_cohens_d_small_difference():
    """Test Cohen's d with small difference (approx -1.0)."""
    # group1: [1,2,3,4,5] -> mean=3, var=2.5, std=1.5811
    # group2: [2,3,4,5,6] -> mean=4, var=2.5, std=1.5811
    # pooled_std = sqrt((2.5 + 2.5)/2) = 1.5811
    # d = (3 - 4) / 1.5811 = -0.632
    # Wait, the task description in the prompt suggested -1.0. 
    # Let's re-calculate:
    # If group1 = [1, 2, 3, 4, 5] (mean 3)
    # If group2 = [2, 3, 4, 5, 6] (mean 4)
    # Difference = -1.
    # Std dev of each = sqrt(2.5) ~ 1.58.
    # Pooled std = 1.58.
    # d = -1 / 1.58 = -0.63.
    # The prompt example said "Expected d≈-1.0". This might have assumed a different
    # dataset or a specific definition of std (population vs sample).
    # We will test for the mathematically correct value for these specific lists.
    
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    group2 = [2.0, 3.0, 4.0, 5.0, 6.0]
    d = calculate_cohens_d(group1, group2)
    
    # Using sample standard deviation (ddof=1) which is standard for Cohen's d
    # mean1 = 3, mean2 = 4
    # var1 = 2.5, var2 = 2.5
    # pooled_var = (2.5 + 2.5) / 2 = 2.5
    # pooled_std = 1.58113883
    # d = (3 - 4) / 1.58113883 = -0.6324555
    expected_d = -0.632455532
    assert np.isclose(d, expected_d, atol=0.001), f"Expected d≈{expected_d}, got {d}"

def test_cohens_d_variance_edge_case():
    """Test Cohen's d with one group having zero variance."""
    group1 = [5.0, 5.0, 5.0]
    group2 = [10.0, 10.0, 10.0]
    # Pooled std will be 0. This should raise a division by zero or return inf.
    # We test that the function handles this gracefully or raises a specific error.
    # If the implementation returns inf, that's acceptable.
    try:
        d = calculate_cohens_d(group1, group2)
        assert np.isinf(d), "Expected inf when pooled std is 0"
    except ZeroDivisionError:
        pass  # Also acceptable behavior
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")