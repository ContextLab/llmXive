"""
Contract test for generate_reference.py.

Verifies that:
1. The reference CSV file is created at the expected path.
2. The file contains the correct columns: 'n', 'p_P(n)'.
3. The values for n in [1, 100] are non-negative integers.
4. Known small values match mathematical expectations (e.g., p_P(n)=0 for n < 2).
"""
import os
import csv
import pytest
import numpy as np

REFERENCE_PATH = "tests/data/reference_values.csv"

@pytest.fixture(scope="module")
def reference_data():
    """Load the reference CSV file."""
    if not os.path.exists(REFERENCE_PATH):
        pytest.skip(f"Reference file {REFERENCE_PATH} not found. Run generate_reference.py first.")
    
    data = {}
    with open(REFERENCE_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            count = int(row['p_P(n)'])
            data[n] = count
    return data

def test_file_exists():
    """Test that the reference file is created."""
    assert os.path.exists(REFERENCE_PATH), f"Reference file {REFERENCE_PATH} does not exist."

def test_columns_present(reference_data):
    """Test that required columns are present."""
    # Load file to check header
    with open(REFERENCE_PATH, 'r') as f:
        reader = csv.DictReader(f)
        assert 'n' in reader.fieldnames, "Column 'n' is missing."
        assert 'p_P(n)' in reader.fieldnames, "Column 'p_P(n)' is missing."

def test_range_coverage(reference_data):
    """Test that all n in [1, 100] are present."""
    expected_n = set(range(1, 101))
    actual_n = set(reference_data.keys())
    assert actual_n == expected_n, f"Missing n values: {expected_n - actual_n}"

def test_non_negative_integers(reference_data):
    """Test that all p_P(n) values are non-negative integers."""
    for n, count in reference_data.items():
        assert isinstance(count, int), f"p_P({n}) is not an integer: {type(count)}"
        assert count >= 0, f"p_P({n}) is negative: {count}"

def test_known_small_values(reference_data):
    """Test known small values of p_P(n)."""
    # p_P(n) = 0 for n < 2 (no primes <= 1)
    assert reference_data[1] == 0, "p_P(1) should be 0"
    
    # p_P(2) = 1 (partition: {2})
    assert reference_data[2] == 1, "p_P(2) should be 1"
    
    # p_P(3) = 1 (partition: {3})
    assert reference_data[3] == 1, "p_P(3) should be 1"
    
    # p_P(4) = 0 (no distinct prime partition: 2+2 not allowed, 3+1 not prime)
    assert reference_data[4] == 0, "p_P(4) should be 0"
    
    # p_P(5) = 1 (partition: {5})
    assert reference_data[5] == 1, "p_P(5) should be 1"
    
    # p_P(6) = 1 (partition: {2, 4}? No, 4 not prime. {3, 3}? No, distinct. {6}? No. Wait: 2+? 2+4 no. 3+? 3+3 no. 5+? 5+1 no. 
    # Actually: 2+? 2+4 no. 3+? 3+3 no. 5+? 5+1 no. 
    # Wait: 2+? 2+4 no. 3+? 3+3 no. 5+? 5+1 no. 
    # Let's recompute: primes <= 6: 2, 3, 5.
    # Partitions of 6 into distinct primes:
    # - 2 + ? (needs 4, not prime)
    # - 3 + ? (needs 3, not distinct)
    # - 5 + ? (needs 1, not prime)
    # - 2 + 3 + ? (needs 1, not prime)
    # So p_P(6) = 0? 
    # But wait: 2+3=5, not 6. 2+5=7. 3+5=8.
    # So p_P(6) = 0.
    assert reference_data[6] == 0, "p_P(6) should be 0"
    
    # p_P(7): 
    # - 2+5=7 (valid: distinct primes)
    # - 7 (valid)
    # So p_P(7) = 2
    assert reference_data[7] == 2, "p_P(7) should be 2"
    
    # p_P(8):
    # - 3+5=8
    # - 2+? (needs 6, not prime)
    # - 7+1 (no)
    # So p_P(8) = 1
    assert reference_data[8] == 1, "p_P(8) should be 1"
    
    # p_P(9):
    # - 2+7=9
    # - 3+? (needs 6, no)
    # - 5+? (needs 4, no)
    # - 2+3+? (needs 4, no)
    # So p_P(9) = 1
    assert reference_data[9] == 1, "p_P(9) should be 1"
    
    # p_P(10):
    # - 3+7=10
    # - 2+? (needs 8, no)
    # - 5+5 (not distinct)
    # - 2+3+5=10
    # So p_P(10) = 2
    assert reference_data[10] == 2, "p_P(10) should be 2"

def test_monotonicity_not_required(reference_data):
    """
    Test that p_P(n) is not necessarily monotonic (due to prime gaps).
    This is a sanity check for the nature of the function.
    """
    # Just ensure the data is consistent and non-trivial
    values = list(reference_data.values())
    assert len(values) == 100
    assert any(v > 0 for v in values), "Expected at least some positive partition counts."
    assert max(values) > 0, "Maximum value should be positive."