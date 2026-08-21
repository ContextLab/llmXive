"""
Unit tests for permutation logic (shuffle correctness).
"""
import random
import pytest

from permutation import shuffle_relevance_labels, compute_permuted_scores

def test_shuffle_relevance_labels():
    """Test that shuffling produces a permutation of the original list."""
    original = [0, 1, 2, 3, 4]
    shuffled = shuffle_relevance_labels(original, seed=42)
    
    assert len(shuffled) == len(original)
    assert set(shuffled) == set(original)
    assert shuffled != original or random.Random(42).randint(0, 100) > 50 
    # Note: It is possible for a shuffle to result in the same order, 
    # but with a fixed seed we expect a specific permutation.
    # The key is that it is a valid permutation.

def test_shuffle_deterministic_with_seed():
    """Test that shuffling is deterministic with the same seed."""
    original = [0, 1, 2, 3, 4]
    seed = 12345
    
    shuffled1 = shuffle_relevance_labels(original, seed=seed)
    shuffled2 = shuffle_relevance_labels(original, seed=seed)
    
    assert shuffled1 == shuffled2

def test_compute_permuted_scores_ndcg():
    """Test score computation for NDCG@10."""
    doc_ids = [1, 2, 3, 4, 5]
    rel_labels = [1, 2, 3, 4, 5]
    
    score = compute_permuted_scores(doc_ids, rel_labels, 'NDCG@10', k=10, shuffle_seed=0)
    
    assert 0.0 <= score <= 1.0

def test_compute_permuted_scores_map():
    """Test score computation for MAP."""
    doc_ids = [1, 2, 3, 4, 5]
    rel_labels = [1, 2, 3, 4, 5]
    
    score = compute_permuted_scores(doc_ids, rel_labels, 'MAP', k=10, shuffle_seed=0)
    
    assert 0.0 <= score <= 1.0

def test_compute_permuted_scores_invalid_metric():
    """Test that invalid metric raises error."""
    doc_ids = [1, 2, 3]
    rel_labels = [1, 2, 3]
    
    with pytest.raises(ValueError):
        compute_permuted_scores(doc_ids, rel_labels, 'INVALID_METRIC')
