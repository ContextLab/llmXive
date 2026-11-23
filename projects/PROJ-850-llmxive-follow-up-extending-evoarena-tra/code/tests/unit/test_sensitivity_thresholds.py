"""
Unit tests for sensitivity threshold analysis.
"""

import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.heuristics.sensitivity_thresholds import (
    calculate_metrics,
    run_sensitivity_analysis,
    write_results_to_csv
)
from src.heuristics.conflict_detector import ConflictDetector


class TestCalculateMetrics:
    """Tests for the calculate_metrics helper function."""

    def test_perfect_prediction(self):
        """Test with perfect predictions."""
        predictions = [True, True, False, False]
        ground_truth = [True, True, False, False]

        precision, recall, f1 = calculate_metrics(predictions, ground_truth)

        assert precision == 1.0
        assert recall == 1.0
        assert f1 == 1.0

    def test_no_true_positives(self):
        """Test when there are no true positives."""
        predictions = [False, False, False, False]
        ground_truth = [True, True, False, False]

        precision, recall, f1 = calculate_metrics(predictions, ground_truth)

        assert precision == 0.0
        assert recall == 0.0
        assert f1 == 0.0

    def test_all_predicted_positive(self):
        """Test when all predictions are positive."""
        predictions = [True, True, True, True]
        ground_truth = [True, True, False, False]

        precision, recall, f1 = calculate_metrics(predictions, ground_truth)

        assert precision == 0.5  # 2 TP / 4 predicted
        assert recall == 1.0     # 2 TP / 2 actual
        assert f1 == 2/3         # harmonic mean

    def test_empty_lists(self):
        """Test with empty input lists."""
        precision, recall, f1 = calculate_metrics([], [])

        assert precision == 0.0
        assert recall == 0.0
        assert f1 == 0.0

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        predictions = [True, False]
        ground_truth = [True]

        with pytest.raises(ValueError, match="same length"):
            calculate_metrics(predictions, ground_truth)


class TestRunSensitivityAnalysis:
    """Tests for the run_sensitivity_analysis function."""

    @pytest.fixture
    def mock_pairs(self):
        """Create mock synthetic pairs for testing."""
        return [
            {"patch_a": "fact: x=1", "patch_b": "fact: x=2", "is_contradiction": True},
            {"patch_a": "fact: x=1", "patch_b": "fact: y=2", "is_contradiction": False},
            {"patch_a": "state: ready", "patch_b": "state: error", "is_contradiction": True},
            {"patch_a": "state: ready", "patch_b": "state: complete", "is_contradiction": False},
        ]

    @pytest.fixture
    def mock_detector(self):
        """Create a mock detector that returns deterministic predictions."""
        class MockDetector:
            def __init__(self):
                self.threshold = 0.5

            def predict(self, patch_a, patch_b):
                from src.heuristics.conflict_detector import ModelResult
                # Simple mock: return True if patch_b contains '2' or 'error'
                is_conflict = '2' in patch_b or 'error' in patch_b
                return ModelResult(
                    is_conflict=is_conflict,
                    confidence=0.9 if is_conflict else 0.1
                )

        return MockDetector()

    def test_single_threshold(self, mock_detector, mock_pairs):
        """Test analysis with a single threshold."""
        thresholds = [0.5]
        results = run_sensitivity_analysis(mock_detector, mock_pairs, thresholds)

        assert len(results) == 1
        assert results[0]["threshold"] == 0.5
        assert "precision" in results[0]
        assert "recall" in results[0]
        assert "f1_score" in results[0]
        assert "model_name" in results[0]

    def test_multiple_thresholds(self, mock_detector, mock_pairs):
        """Test analysis with multiple thresholds."""
        thresholds = [0.3, 0.5, 0.7]
        results = run_sensitivity_analysis(mock_detector, mock_pairs, thresholds)

        assert len(results) == 3
        assert all(r["threshold"] in thresholds for r in results)

    def test_model_name_in_results(self, mock_detector, mock_pairs):
        """Test that model name is included in results."""
        thresholds = [0.5]
        results = run_sensitivity_analysis(
            mock_detector, mock_pairs, thresholds, model_name="test-model"
        )

        assert results[0]["model_name"] == "test-model"


class TestWriteResultsToCsv:
    """Tests for the write_results_to_csv function."""

    def test_writes_correct_columns(self, tmp_path):
        """Test that CSV has correct column headers."""
        results = [
            {"threshold": 0.5, "precision": 0.8, "recall": 0.9, "f1_score": 0.85, "model_name": "test"}
        ]
        output_path = tmp_path / "test_output.csv"

        write_results_to_csv(results, output_path)

        assert output_path.exists()

        with open(output_path, "r") as f:
            header = f.readline().strip()

        assert "threshold" in header
        assert "precision" in header
        assert "recall" in header
        assert "f1_score" in header
        assert "model_name" in header

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        results = [
            {"threshold": 0.5, "precision": 0.8, "recall": 0.9, "f1_score": 0.85, "model_name": "test"}
        ]
        nested_path = tmp_path / "nested" / "dir" / "output.csv"

        write_results_to_csv(results, nested_path)

        assert nested_path.exists()

    def test_writes_all_rows(self, tmp_path):
        """Test that all result rows are written."""
        results = [
            {"threshold": 0.5, "precision": 0.8, "recall": 0.9, "f1_score": 0.85, "model_name": "test1"},
            {"threshold": 0.7, "precision": 0.85, "recall": 0.88, "f1_score": 0.865, "model_name": "test1"},
        ]
        output_path = tmp_path / "test_output.csv"

        write_results_to_csv(results, output_path)

        with open(output_path, "r") as f:
            lines = f.readlines()

        # Header + 2 data rows
        assert len(lines) == 3