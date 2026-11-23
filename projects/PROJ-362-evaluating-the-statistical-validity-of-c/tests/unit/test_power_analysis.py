"""
Unit tests for power_analysis.py
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from power_analysis import (
    bootstrap_resample_indices,
    swap_top_k_relevance,
    estimate_power,
    calculate_mdes_power
)

@pytest.fixture
def sample_qrels():
    """Generate a small sample of qrels for testing."""
    return [
        {'query_id': 1, 'doc_id': 100, 'relevance': 3},
        {'query_id': 1, 'doc_id': 101, 'relevance': 3},
        {'query_id': 1, 'doc_id': 102, 'relevance': 2},
        {'query_id': 1, 'doc_id': 103, 'relevance': 2},
        {'query_id': 1, 'doc_id': 104, 'relevance': 1},
        {'query_id': 1, 'doc_id': 105, 'relevance': 1},
        {'query_id': 1, 'doc_id': 106, 'relevance': 0},
        {'query_id': 1, 'doc_id': 107, 'relevance': 0},
        {'query_id': 1, 'doc_id': 108, 'relevance': 0},
        {'query_id': 1, 'doc_id': 109, 'relevance': 0},
    ]

def test_bootstrap_resample_indices():
    """Test that bootstrap resampling returns correct length and values."""
    n = 100
    indices = bootstrap_resample_indices(n, seed=42)
    assert len(indices) == n
    assert np.all((indices >= 0) & (indices < n))
    
    # Check reproducibility
    indices_2 = bootstrap_resample_indices(n, seed=42)
    np.testing.assert_array_equal(indices, indices_2)

def test_swap_top_k_relevance(sample_qrels):
    """Test that swap_top_k_relevance actually changes values."""
    original_rels = [q['relevance'] for q in sample_qrels]
    swapped_qrels = swap_top_k_relevance(sample_qrels, k_swap=2, seed=123)
    swapped_rels = [q['relevance'] for q in swapped_qrels]
    
    assert len(original_rels) == len(swapped_rels)
    # Check that at least some values changed
    assert original_rels != swapped_rels
    
    # Check that high relevance docs got lower values
    # Original top 2 are 3, 3. Bottom 2 are 0, 0.
    # After swap, top 2 should be 0, 0 (or similar low values)
    # Note: The implementation swaps top-k with bottom-k values.
    # We verify that the sum changed or specific indices changed.
    assert sum(swapped_rels) != sum(original_rels) or (sum(swapped_rels) == sum(original_rels) and swapped_rels != original_rels)

def test_estimate_power():
    """Test power estimation logic."""
    observed = 0.8
    null_scores = [0.4, 0.5, 0.6, 0.5, 0.65] # Low scores
    swapped_scores = [0.9, 0.95, 0.85, 0.92, 0.88] # High scores (H1)
    
    power = estimate_power(observed, null_scores, swapped_scores, alpha=0.05)
    
    # Critical value should be high (e.g., 95th percentile of null ~ 0.65)
    # All swapped scores are > 0.65, so power should be 1.0
    assert power == 1.0
    
    # Test with low power scenario
    swapped_scores_low = [0.5, 0.55, 0.6, 0.52, 0.58]
    power_low = estimate_power(observed, null_scores, swapped_scores_low, alpha=0.05)
    assert power_low < 0.5 # Most should be below critical value

def test_calculate_mdes_power(sample_qrels):
    """Test MDES calculation with a mock scenario."""
    observed_score = 0.5
    null_scores = [0.4, 0.45, 0.5, 0.48, 0.42] * 20 # Simulated null
    
    # This is a heavy test, so we limit bootstrap samples
    mdes, power = calculate_mdes_power(
        sample_qrels, 
        observed_score, 
        null_scores, 
        n_bootstrap=5 # Very small for unit test speed
    )
    
    assert 0.001 <= mdes <= 0.500
    assert 0.0 <= power <= 1.0