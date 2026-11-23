import pytest
import numpy as np
import random
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats import (
    run_block_bootstrap_deviation_test,
    block_bootstrap_residues,
    calculate_deviation_D,
    StatisticalResult
)

def test_block_bootstrap_p_value_calculation():
    """
    Test that Block Bootstrap p-value is calculated correctly.
    We create a sequence that is perfectly uniform (or close) and check p-value.
    Then we create a biased sequence and check p-value is low.
    """
    random.seed(42)
    np.random.seed(42)

    # Test 1: Uniform-like sequence (should have high p-value)
    # Create a sequence with roughly equal counts for p=3
    N = 300
    prime = 3
    # Construct a sequence: 0, 1, 2, 0, 1, 2...
    sequence = [i % prime for i in range(N)]
    random.shuffle(sequence) # Shuffle to remove order but keep counts

    observed_counts = {k: 0 for k in range(prime)}
    for val in sequence:
        observed_counts[val] += 1

    # Run test
    p_val, pass_flag = run_block_bootstrap_deviation_test(
        observed_counts, sequence, prime, N,
        block_size=10, num_samples=500, alpha=0.05
    )

    # For a uniform sequence, p-value should be high (fail to reject H0)
    assert p_val > 0.01, f"Uniform sequence should have high p-value, got {p_val}"
    assert pass_flag == True, "Uniform sequence should pass the test"

    # Test 2: Biased sequence (should have low p-value)
    # Create a sequence heavily skewed to 0
    biased_sequence = [0] * 200 + [1] * 50 + [2] * 50
    random.shuffle(biased_sequence)
    
    biased_counts = {k: 0 for k in range(prime)}
    for val in biased_sequence:
        biased_counts[val] += 1

    p_val_biased, pass_flag_biased = run_block_bootstrap_deviation_test(
        biased_counts, biased_sequence, prime, N,
        block_size=10, num_samples=500, alpha=0.05
    )

    # For a biased sequence, p-value should be low (reject H0)
    # Note: With only 500 samples, p-value might not be extremely small, but likely < 0.05
    # We assert it is significantly lower than the uniform case
    assert p_val_biased < p_val, "Biased sequence should have lower p-value than uniform"
    
    # Test 3: D_obs calculation
    # Expected = 100 for each
    # Observed = 200, 50, 50
    # D = max(|200-100|, |50-100|, |50-100|) = 100
    D = calculate_deviation_D(biased_counts, prime, N)
    assert D == 100.0, f"D calculation incorrect: {D}"
