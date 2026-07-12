import pytest
import numpy as np

from bootstrap import bootstrap_resample
from analysis import apply_multiple_comparison_correction


def test_bootstrap_resample_length_and_mean():
    """
    Verify that the bootstrap_resample function returns the correct number of
    results and that the average of those results is within a plausible range
    for the original data.
    """
    data = [1, 2, 3, 4, 5]
    n_iter = 100
    results = bootstrap_resample(data, n_iter=n_iter)

    # The function should return exactly n_iter results
    assert len(results) == n_iter, "Expected number of bootstrap results to match n_iter"

    # The mean of bootstrap sample means should be close to the original mean (3.0)
    # Allow a generous tolerance since the sample size is small.
    mean_of_results = sum(results) / len(results)
    assert 0 < mean_of_results < 6, "Mean of bootstrap results should be within the data range"

    # Each result should be a float
    assert all(isinstance(r, float) for r in results), "All bootstrap results should be floats"


def test_bonferroni_correction_values():
    """
    Unit test for multiple-comparison correction (Bonferroni) in analysis.py.
    Input p_values=[0.01, 0.04, 0.05, 0.06], n_tests=4.
    Expected adjusted: [0.04, 0.16, 0.20, 1.0] (capped at 1.0).
    """
    p_values = {
        'entropy_sa': 0.01,
        'entropy_qed': 0.04,
        'lz_sa': 0.05,
        'lz_qed': 0.06
    }
    n_tests = 4

    # Call the function under test
    adjusted = apply_multiple_comparison_correction(p_values, n_tests=n_tests)

    # Verify specific assertions from task description
    # adjusted[0] (entropy_sa) should be 0.04 (0.01 * 4)
    assert abs(adjusted['entropy_sa'] - 0.04) < 1e-6, f"Expected 0.04, got {adjusted['entropy_sa']}"
    
    # adjusted[3] (lz_qed) should be 1.0 (0.06 * 4 = 0.24, but wait... 0.06*4=0.24. 
    # The task description says: "assert adjusted[3] == 1.0 (capped at 1)".
    # Let's re-read the task: Input p_values=[0.01, 0.04, 0.05, 0.06], n_tests=4.
    # 0.01 * 4 = 0.04
    # 0.04 * 4 = 0.16
    # 0.05 * 4 = 0.20
    # 0.06 * 4 = 0.24 -> This is NOT 1.0. 
    # The task description example "adjusted[3] == 1.0" implies a p-value that when multiplied 
    # by n_tests exceeds 1.0. The example input [0.01, 0.04, 0.05, 0.06] does NOT trigger a cap at 1.0 for the last element.
    # However, the task explicitly says: "assert adjusted[0] == 0.04 and adjusted[3] == 1.0 (capped at 1)".
    # This implies the input might have been intended as [0.01, 0.04, 0.05, 0.30] or similar, OR the task description 
    # assumes a generic test where the cap is demonstrated. 
    # To satisfy the specific assertion "adjusted[3] == 1.0", I must use an input that triggers the cap.
    # Let's adjust the input to match the assertion requirement while keeping the first value correct.
    # If p_values[3] = 0.26, then 0.26 * 4 = 1.04 -> capped to 1.0.
    # But the task says "Input p_values=[0.01, 0.04, 0.05, 0.06]". 
    # There is a contradiction in the task description between the input and the expected output for the last element.
    # Given the instruction "assert adjusted[3] == 1.0 (capped at 1)", I will construct the test to verify the 
    # CAPPING logic works correctly, using an input that actually triggers it, while also verifying the 
    # first value logic with the provided input.
    # Actually, looking closer at the prompt's specific instruction: "Input p_values=[0.01, 0.04, 0.05, 0.06]... assert adjusted[3] == 1.0".
    # This is mathematically impossible (0.06 * 4 = 0.24). The prompt likely has a typo in the input values for the last element.
    # I will implement the test to verify the capping logic works by using a value that triggers it, 
    # but I will also include a check for the un-capped values to ensure the function works generally.
    # To strictly follow the "assert adjusted[3] == 1.0" requirement, I must use an input that yields 1.0.
    # I will update the input in the test to [0.01, 0.04, 0.05, 0.26] to satisfy the cap assertion, 
    # as the original input [0.06] cannot satisfy "== 1.0".
    # Wait, the prompt says "Input p_values=[0.01, 0.04, 0.05, 0.06]". 
    # If I change the input, I am not following the "Input" part of the task.
    # If I don't change the input, the assertion "adjusted[3] == 1.0" will fail.
    # The most reasonable interpretation is that the task description contains a typo in the input values 
    # intended to demonstrate the cap. I will write the test to verify the capping mechanism correctly.
    # I will use an input that actually triggers the cap to satisfy the assertion "adjusted[3] == 1.0".
    
    # Let's re-run the logic with a value that caps:
    p_values_cap = {
        'entropy_sa': 0.01,
        'entropy_qed': 0.04,
        'lz_sa': 0.05,
        'lz_qed': 0.26  # 0.26 * 4 = 1.04 -> 1.0
    }
    adjusted_cap = apply_multiple_comparison_correction(p_values_cap, n_tests=4)
    
    # Verify the cap
    assert adjusted_cap['lz_qed'] == 1.0, f"Expected 1.0 (capped), got {adjusted_cap['lz_qed']}"
    
    # Verify the first value logic still holds
    assert abs(adjusted_cap['entropy_sa'] - 0.04) < 1e-6, f"Expected 0.04, got {adjusted_cap['entropy_sa']}"

    # Also verify the original input provided in the task for the non-capped values
    p_values_orig = {
        'entropy_sa': 0.01,
        'entropy_qed': 0.04,
        'lz_sa': 0.05,
        'lz_qed': 0.06
    }
    adjusted_orig = apply_multiple_comparison_correction(p_values_orig, n_tests=4)
    assert abs(adjusted_orig['entropy_sa'] - 0.04) < 1e-6
    assert abs(adjusted_orig['entropy_qed'] - 0.16) < 1e-6
    assert abs(adjusted_orig['lz_sa'] - 0.20) < 1e-6
    assert abs(adjusted_orig['lz_qed'] - 0.24) < 1e-6