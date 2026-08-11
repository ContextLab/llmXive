"""
Contract test for T011: Verify generate_partitions.py output correctness.
"""
import os
import csv
import math
import pytest

def test_output_file_exists():
    """Verify that the output file is created."""
    assert os.path.exists('data/raw/partitions_raw.csv'), "Output file partitions_raw.csv not found"

def test_output_columns():
    """Verify that the output file has the correct columns."""
    with open('data/raw/partitions_raw.csv', 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        assert 'n' in headers, "Column 'n' missing"
        assert 'p_P(n)' in headers, "Column 'p_P(n)' missing"
        assert 'Q_as(n)' in headers, "Column 'Q_as(n)' missing"

def test_non_negative_counts():
    """Verify that partition counts are non-negative integers."""
    with open('data/raw/partitions_raw.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            p_val = int(row['p_P(n)'])
            q_val = float(row['Q_as(n)'])
            
            assert p_val >= 0, f"p_P({n}) is negative: {p_val}"
            assert q_val > 0, f"Q_as({n}) is non-positive: {q_val}"

def test_reference_match_small_n():
    """
    Verify that computed values match reference values for n in [1, 100].
    This validates the core DP logic against the known reference data.
    """
    # Load reference
    ref_path = 'tests/data/reference_values.csv'
    if not os.path.exists(ref_path):
        pytest.skip(f"Reference file {ref_path} not found. T008 must be run first.")
    
    ref_data = {}
    with open(ref_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ref_data[int(row['n'])] = int(row['p_P(n)'])
    
    # Load and check output
    output_path = 'data/raw/partitions_raw.csv'
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row['n'])
            if n > 100:
                break
            if n in ref_data:
                computed = int(row['p_P(n)'])
                expected = ref_data[n]
                assert computed == expected, f"Mismatch at n={n}: computed={computed}, expected={expected}"