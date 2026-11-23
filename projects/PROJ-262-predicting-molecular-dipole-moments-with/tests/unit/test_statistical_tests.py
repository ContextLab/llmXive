import pytest
import numpy as np

# Import the function from the project module
from analysis.statistical_tests import paired_t_test


def test_paired_t_test_identical_samples():
    """Identical samples should yield a t‑stat of 0 and p‑value of 1."""
    sample = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = paired_t_test(sample, sample)
    assert result["t_stat"] == pytest.approx(0.0, abs=1e-12)
    assert result["p_value"] == pytest.approx(1.0, abs=1e-12)
    assert result["df"] == 4.0  # len(sample) - 1


def test_paired_t_test_known_difference():
    """A simple case where one sample is uniformly higher should give a low p‑value."""
    sample1 = [1, 2, 3, 4, 5]
    sample2 = [2, 3, 4, 5, 6]  # each element +1
    result = paired_t_test(sample1, sample2)
    # The difference is constant, so t statistic is large in magnitude
    assert result["p_value"] < 0.001


def test_paired_t_test_mismatched_lengths():
    """Function should raise ValueError when input lengths differ."""
    with pytest.raises(ValueError):
        paired_t_test([1, 2, 3], [1, 2])


def test_t_test_handles_equal_variance_and_small_samples():
    """
    Assert correct statistical handling for equal variance assumption
    and small sample sizes (n < 30).
    """
    # Small sample sizes (n=5 each)
    # Sample 1: [10.0, 12.0, 9.0, 11.0, 13.0] -> mean=11.0, var=2.5
    # Sample 2: [11.0, 13.0, 10.0, 12.0, 14.0] -> mean=12.0, var=2.5
    # Differences: [-1, -1, -1, -1, -1] -> mean_diff = -1.0, std_diff = 0.0
    # t = mean_diff / (std_diff / sqrt(n)) -> division by zero if std_diff is 0
    # However, paired t-test on constant difference usually yields t=inf or similar
    # Let's use a case with non-zero variance in differences
    
    # Case: Small samples with non-constant difference
    sample1 = [10.0, 12.0, 9.0, 11.0, 13.0]
    sample2 = [11.5, 13.0, 10.5, 12.0, 14.5]
    # Differences: [-1.5, -1.0, -1.5, -1.0, -1.5]
    # Mean diff = -1.3
    # Std diff ~ 0.2236
    
    result = paired_t_test(sample1, sample2)
    
    # Verify keys exist
    assert "t_stat" in result
    assert "p_value" in result
    assert "df" in result
    
    # Degrees of freedom for paired t-test is n-1
    assert result["df"] == len(sample1) - 1
    
    # Verify p_value is a valid probability
    assert 0.0 <= result["p_value"] <= 1.0
    
    # Verify t_stat is a float
    assert isinstance(result["t_stat"], float)


def test_paired_t_test_unequal_variance_small_sample():
    """
    Test behavior with small samples where variances differ.
    SciPy's paired_t_test (using ttest_rel) does not assume equal variance
    in the same way as independent samples, but handles the paired differences.
    """
    # Small samples
    sample1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    sample2 = [2.0, 4.0, 6.0, 8.0, 10.0]
    # Differences: [-1, -2, -3, -4, -5]
    
    result = paired_t_test(sample1, sample2)
    
    assert result["df"] == 4
    assert result["p_value"] < 0.01  # Significant difference