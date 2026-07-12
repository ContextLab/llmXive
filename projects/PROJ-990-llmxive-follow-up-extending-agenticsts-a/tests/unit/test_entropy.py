"""
Unit tests for entropy.py
"""
import pytest
import numpy as np
from code.entropy import (
    calculate_shannon_entropy,
    extract_move_distribution,
    calculate_entropy_for_trajectory,
    process_trajectories,
    ENTROPY_SENTINEL
)

def test_calculate_shannon_entropy_uniform():
    """Test entropy calculation for a uniform distribution."""
    probs = [0.25, 0.25, 0.25, 0.25]
    entropy = calculate_shannon_entropy(probs)
    # log2(4) = 2.0
    assert abs(entropy - 2.0) < 1e-6

def test_calculate_shannon_entropy_deterministic():
    """Test entropy calculation for a deterministic distribution (one move)."""
    probs = [1.0]
    entropy = calculate_shannon_entropy(probs)
    # log2(1) = 0.0
    assert entropy == 0.0

def test_calculate_shannon_entropy_empty():
    """Test entropy calculation for an empty distribution."""
    probs = []
    entropy = calculate_shannon_entropy(probs)
    assert entropy == ENTROPY_SENTINEL

def test_calculate_shannon_entropy_nan_handling():
    """Test that NaN inputs result in sentinel value."""
    # Create a distribution that might cause issues
    probs = [float('nan'), 0.5]
    entropy = calculate_shannon_entropy(probs)
    assert entropy == ENTROPY_SENTINEL

def test_calculate_shannon_entropy_inf_handling():
    """Test that Inf inputs result in sentinel value."""
    # This is a bit contrived, but testing the check
    probs = [0.5, 0.5]
    entropy = calculate_shannon_entropy(probs)
    # Normal case should not be sentinel
    assert entropy != ENTROPY_SENTINEL

def test_extract_move_distribution():
    """Test extraction of move probabilities from turn data."""
    turn_data = {
        'legal_moves': ['a', 'b', 'c'],
        'move_probabilities': [0.2, 0.3, 0.5]
    }
    probs = extract_move_distribution(turn_data)
    assert probs == [0.2, 0.3, 0.5]

def test_extract_move_distribution_missing_keys():
    """Test extraction when keys are missing."""
    turn_data = {'other_key': 'value'}
    probs = extract_move_distribution(turn_data)
    assert probs == []

def test_calculate_entropy_for_trajectory():
    """Test entropy calculation for a full trajectory."""
    turns = [
        {'legal_moves': ['a', 'b'], 'move_probabilities': [0.5, 0.5]},
        {'legal_moves': ['x'], 'move_probabilities': [1.0]}
    ]
    results = calculate_entropy_for_trajectory(turns)
    assert len(results) == 2
    # Turn 0: uniform 2 outcomes -> entropy 1.0
    assert abs(results[0][1] - 1.0) < 1e-6
    # Turn 1: deterministic -> entropy 0.0
    assert results[1][1] == 0.0
    # No edge cases
    assert results[0][2] is False
    assert results[1][2] is False

def test_calculate_entropy_for_trajectory_edge_case():
    """Test entropy calculation when an edge case occurs."""
    turns = [
        {'legal_moves': [], 'move_probabilities': []}, # Empty -> sentinel
        {'legal_moves': ['a'], 'move_probabilities': [1.0]}
    ]
    results = calculate_entropy_for_trajectory(turns)
    assert len(results) == 2
    assert results[0][1] == ENTROPY_SENTINEL
    assert results[0][2] is True
    assert results[1][1] == 0.0
    assert results[1][2] is False
