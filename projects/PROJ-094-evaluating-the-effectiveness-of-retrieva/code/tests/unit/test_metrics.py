"""
Unit tests for metrics calculations.
"""
import pytest
import math
from src.models.metrics import (
    precision_at_k,
    recall_at_k,
    dcg_at_k,
    ideal_dcg_at_k,
    ndcg_at_k,
    evaluate_metrics
)

class TestPrecisionAtK:
    def test_perfect_precision(self):
        relevant = {1, 2, 3}
        retrieved = [1, 2, 3, 4, 5]
        assert precision_at_k(relevant, retrieved, 3) == 1.0

    def test_zero_precision(self):
        relevant = {1, 2, 3}
        retrieved = [4, 5, 6, 7]
        assert precision_at_k(relevant, retrieved, 3) == 0.0

    def test_partial_precision(self):
        relevant = {1, 2, 3}
        retrieved = [1, 4, 5, 2]
        # Top 2: [1, 4] -> 1 hit out of 2
        assert precision_at_k(relevant, retrieved, 2) == 0.5

    def test_k_larger_than_retrieved(self):
        relevant = {1, 2}
        retrieved = [1]
        # k=5, but only 1 item retrieved
        assert precision_at_k(relevant, retrieved, 5) == 1.0

    def test_empty_retrieved(self):
        relevant = {1, 2}
        retrieved = []
        assert precision_at_k(relevant, retrieved, 3) == 0.0

    def test_k_zero(self):
        relevant = {1, 2}
        retrieved = [1, 2]
        assert precision_at_k(relevant, retrieved, 0) == 0.0

class TestRecallAtK:
    def test_perfect_recall(self):
        relevant = {1, 2, 3}
        retrieved = [1, 2, 3, 4, 5]
        assert recall_at_k(relevant, retrieved, 3) == 1.0

    def test_zero_recall(self):
        relevant = {1, 2, 3}
        retrieved = [4, 5, 6]
        assert recall_at_k(relevant, retrieved, 3) == 0.0

    def test_partial_recall(self):
        relevant = {1, 2, 3}
        retrieved = [1, 4, 5]
        # Top 3: [1, 4, 5] -> 1 hit out of 3 relevant
        assert recall_at_k(relevant, retrieved, 3) == 1/3

    def test_k_larger_than_relevant(self):
        relevant = {1, 2}
        retrieved = [1, 2, 3, 4, 5]
        # All relevant are in top 3
        assert recall_at_k(relevant, retrieved, 3) == 1.0

    def test_empty_relevant(self):
        relevant = set()
        retrieved = [1, 2, 3]
        assert recall_at_k(relevant, retrieved, 3) == 0.0

class TestDcgAtK:
    def test_dcg_perfect_order(self):
        relevant = {1, 2}
        retrieved = [1, 2, 3]
        # i=0: 1/log2(2) = 1.0
        # i=1: 1/log2(3) = 1/1.585...
        expected = 1.0 + 1.0 / math.log2(3)
        assert abs(dcg_at_k(relevant, retrieved, 3) - expected) < 1e-6

    def test_dcg_partial_hits(self):
        relevant = {1}
        retrieved = [2, 1, 3]
        # i=0: 0
        # i=1: 1/log2(3)
        expected = 1.0 / math.log2(3)
        assert abs(dcg_at_k(relevant, retrieved, 3) - expected) < 1e-6

    def test_dcg_no_hits(self):
        relevant = {1}
        retrieved = [2, 3, 4]
        assert dcg_at_k(relevant, retrieved, 3) == 0.0

class TestIdealDcgAtK:
    def test_idcg_perfect(self):
        relevant = {1, 2}
        # Ideal: [1, 2, ...]
        expected = 1.0 + 1.0 / math.log2(3)
        assert abs(ideal_dcg_at_k(relevant, 3) - expected) < 1e-6

    def test_idcg_zero_relevant(self):
        relevant = set()
        assert ideal_dcg_at_k(relevant, 3) == 0.0

    def test_idcg_k_limited(self):
        relevant = {1, 2, 3}
        # k=2, so only first 2 relevant count
        expected = 1.0 + 1.0 / math.log2(3)
        assert abs(ideal_dcg_at_k(relevant, 2) - expected) < 1e-6

class TestNdcgAtK:
    def test_ndcg_perfect(self):
        relevant = {1, 2}
        retrieved = [1, 2, 3]
        assert abs(ndcg_at_k(relevant, retrieved, 3) - 1.0) < 1e-6

    def test_ndcg_zero(self):
        relevant = {1}
        retrieved = [2, 3, 4]
        assert ndcg_at_k(relevant, retrieved, 3) == 0.0

    def test_ndcg_partial(self):
        relevant = {1, 2}
        retrieved = [3, 1, 2]
        # DCG: 0 + 1/log2(3) + 1/log2(4)
        # IDCG: 1 + 1/log2(3)
        dcg_val = 1.0 / math.log2(3) + 1.0 / math.log2(4)
        idcg_val = 1.0 + 1.0 / math.log2(3)
        expected = dcg_val / idcg_val
        assert abs(ndcg_at_k(relevant, retrieved, 3) - expected) < 1e-6

    def test_ndcg_no_relevant(self):
        relevant = set()
        retrieved = [1, 2, 3]
        # IDCG is 0, so ndcg should be 0
        assert ndcg_at_k(relevant, retrieved, 3) == 0.0

class TestEvaluateMetrics:
    def test_all_metrics_calculated(self):
        relevant = {1, 2, 3}
        retrieved = [1, 2, 4, 5, 3]
        k_values = [1, 3, 5]
        
        results = evaluate_metrics(relevant, retrieved, k_values)
        
        # Check all expected keys exist
        for k in k_values:
            assert f'P@{k}' in results
            assert f'R@{k}' in results
            assert f'nDCG@{k}' in results

    def test_metrics_ranges(self):
        relevant = {1, 2}
        retrieved = [1, 2, 3]
        results = evaluate_metrics(relevant, retrieved, [1, 3])
        
        for k in [1, 3]:
            assert 0.0 <= results[f'P@{k}'] <= 1.0
            assert 0.0 <= results[f'R@{k}'] <= 1.0
            assert 0.0 <= results[f'nDCG@{k}'] <= 1.0