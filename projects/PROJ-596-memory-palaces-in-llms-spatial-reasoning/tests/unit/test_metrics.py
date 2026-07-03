"""
Contract test for recall metric calculation.

This module validates the exact-match recall metric computation logic
required for User Story 1 (US1). It ensures that the calculation correctly
compares model predictions against ground truth answers and returns a
valid recall score between 0.0 and 1.0.

The test uses deterministic, real-world style data samples to verify
the mathematical correctness of the metric without requiring model inference.
"""
import pytest
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


# We define the metric function here to ensure it is tested in isolation.
# In the full pipeline, this logic will reside in code/evaluation/metrics.py.
# This contract test verifies the spec requirement: "compute exact-match recall per seed".
def compute_exact_match_recall(predictions: List[str], ground_truth: List[str]) -> float:
    """
    Calculate the exact-match recall score.
    
    Args:
        predictions: List of predicted answer strings.
        ground_truth: List of ground truth answer strings.
        
    Returns:
        A float between 0.0 and 1.0 representing the proportion of
        exact matches.
        
    Raises:
        ValueError: If input lists are empty or of different lengths.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError(
            f"Prediction and ground truth lists must have the same length. "
            f"Got {len(predictions)} predictions and {len(ground_truth)} ground truths."
        )
    
    if len(predictions) == 0:
        raise ValueError("Input lists cannot be empty.")
    
    matches = sum(1 for pred, truth in zip(predictions, ground_truth) if pred.strip() == truth.strip())
    return matches / len(predictions)


class TestRecallMetricContract:
    """
    Contract tests for the recall metric calculation.
    
    These tests verify the logical correctness and edge case handling
    of the exact-match recall metric as required by the project specification.
    """
    
    def test_perfect_recall(self):
        """Test case where all predictions match ground truth."""
        predictions = [
            "The cat sat on the mat.",
            "London is the capital of the UK.",
            "The answer is 42."
        ]
        ground_truth = [
            "The cat sat on the mat.",
            "London is the capital of the UK.",
            "The answer is 42."
        ]
        
        result = compute_exact_match_recall(predictions, ground_truth)
        
        assert result == 1.0, f"Expected perfect recall (1.0), got {result}"
        
    def test_zero_recall(self):
        """Test case where no predictions match ground truth."""
        predictions = [
            "The dog barked.",
            "Paris is the capital.",
            "The answer is 100."
        ]
        ground_truth = [
            "The cat sat on the mat.",
            "London is the capital of the UK.",
            "The answer is 42."
        ]
        
        result = compute_exact_match_recall(predictions, ground_truth)
        
        assert result == 0.0, f"Expected zero recall (0.0), got {result}"
        
    def test_partial_recall(self):
        """Test case with partial matches."""
        predictions = [
            "The cat sat on the mat.",  # Match
            "Paris is the capital.",    # No match
            "The answer is 42."        # Match
        ]
        ground_truth = [
            "The cat sat on the mat.",
            "London is the capital of the UK.",
            "The answer is 42."
        ]
        
        result = compute_exact_match_recall(predictions, ground_truth)
        
        assert result == 0.6666666666666666, f"Expected recall of 2/3, got {result}"
        
    def test_case_sensitivity_handling(self):
        """Test that whitespace and minor case differences are handled as per spec (exact match)."""
        # Spec requires exact match. "Answer" != "answer" unless normalized.
        # We test the strict behavior.
        predictions = ["The Answer is 42."]
        ground_truth = ["The answer is 42."]
        
        result = compute_exact_match_recall(predictions, ground_truth)
        
        # Strict exact match should fail here
        assert result == 0.0, f"Expected 0.0 for case mismatch, got {result}"
        
    def test_whitespace_normalization(self):
        """Test that leading/trailing whitespace is ignored."""
        predictions = ["  The cat sat on the mat.  "]
        ground_truth = ["The cat sat on the mat."]
        
        result = compute_exact_match_recall(predictions, ground_truth)
        
        assert result == 1.0, f"Expected 1.0 after whitespace normalization, got {result}"
        
    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched list lengths raise a ValueError."""
        predictions = ["Match 1", "Match 2"]
        ground_truth = ["Match 1"]
        
        with pytest.raises(ValueError):
            compute_exact_match_recall(predictions, ground_truth)
            
    def test_empty_lists_raises_error(self):
        """Test that empty lists raise a ValueError."""
        predictions: List[str] = []
        ground_truth: List[str] = []
        
        with pytest.raises(ValueError):
            compute_exact_match_recall(predictions, ground_truth)
            
    def test_output_bounds(self):
        """Test that the output is always within [0.0, 1.0]."""
        # Generate a random-ish set of matches
        predictions = ["a", "b", "c", "d", "e"]
        ground_truth = ["a", "x", "c", "y", "e"]
        
        result = compute_exact_match_recall(predictions, ground_truth)
        
        assert 0.0 <= result <= 1.0, f"Recall score {result} is outside valid bounds [0.0, 1.0]"

    def test_artifact_output_format(self):
        """
        Verify that the metric function can produce results compatible
        with the required artifact format: artifacts/results/recall_accuracy.json
        """
        predictions = [
            "The story ends here.",
            "The hero wins.",
            "The villain loses."
        ]
        ground_truth = [
            "The story ends here.",
            "The hero loses.",
            "The villain wins."
        ]
        
        recall_score = compute_exact_match_recall(predictions, ground_truth)
        
        # Simulate the structure required for artifacts/results/recall_accuracy.json
        artifact_data = {
            "metric": "exact_match_recall",
            "seed": 42,
            "score": recall_score,
            "total_samples": len(predictions),
            "correct_samples": int(recall_score * len(predictions))
        }
        
        # Verify JSON serializability
        json_str = json.dumps(artifact_data)
        loaded = json.loads(json_str)
        
        assert loaded["score"] == recall_score
        assert loaded["metric"] == "exact_match_recall"
        assert isinstance(loaded["score"], float)