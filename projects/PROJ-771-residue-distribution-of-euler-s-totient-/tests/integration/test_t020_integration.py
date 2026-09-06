import pytest
import json
import os
import sys
import random
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from sieve import compute_phi_linear_sieve, compute_residues
from stats import run_block_bootstrap_deviation_test, run_full_statistical_analysis, save_statistical_result, StatisticalResult

@pytest.fixture
def small_n():
    return 1000

@pytest.fixture
def prime():
    return 3

def test_t020_full_pipeline_integration(small_n, prime):
    """
    Integration test for T020:
    1. Compute phi for N
    2. Compute residues
    3. Run Block Bootstrap test (T020)
    4. Verify output structure
    """
    # Step 1: Compute Phi
    phi_values = compute_phi_linear_sieve(small_n)
    
    # Step 2: Compute Residues
    residue_sequence = [v % prime for v in phi_values]
    observed_counts = {k: 0 for k in range(prime)}
    for r in residue_sequence:
        observed_counts[r] += 1
    
    # Step 3: Run T020 (Block Bootstrap Deviation Test)
    # Note: We pass the sequence and counts
    p_val, pass_flag = run_block_bootstrap_deviation_test(
        observed_counts, residue_sequence, prime, small_n,
        block_size=10, num_samples=200, alpha=0.05
    )
    
    # Step 4: Verify results
    assert isinstance(p_val, float), "p-value must be a float"
    assert 0.0 <= p_val <= 1.0, "p-value must be between 0 and 1"
    assert isinstance(pass_flag, bool), "pass_flag must be a boolean"
    
    # Check that we got a result
    assert p_val is not None

def test_t020_save_load_result(small_n, prime):
    """
    Test saving and loading the StatisticalResult from T020.
    """
    phi_values = compute_phi_linear_sieve(small_n)
    residue_sequence = [v % prime for v in phi_values]
    
    observed_counts = {k: 0 for k in range(prime)}
    for r in residue_sequence:
        observed_counts[r] += 1
    
    # Run full analysis
    result = run_full_statistical_analysis(
        residue_sequence, prime, small_n,
        block_size=10, num_bootstrap_samples=200
    )
    
    # Save
    save_path = "data/processed/stats_test_T020.json"
    save_statistical_result(result, save_path)
    
    # Verify file exists
    assert os.path.exists(save_path), "Result file should be saved"
    
    # Load and verify
    with open(save_path, 'r') as f:
        data = json.load(f)
    
    assert 'block_bootstrap_p_value' in data
    assert 'deviation_D' in data
    assert data['prime'] == prime
    assert data['N'] == small_n

    # Cleanup
    if os.path.exists(save_path):
        os.remove(save_path)