import pytest
import json
import os
import sys
import numpy as np
from typing import Dict, List

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats import (
    run_deviation_test,
    calculate_deviation_D,
    block_bootstrap_residues,
    StatisticalResult,
    calculate_chi_squared_statistic,
    check_bin_counts_and_fallback
)

def test_calculate_deviation_D():
    """Test D calculation with known values."""
    # N=100, prime=5, expected=20
    # Counts: [18, 22, 20, 20, 20] -> max dev = 2
    counts = {0: 18, 1: 22, 2: 20, 3: 20, 4: 20}
    D = calculate_deviation_D(counts, 5, 100)
    assert D == 2.0

def test_block_bootstrap_residues():
    """Test that block bootstrap produces sequences of correct length."""
    seq = list(range(100))
    boot_seqs = block_bootstrap_residues(seq, block_size=10, num_samples=5)
    assert len(boot_seqs) == 5
    assert all(len(s) == 100 for s in boot_seqs)

def test_run_deviation_test():
    """Test the full deviation test (T019b) logic."""
    # Create a synthetic sequence
    N = 1000
    prime = 5
    # Uniform-ish sequence
    seq = [i % prime for i in range(N)]
    
    # Observed counts (perfectly uniform)
    counts = {k: N//prime for k in range(prime)}
    
    D_obs, p_val = run_deviation_test(counts, prime, seq, N, num_samples=100)
    
    # D_obs should be 0 or very small
    assert D_obs == 0.0
    # P-value should be high for uniform data
    assert p_val > 0.05

def test_check_bin_counts_and_fallback():
    """Test fallback trigger logic."""
    # Large N, uniform counts -> no fallback
    counts_large = {k: 10000 for k in range(5)}
    assert not check_bin_counts_and_fallback(counts_large, 5, 50000)
    
    # Small N -> fallback
    counts_small = {k: 2 for k in range(5)}
    assert check_bin_counts_and_fallback(counts_small, 5, 10)

def test_calculate_chi_squared_statistic():
    """Test Chi-squared calculation."""
    # Perfectly uniform
    counts = {0: 20, 1: 20, 2: 20, 3: 20, 4: 20}
    chi_sq, p_val = calculate_chi_squared_statistic(counts, 5, 100)
    assert chi_sq == 0.0
    # p-value should be 1.0 (or very close)
    assert p_val >= 0.99

def test_run_deviation_test_with_biased_data():
    """Test deviation test with biased data."""
    N = 1000
    prime = 5
    # Biased sequence: 0 appears more often
    seq = [0]*400 + [i % prime for i in range(600)]
    
    # Counts: 0->400, others->150
    counts = {0: 400, 1: 150, 2: 150, 3: 150, 4: 150}
    
    D_obs, p_val = run_deviation_test(counts, prime, seq, N, num_samples=200)
    
    # D_obs should be large
    expected = 200
    assert D_obs == expected
    # P-value should be low
    assert p_val < 0.1