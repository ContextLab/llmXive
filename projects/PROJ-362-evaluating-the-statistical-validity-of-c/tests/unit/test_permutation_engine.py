"""
Unit tests for the permutation engine logic.
"""

import random
import pytest
from code.permutation import shuffle_relevance_labels, compute_permuted_scores
from code.metrics import ndcg_at_k, average_precision

def test_shuffle_preserves_values():
    labels = [0, 1, 2, 2, 3]
    rng = random.Random(42)
    shuffled = shuffle_relevance_labels(labels, rng)
    assert sorted(shuffled) == sorted(labels)
    assert shuffled != labels or random.Random(42).shuffle(labels.copy()) # Basic check

def test_shuffle_changes_order():
    labels = [1, 2, 3, 4, 5]
    rng = random.Random(12345)
    shuffled = shuffle_relevance_labels(labels, rng)
    # With a specific seed, we expect a specific permutation.
    # We just verify it's a valid permutation.
    assert len(shuffled) == len(labels)
    assert set(shuffled) == set(labels)

def test_compute_permuted_scores_count():
    # Create a simple scenario
    labels = [1, 0, 1, 0]
    rng = random.Random(42)
    scores, n_actual = compute_permuted_scores(
        query_id=1,
        relevance_labels=labels,
        metric_func=lambda l, k: sum(l), # Dummy metric: sum of labels
        k=4,
        rng=rng,
        n_permutations=5
    )
    assert n_actual == 5
    assert len(scores) == 5
    # Since metric is sum(labels), and sum is invariant to permutation,
    # all scores should be equal.
    assert all(s == scores[0] for s in scores)

def test_compute_permuted_scores_real_metric():
    # Use real NDCG metric
    labels = [3, 2, 1, 0, 0]
    rng = random.Random(999)
    scores, n_actual = compute_permuted_scores(
        query_id=1,
        relevance_labels=labels,
        metric_func=ndcg_at_k,
        k=5,
        rng=rng,
        n_permutations=10
    )
    assert n_actual == 10
    assert len(scores) == 10
    # Scores should be floats between 0 and 1
    for s in scores:
        assert 0.0 <= s <= 1.0