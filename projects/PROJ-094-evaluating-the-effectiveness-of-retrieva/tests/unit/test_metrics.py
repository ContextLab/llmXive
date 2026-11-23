"""
Unit tests for metrics calculation module.
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
        """Test when all retrieved items are relevant."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "b", "c", "d", "e", "f"}
        assert precision_at_k(retrieved, relevant, 5) == 1.0

    def test_partial_precision(self):
        """Test when some retrieved items are relevant."""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = {"a", "b", "x"}
        # 2 relevant out of 5 retrieved
        assert precision_at_k(retrieved, relevant, 5) == 0.4

    def test_zero_precision(self):
        """Test when no retrieved items are relevant."""
        retrieved = ["a", "b", "c"]
        relevant = {"x", "y", "z"}
        assert precision_at_k(retrieved, relevant, 3) == 0.0

    def test_k_larger_than_retrieved(self):
        """Test when K is larger than retrieved list."""
        retrieved = ["a", "b"]
        relevant = {"a"}
        # Only 2 items retrieved, so precision is 1/2 = 0.5
        assert precision_at_k(retrieved, relevant, 5) == 0.5

    def test_empty_retrieved(self):
        """Test with empty retrieved list."""
        assert precision_at_k([], {"a"}, 5) == 0.0

    def test_k_zero(self):
        """Test with K=0."""
        assert precision_at_k(["a"], {"a"}, 0) == 0.0

class TestRecallAtK:
    def test_perfect_recall(self):
        """Test when all relevant items are retrieved."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b"}
        assert recall_at_k(retrieved, relevant, 3) == 1.0

    def test_partial_recall(self):
        """Test when only some relevant items are retrieved."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c", "d"}
        # 3 out of 4 relevant retrieved
        assert recall_at_k(retrieved, relevant, 3) == 0.75

    def test_zero_recall(self):
        """Test when no relevant items are retrieved."""
        retrieved = ["a", "b"]
        relevant = {"x", "y"}
        assert recall_at_k(retrieved, relevant, 2) == 0.0

    def test_empty_relevant(self):
        """Test with empty relevant set."""
        assert recall_at_k(["a", "b"], set(), 2) == 0.0

class TestDcgAtK:
    def test_perfect_dcg(self):
        """Test DCG with all relevant items at top."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        # DCG = 1/log2(2) + 1/log2(3) + 1/log2(4)
        expected = 1.0 + 1.0/math.log2(3) + 1.0/2.0
        assert math.isclose(dcg_at_k(retrieved, relevant, 3), expected, rel_tol=1e-9)

    def test_no_relevant(self):
        """Test DCG with no relevant items."""
        retrieved = ["a", "b", "c"]
        relevant = {"x", "y"}
        assert dcg_at_k(retrieved, relevant, 3) == 0.0

    def test_k_zero(self):
        """Test DCG with K=0."""
        assert dcg_at_k(["a"], {"a"}, 0) == 0.0

class TestIdealDcgAtK:
    def test_idcg_calculation(self):
        """Test IDCG calculation."""
        relevant = {"a", "b", "c"}
        # Perfect ranking: a, b, c
        # IDCG = 1/log2(2) + 1/log2(3) + 1/log2(4)
        expected = 1.0 + 1.0/math.log2(3) + 1.0/2.0
        assert math.isclose(ideal_dcg_at_k(relevant, 3), expected, rel_tol=1e-9)

    def test_idcg_zero_relevant(self):
        """Test IDCG with no relevant items."""
        assert ideal_dcg_at_k(set(), 5) == 0.0

    def test_idcg_k_larger_than_relevant(self):
        """Test IDCG when K exceeds number of relevant items."""
        relevant = {"a", "b"}
        # Should only count 2 items even though k=5
        expected = 1.0 + 1.0/math.log2(3)
        assert math.isclose(ideal_dcg_at_k(relevant, 5), expected, rel_tol=1e-9)

class TestNdcgAtK:
    def test_perfect_ndcg(self):
        """Test nDCG with perfect ranking (should be 1.0)."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        assert math.isclose(ndcg_at_k(retrieved, relevant, 3), 1.0, rel_tol=1e-9)

    def test_zero_ndcg(self):
        """Test nDCG with no relevant items retrieved."""
        retrieved = ["a", "b"]
        relevant = {"x", "y"}
        assert ndcg_at_k(retrieved, relevant, 2) == 0.0

    def test_partial_ndcg(self):
        """Test nDCG with partial ranking."""
        retrieved = ["x", "a", "y"]  # relevant item 'a' at rank 2
        relevant = {"a"}
        # DCG = 0 + 1/log2(3) + 0
        # IDCG = 1/log2(2) = 1.0
        dcg = 1.0 / math.log2(3)
        expected = dcg / 1.0
        assert math.isclose(ndcg_at_k(retrieved, relevant, 3), expected, rel_tol=1e-9)

    def test_zero_idcg_handling(self):
        """Test nDCG when IDCG is zero (no relevant items)."""
        retrieved = ["a", "b"]
        relevant = set()
        assert ndcg_at_k(retrieved, relevant, 2) == 0.0

class TestEvaluateMetrics:
    def test_full_evaluation(self):
        """Test complete metrics evaluation."""
        retrieved = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        relevant = ["a", "b", "c"]

        results = evaluate_metrics(retrieved, relevant, k_values=[1, 5, 10])

        assert "precision_at_k" in results
        assert "recall_at_k" in results
        assert "ndcg_at_k" in results

        # Check P@1: 1/1 = 1.0 (a is relevant)
        assert results["precision_at_k"][1] == 1.0

        # Check P@5: 3/5 = 0.6 (a, b, c are relevant)
        assert results["precision_at_k"][5] == 0.6

        # Check R@5: 3/3 = 1.0 (all relevant retrieved in top 5)
        assert results["recall_at_k"][5] == 1.0

    def test_default_k_values(self):
        """Test evaluation with default K values."""
        retrieved = ["a", "b"]
        relevant = ["a"]

        results = evaluate_metrics(retrieved, relevant)

        # Default k_values should be [1, 5, 10, 20]
        assert 1 in results["precision_at_k"]
        assert 5 in results["precision_at_k"]
        assert 10 in results["precision_at_k"]
        assert 20 in results["precision_at_k"]