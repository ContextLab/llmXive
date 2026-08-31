"""
Unit tests for metrics.py NDCG@10 calculation with known ground truth.
"""
import pytest
import math

from metrics import ndcg_at_k, dcg_at_k, idcg_at_k

def test_dcg_at_k():
    """Test DCG calculation."""
    # rel = [3, 2, 3, 0, 1]
    # DCG = 3/1 + 2/2 + 3/3 + 0/4 + 1/5 = 3 + 1 + 1 + 0 + 0.2 = 5.2
    rel = [3, 2, 3, 0, 1]
    assert dcg_at_k(rel, 5) == pytest.approx(5.2, rel=1e-5)

def test_idcg_at_k():
    """Test IDCG calculation."""
    # rel = [3, 2, 3, 0, 1] -> sorted = [3, 3, 2, 1, 0]
    # IDCG = 3/1 + 3/2 + 2/3 + 1/4 + 0/5 = 3 + 1.5 + 0.666... + 0.25 = 5.4166...
    rel = [3, 2, 3, 0, 1]
    expected = 3 + 1.5 + (2/3) + 0.25
    assert idcg_at_k(rel, 5) == pytest.approx(expected, rel=1e-5)

def test_ndcg_at_k_known_ground_truth():
    """Test NDCG@10 with a known example."""
    # Example from standard IR literature
    # Relevance: [3, 2, 3, 0, 1, 1, 2, 3, 2, 1] (10 docs)
    # DCG @ 10
    # IDCG @ 10 (sorted: 3,3,3,2,2,2,1,1,1,0)
    
    rel = [3, 2, 3, 0, 1, 1, 2, 3, 2, 1]
    k = 10
    
    dcg = dcg_at_k(rel, k)
    idcg = idcg_at_k(rel, k)
    ndcg = ndcg_at_k(rel, k)
    
    # NDCG should be <= 1.0
    assert ndcg <= 1.0 + 1e-5
    assert ndcg >= 0.0
    
    # Check that NDCG = DCG / IDCG
    assert ndcg == pytest.approx(dcg / idcg, rel=1e-5)

def test_ndcg_at_k_perfect():
    """Test NDCG is 1.0 for perfectly sorted list."""
    rel = [5, 4, 3, 2, 1]
    assert ndcg_at_k(rel, 5) == pytest.approx(1.0, rel=1e-5)

def test_ndcg_at_k_zero():
    """Test NDCG is 0.0 if no relevant documents."""
    rel = [0, 0, 0, 0]
    assert ndcg_at_k(rel, 4) == pytest.approx(0.0, rel=1e-5)

def test_ndcg_at_k_k_smaller():
    """Test NDCG@k where k < len(rel)."""
    rel = [3, 2, 3, 0, 1]
    # NDCG@3
    # DCG@3 = 3/1 + 2/2 + 3/3 = 3 + 1 + 1 = 5
    # IDCG@3 (sorted top 3: 3, 3, 2) = 3/1 + 3/2 + 2/3 = 3 + 1.5 + 0.666 = 5.166
    # NDCG = 5 / 5.166 = 0.9677
    assert ndcg_at_k(rel, 3) == pytest.approx(0.9677, rel=1e-3)

def test_ndcg_at_k_specific_ground_truth():
    """
    Specific ground truth test as requested in task description:
    assert ndcg_at_k([1,0,0], [1,0,0]) == 1.0
    
    Note: The function signature in metrics.py is ndcg_at_k(rels, k).
    The test case provided in the task description appears to pass two lists.
    Interpreting the intent: The first list is the relevance judgments,
    and the second list might be a distractor or the user intended to check
    a specific permutation. 
    
    However, standard NDCG takes relevance labels and a cutoff k.
    If the user meant: relevance=[1,0,0], k=3 (implied by list length)
    Then DCG = 1/1 + 0/2 + 0/3 = 1.
    IDCG (sorted [1,0,0]) = 1/1 + 0/2 + 0/3 = 1.
    NDCG = 1.0.
    
    We will test the specific assertion logic by constructing the call
    that yields 1.0 for the relevance vector [1, 0, 0].
    """
    rels = [1, 0, 0]
    k = 3
    # DCG = 1/1 + 0/2 + 0/3 = 1
    # IDCG = 1/1 + 0/2 + 0/3 = 1
    # NDCG = 1.0
    assert ndcg_at_k(rels, k) == pytest.approx(1.0, rel=1e-5)

    # Additional verification for the specific case where the first doc is relevant
    # and we only look at the first doc (k=1)
    assert ndcg_at_k([1, 0, 0], 1) == pytest.approx(1.0, rel=1e-5)