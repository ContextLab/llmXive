"""
Unit tests for metrics.py
"""
import pytest
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
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc2", "doc3", "doc4"}
        assert precision_at_k(retrieved, relevant, 3) == 1.0

    def test_partial_precision(self):
        retrieved = ["doc1", "doc5", "doc3"]
        relevant = {"doc1", "doc2", "doc3"}
        # 2 out of 3 are relevant
        assert precision_at_k(retrieved, relevant, 3) == 2.0 / 3.0

    def test_zero_precision(self):
        retrieved = ["doc5", "doc6"]
        relevant = {"doc1", "doc2"}
        assert precision_at_k(retrieved, relevant, 2) == 0.0

    def test_k_larger_than_retrieved(self):
        retrieved = ["doc1"]
        relevant = {"doc1", "doc2"}
        # Only 1 retrieved, so precision is 1/5 = 0.2
        assert precision_at_k(retrieved, relevant, 5) == 1.0 / 5.0

    def test_k_zero(self):
        retrieved = ["doc1"]
        relevant = {"doc1"}
        assert precision_at_k(retrieved, relevant, 0) == 0.0

class TestRecallAtK:
    def test_perfect_recall(self):
        retrieved = ["doc1", "doc2"]
        relevant = {"doc1", "doc2"}
        assert recall_at_k(retrieved, relevant, 2) == 1.0

    def test_partial_recall(self):
        retrieved = ["doc1"]
        relevant = {"doc1", "doc2"}
        assert recall_at_k(retrieved, relevant, 1) == 0.5

    def test_zero_recall(self):
        retrieved = ["doc3"]
        relevant = {"doc1", "doc2"}
        assert recall_at_k(retrieved, relevant, 1) == 0.0

    def test_empty_relevant(self):
        retrieved = ["doc1"]
        relevant = set()
        assert recall_at_k(retrieved, relevant, 1) == 0.0

    def test_k_larger_than_retrieved(self):
        retrieved = ["doc1"]
        relevant = {"doc1", "doc2"}
        # Retrieved 1 relevant out of 2 total relevant
        assert recall_at_k(retrieved, relevant, 5) == 0.5

class TestDcgAtK:
    def test_perfect_dcg(self):
        retrieved = ["doc1", "doc2"]
        relevant = {"doc1", "doc2"}
        # 1/log2(2) + 1/log2(3)
        expected = 1.0 / math.log2(2) + 1.0 / math.log2(3)
        assert abs(dcg_at_k(retrieved, relevant, 2) - expected) < 1e-6

    def test_zero_dcg(self):
        retrieved = ["doc3"]
        relevant = {"doc1", "doc2"}
        assert dcg_at_k(retrieved, relevant, 1) == 0.0

    def test_partial_dcg(self):
        retrieved = ["doc1", "doc3"]
        relevant = {"doc1", "doc2"}
        # Only first is relevant: 1/log2(2)
        expected = 1.0 / math.log2(2)
        assert abs(dcg_at_k(retrieved, relevant, 2) - expected) < 1e-6

class TestIdealDcgAtK:
    def test_idcg_calculation(self):
        relevant = {"doc1", "doc2"}
        # Ideal: both relevant at top. 1/log2(2) + 1/log2(3)
        expected = 1.0 / math.log2(2) + 1.0 / math.log2(3)
        assert abs(ideal_dcg_at_k(relevant, 2) - expected) < 1e-6

    def test_idcg_empty_relevant(self):
        relevant = set()
        assert ideal_dcg_at_k(relevant, 5) == 0.0

    def test_idcg_k_larger_than_relevant(self):
        relevant = {"doc1"}
        # Only 1 relevant, so only first position contributes
        expected = 1.0 / math.log2(2)
        assert abs(ideal_dcg_at_k(relevant, 5) - expected) < 1e-6

class TestNdcgAtK:
    def test_perfect_ndcg(self):
        retrieved = ["doc1", "doc2"]
        relevant = {"doc1", "doc2"}
        assert abs(ndcg_at_k(retrieved, relevant, 2) - 1.0) < 1e-6

    def test_zero_ndcg(self):
        retrieved = ["doc3"]
        relevant = {"doc1", "doc2"}
        assert ndcg_at_k(retrieved, relevant, 1) == 0.0

    def test_partial_ndcg(self):
        retrieved = ["doc3", "doc1"]  # Relevant at pos 2
        relevant = {"doc1"}
        # DCG = 0 + 1/log2(3)
        # IDCG = 1/log2(2)
        # nDCG = (1/log2(3)) / (1/log2(2))
        dcg = 1.0 / math.log2(3)
        idcg = 1.0 / math.log2(2)
        expected = dcg / idcg
        assert abs(ndcg_at_k(retrieved, relevant, 2) - expected) < 1e-6

    def test_empty_relevant_ndcg(self):
        retrieved = ["doc1"]
        relevant = set()
        assert ndcg_at_k(retrieved, relevant, 1) == 0.0

class TestEvaluateMetrics:
    def test_full_evaluation(self):
        retrieved = ["doc1", "doc5", "doc2"]
        relevant = ["doc1", "doc2", "doc3"]
        results = evaluate_metrics(retrieved, relevant, k_values=[2])
        
        assert "precision@2" in results
        assert "recall@2" in results
        assert "ndcg@2" in results
        
        # precision@2: 2 relevant in top 2 -> 2/2 = 1.0
        assert results["precision@2"] == 1.0
        
        # recall@2: 2 relevant retrieved out of 3 total -> 2/3
        assert abs(results["recall@2"] - 2.0/3.0) < 1e-6

    def test_default_k_values(self):
        retrieved = ["doc1"]
        relevant = ["doc1"]
        results = evaluate_metrics(retrieved, relevant)
        
        assert "precision@5" in results
        assert "recall@5" in results
        assert "ndcg@5" in results
        assert "precision@10" in results
        assert "precision@20" in results

    def test_empty_relevant_list(self):
        retrieved = ["doc1"]
        relevant = []
        results = evaluate_metrics(retrieved, relevant, k_values=[1])
        
        assert results["precision@1"] == 0.0
        assert results["recall@1"] == 0.0
        assert results["ndcg@1"] == 0.0

    def test_empty_retrieved_list(self):
        retrieved = []
        relevant = ["doc1"]
        results = evaluate_metrics(retrieved, relevant, k_values=[1])
        
        assert results["precision@1"] == 0.0
        assert results["recall@1"] == 0.0
        assert results["ndcg@1"] == 0.0

import math
import math