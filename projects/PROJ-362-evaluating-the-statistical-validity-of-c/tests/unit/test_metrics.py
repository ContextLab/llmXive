"""
Unit tests for metrics.py NDCG@10 and other metric calculations.
"""

import pytest
from code.metrics import discount_factor, dcg_at_k, idcg_at_k, ndcg_at_k, average_precision

class TestDiscountFactor:
    def test_rank_1(self):
        # log2(2) = 1.0
        assert discount_factor(1) == 1.0
    
    def test_rank_3(self):
        # log2(4) = 2.0 -> 1/2 = 0.5
        assert discount_factor(3) == 0.5

class TestDcgAtK:
    def test_simple_dcg(self):
        # Labels: [3, 2, 2, 1]
        # Rank 1: 3 / log2(2) = 3
        # Rank 2: 2 / log2(3) ~ 1.26
        # DCG = 3 + 1.26...
        labels = [3, 2, 2, 1]
        dcg = dcg_at_k(labels, k=2)
        assert dcg > 3.0
        assert dcg < 4.0

    def test_dcg_all(self):
        labels = [1, 0, 0]
        # Rank 1: 1/1 = 1.
        # Rank 2: 0.
        # Rank 3: 0.
        assert dcg_at_k(labels) == 1.0

class TestIdcgAtK:
    def test_idcg_ideal(self):
        # Ideal order: [3, 2, 1, 0]
        # DCG of this should be the IDCG of [0, 1, 2, 3]
        ideal = [3, 2, 1, 0]
        shuffled = [0, 1, 2, 3]
        assert idcg_at_k(shuffled) == dcg_at_k(ideal)

class TestNdcgAtK:
    def test_ndcg_perfect(self):
        # Perfect ranking: [3, 2, 1]
        labels = [3, 2, 1]
        assert ndcg_at_k(labels) == 1.0

    def test_ndcg_worst(self):
        # Worst ranking (all 0s or 0s at top): [0, 0, 3]
        # DCG will be low, IDCG will be high (based on sorted [3, 0, 0])
        labels = [0, 0, 3]
        ndcg = ndcg_at_k(labels)
        assert 0.0 <= ndcg < 1.0

    def test_ndcg_k_cutoff(self):
        # [3, 2, 1, 0]
        # k=2: only considers [3, 2]
        labels = [3, 2, 1, 0]
        ndcg_k2 = ndcg_at_k(labels, k=2)
        # k=4: considers all
        ndcg_k4 = ndcg_at_k(labels, k=4)
        # Since [3, 2] is the top of the ideal, NDCG@2 should be 1.0
        assert ndcg_k2 == 1.0

class TestAveragePrecision:
    def test_ap_perfect(self):
        # [1, 1, 0, 0] -> Rel at 1, Rel at 2.
        # P@1 = 1/1 = 1. P@2 = 2/2 = 1. Avg = 1.
        labels = [1, 1, 0, 0]
        assert average_precision(labels) == 1.0

    def test_ap_worst(self):
        # [0, 0, 1, 1] -> Rel at 3, Rel at 4.
        # P@3 = 1/3. P@4 = 2/4 = 0.5. Avg = (0.33 + 0.5)/2 = 0.4166
        labels = [0, 0, 1, 1]
        ap = average_precision(labels)
        assert 0.41 < ap < 0.42

    def test_ap_no_relevant(self):
        labels = [0, 0, 0]
        assert average_precision(labels) == 0.0
