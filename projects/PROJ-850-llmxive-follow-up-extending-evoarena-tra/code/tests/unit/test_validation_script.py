"""
Unit tests for the validation script logic.
Tests metrics calculation and data loading without running the full model.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.validate_conflict_detector import (
    load_synthetic_pairs,
    calculate_metrics
)

class TestLoadSyntheticPairs:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON list."""
        data = [
            {"patch_a": "a", "patch_b": "b", "is_contradiction": True},
            {"patch_a": "c", "patch_b": "d", "is_contradiction": False}
        ]
        file_path = tmp_path / "pairs.json"
        file_path.write_text(json.dumps(data))

        result = load_synthetic_pairs(str(file_path))
        assert len(result) == 2
        assert result[0]["is_contradiction"] is True

    def test_load_nonexistent_file(self, tmp_path):
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_synthetic_pairs(str(tmp_path / "missing.json"))

    def test_load_invalid_format(self, tmp_path):
        """Test error on non-list JSON."""
        file_path = tmp_path / "bad.json"
        file_path.write_text(json.dumps({"key": "value"}))
        
        with pytest.raises(ValueError):
            load_synthetic_pairs(str(file_path))

class TestValidationMetrics:
    def test_perfect_prediction(self):
        """Test metrics when predictions match ground truth perfectly."""
        preds = [True, False, True, False]
        truth = [True, False, True, False]
        
        metrics = calculate_metrics(preds, truth)
        
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1_score"] == 1.0
        assert metrics["accuracy"] == 1.0
        assert metrics["true_positives"] == 2
        assert metrics["true_negatives"] == 2
        assert metrics["false_positives"] == 0
        assert metrics["false_negatives"] == 0

    def test_no_true_positives(self):
        """Test metrics when model predicts nothing is a conflict (but some are)."""
        preds = [False, False, False, False]
        truth = [True, False, True, False]
        
        metrics = calculate_metrics(preds, truth)
        
        assert metrics["precision"] == 0.0 # Division by zero handled -> 0
        assert metrics["recall"] == 0.0
        assert metrics["f1_score"] == 0.0
        assert metrics["true_positives"] == 0
        assert metrics["false_negatives"] == 2

    def test_all_false_positives(self):
        """Test metrics when model predicts everything is a conflict (but none are)."""
        preds = [True, True, True, True]
        truth = [False, False, False, False]
        
        metrics = calculate_metrics(preds, truth)
        
        assert metrics["precision"] == 0.0
        assert metrics["recall"] == 0.0 # TP is 0, FN is 0 -> 0/0 -> 0
        assert metrics["f1_score"] == 0.0
        assert metrics["true_negatives"] == 0
        assert metrics["false_positives"] == 4

    def test_mixed_results(self):
        """Test metrics with a mix of correct and incorrect predictions."""
        # TP=1, FP=1, TN=1, FN=1
        preds = [True, True, False, False]
        truth = [True, False, False, True]
        
        metrics = calculate_metrics(preds, truth)
        
        # Precision = 1 / (1+1) = 0.5
        # Recall = 1 / (1+1) = 0.5
        # F1 = 2 * 0.5 * 0.5 / 1.0 = 0.5
        assert abs(metrics["precision"] - 0.5) < 1e-6
        assert abs(metrics["recall"] - 0.5) < 1e-6
        assert abs(metrics["f1_score"] - 0.5) < 1e-6
        assert metrics["accuracy"] == 0.5

    def test_empty_lists(self):
        """Test handling of empty input."""
        metrics = calculate_metrics([], [])
        assert metrics["precision"] == 0.0
        assert metrics["recall"] == 0.0
        assert metrics["f1_score"] == 0.0
        assert metrics["accuracy"] == 0.0
        assert metrics["total_samples"] == 0

    def test_mismatched_lengths(self):
        """Test error when lengths differ."""
        with pytest.raises(ValueError):
            calculate_metrics([True, False], [True])