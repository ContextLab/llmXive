import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_networks import generate_nanowire_network, calculate_average_degree, validate_degree_bounds

def test_avg_degree_within_tolerance():
    N = 100
    target_degree = 4
    seed = 42
    
    G = generate_nanowire_network(N, 0.1, target_degree, seed)
    avg_deg = calculate_average_degree(G)
    
    # Check if within 5% tolerance
    tolerance = 0.05 * target_degree
    assert abs(avg_deg - target_degree) <= tolerance, f"Average degree {avg_deg} not within {tolerance} of {target_degree}"

def test_validate_degree_bounds():
    assert validate_degree_bounds(4, 100) == True
    assert validate_degree_bounds(0, 100) == True
    assert validate_degree_bounds(99, 100) == True
    assert validate_degree_bounds(100, 100) == False
    assert validate_degree_bounds(-1, 100) == False
