"""
Contract tests for recall metric calculation.

These tests verify that the exact-match recall metric is computed correctly
according to the specification (US1). They serve as a contract for the
evaluation module's behavior.

Note: These tests do NOT require training. They validate the metric logic
using mock inputs that simulate model outputs and ground truth.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure we can import from the code directory
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from evaluation.metrics import compute_exact_match_recall, evaluate_model_on_dataset


class TestExactMatchRecall:
    """Contract tests for the exact-match recall metric."""

    def test_perfect_recall(self):
        """Contract: If predictions exactly match targets, recall should be 1.0."""
        predictions = ["The cat sat on the mat", "The dog ran fast"]
        targets = ["The cat sat on the mat", "The dog ran fast"]
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 1.0, "Perfect matches should yield 1.0 recall"

    def test_zero_recall(self):
        """Contract: If no predictions match targets, recall should be 0.0."""
        predictions = ["completely wrong", "totally different"]
        targets = ["The cat sat on the mat", "The dog ran fast"]
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 0.0, "No matches should yield 0.0 recall"

    def test_partial_recall(self):
        """Contract: Recall should be the proportion of exact matches."""
        predictions = ["The cat sat on the mat", "wrong answer", "The dog ran fast"]
        targets = ["The cat sat on the mat", "correct answer", "The dog ran fast"]
        
        result = compute_exact_match_recall(predictions, targets)
        
        # 2 out of 3 matches
        assert result == pytest.approx(2/3, rel=1e-6), "Partial matches should yield correct proportion"

    def test_empty_predictions(self):
        """Contract: Empty predictions should result in 0.0 recall."""
        predictions = []
        targets = ["The cat sat on the mat"]
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 0.0, "Empty predictions should yield 0.0 recall"

    def test_empty_targets(self):
        """Contract: Empty targets should result in 0.0 recall (or handle gracefully)."""
        predictions = ["The cat sat on the mat"]
        targets = []
        
        result = compute_exact_match_recall(predictions, targets)
        
        # Should handle gracefully, typically 0.0 or raise a clear error
        # We expect 0.0 as there are no items to match
        assert result == 0.0, "Empty targets should yield 0.0 recall"

    def test_case_sensitivity(self):
        """Contract: Exact match is case-sensitive."""
        predictions = ["The cat sat on the mat"]
        targets = ["the cat sat on the mat"]  # different case
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 0.0, "Exact match should be case-sensitive"

    def test_whitespace_sensitivity(self):
        """Contract: Exact match is whitespace-sensitive."""
        predictions = ["The cat sat on the mat"]
        targets = ["The cat  sat on the mat"]  # extra space
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 0.0, "Exact match should be whitespace-sensitive"

    def test_single_item_match(self):
        """Contract: Single item matching should yield 1.0."""
        predictions = ["exact match"]
        targets = ["exact match"]
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 1.0, "Single matching item should yield 1.0"

    def test_single_item_mismatch(self):
        """Contract: Single item mismatch should yield 0.0."""
        predictions = ["wrong"]
        targets = ["correct"]
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 0.0, "Single mismatching item should yield 0.0"


class TestEvaluateModelOnDataset:
    """Contract tests for the model evaluation function."""

    def test_evaluate_returns_dict(self):
        """Contract: evaluate_model_on_dataset should return a dictionary."""
        # Mock model and dataset
        mock_model = None  # Will be handled by the function's internal logic
        mock_dataset = [
            {"input": "test input 1", "expected": "test output 1"},
            {"input": "test input 2", "expected": "test output 2"}
        ]
        
        result = evaluate_model_on_dataset(mock_model, mock_dataset, batch_size=1)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "predictions" in result, "Result should contain 'predictions'"
        assert "targets" in result, "Result should contain 'targets'"
        assert "recall" in result, "Result should contain 'recall'"

    def test_evaluate_preserves_order(self):
        """Contract: Predictions and targets should maintain input order."""
        mock_dataset = [
            {"input": "first", "expected": "first_out"},
            {"input": "second", "expected": "second_out"},
            {"input": "third", "expected": "third_out"}
        ]
        
        result = evaluate_model_on_dataset(None, mock_dataset, batch_size=1)
        
        # The function should preserve order even if predictions are mocked
        assert len(result["predictions"]) == 3, "Should have 3 predictions"
        assert len(result["targets"]) == 3, "Should have 3 targets"


class TestIntegrationWithRealData:
    """Integration tests that validate the metric against real dataset samples."""

    def test_metric_on_babi_sample(self):
        """Contract test using a sample from bAbI Task 3 (if available)."""
        # This test verifies the metric works with realistic data structures
        # We use a small, deterministic sample that mimics bAbI Task 3 format
        
        # Sample bAbI Task 3 data (story + question + answer)
        predictions = [
            "Mary",
            "John",
            "Daniel"
        ]
        targets = [
            "Mary",
            "John",
            "Daniel"
        ]
        
        result = compute_exact_match_recall(predictions, targets)
        
        assert result == 1.0, "Metric should work correctly with bAbI-style data"

    def test_metric_on_mixed_accuracy(self):
        """Contract test with mixed correct/incorrect predictions."""
        # Simulate a realistic scenario with ~75% accuracy
        predictions = [
            "Mary",
            "John",
            "Sarah",  # Wrong
            "Daniel"
        ]
        targets = [
            "Mary",
            "John",
            "Emma",   # Expected
            "Daniel"
        ]
        
        result = compute_exact_match_recall(predictions, targets)
        
        # 3 out of 4 correct
        expected = 0.75
        assert result == pytest.approx(expected, rel=1e-6), "Mixed accuracy should be computed correctly"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])