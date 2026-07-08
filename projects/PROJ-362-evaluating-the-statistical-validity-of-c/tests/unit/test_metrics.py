import pytest
from metrics import ndcg_at_k, dcg_at_k, idcg_at_k, discount_factor

def test_discount_factor():
    # discount_factor(i) = 1 / log2(i + 2)
    # i=0 -> 1/log2(2) = 1/1 = 1.0
    assert discount_factor(0) == pytest.approx(1.0)
    # i=1 -> 1/log2(3) ≈ 0.6309
    assert discount_factor(1) == pytest.approx(0.6309297535714574)

def test_dcg_at_k_simple():
    # Relevance: [3, 2, 3, 0, 1]
    # DCG@2 = rel[0]/log2(2) + rel[1]/log2(3) = 3/1 + 2/0.6309...
    rel = [3, 2, 3, 0, 1]
    # DCG@1 = 3
    assert dcg_at_k(rel, k=1) == pytest.approx(3.0)
    # DCG@2 = 3 + 2/log2(3)
    expected_dcg_2 = 3 + 2 / (1.5849625007211563)
    assert dcg_at_k(rel, k=2) == pytest.approx(expected_dcg_2)

def test_idcg_at_k_perfect():
    # Ideal relevance: [3, 3, 2, 1, 0] for k=5
    ideal_rel = [3, 3, 2, 1, 0]
    # IDCG@5 is the DCG of the sorted list
    expected_idcg = 0
    for i, r in enumerate(ideal_rel):
        expected_idcg += r / (1 + math.log2(i + 2))
    
    import math
    assert idcg_at_k(ideal_rel, k=5) == pytest.approx(expected_idcg)

def test_ndcg_at_k_known_values():
    """
    Test NDCG@3 with a known ground truth scenario.
    Relevance labels: [3, 2, 3, 0, 1]
    k=3
    
    Actual DCG@3:
    i=0: 3 / log2(2) = 3.0
    i=1: 2 / log2(3) ≈ 1.2618
    i=2: 3 / log2(4) = 1.5
    Total DCG@3 ≈ 5.7618
    
    Ideal order (sorted desc): [3, 3, 2, 1, 0]
    IDCG@3:
    i=0: 3 / log2(2) = 3.0
    i=1: 3 / log2(3) ≈ 1.8928
    i=2: 2 / log2(4) = 1.0
    Total IDCG@3 ≈ 5.8928
    
    NDCG@3 = DCG@3 / IDCG@3
    """
    rel = [3, 2, 3, 0, 1]
    k = 3
    
    import math
    # Calculate expected manually
    dcg_val = 0
    for i in range(min(k, len(rel))):
        dcg_val += rel[i] / math.log2(i + 2)
    
    sorted_rel = sorted(rel, reverse=True)
    idcg_val = 0
    for i in range(min(k, len(sorted_rel))):
        idcg_val += sorted_rel[i] / math.log2(i + 2)
    
    expected_ndcg = dcg_val / idcg_val if idcg_val > 0 else 0.0
    
    actual_ndcg = ndcg_at_k(rel, k=k)
    
    assert actual_ndcg == pytest.approx(expected_ndcg, rel=1e-5)

def test_ndcg_at_k_perfect_ranking():
    # If the list is already sorted descending, NDCG should be 1.0
    rel = [3, 2, 1, 0]
    k = 4
    assert ndcg_at_k(rel, k=k) == pytest.approx(1.0)

def test_ndcg_at_k_zero_relevance():
    # All zeros should result in 0.0
    rel = [0, 0, 0, 0]
    k = 4
    assert ndcg_at_k(rel, k=k) == pytest.approx(0.0)

def test_ndcg_at_k_k_greater_than_len():
    # k larger than list length should just use the whole list
    rel = [3, 2, 1]
    k = 10
    # Should calculate NDCG for the whole list
    assert ndcg_at_k(rel, k=k) == pytest.approx(1.0) # Already sorted

def test_ndcg_at_k_unsorted():
    # Reverse sorted: [0, 1, 2, 3]
    rel = [0, 1, 2, 3]
    k = 4
    # Ideal: [3, 2, 1, 0]
    # DCG: 0/1 + 1/log2(3) + 2/log2(4) + 3/log2(5)
    # IDCG: 3/1 + 2/log2(3) + 1/log2(4) + 0/log2(5)
    import math
    dcg = 0 + 1/math.log2(3) + 2/2 + 3/math.log2(5)
    idcg = 3 + 2/math.log2(3) + 1/2 + 0
    expected = dcg / idcg
    assert ndcg_at_k(rel, k=k) == pytest.approx(expected, rel=1e-5)
