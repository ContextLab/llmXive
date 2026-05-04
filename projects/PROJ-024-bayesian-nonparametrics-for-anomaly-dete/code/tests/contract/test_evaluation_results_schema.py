"""Contract test for evaluation metrics and results schemas."""
import pytest
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any, List, Tuple

# Import from the correct path per API surface
from evaluation.metrics import EvaluationMetrics, compute_f1_score, compute_precision, compute_recall

class TestEvaluationMetricsSchema:
    """Verify EvaluationMetrics dataclass has required fields and types."""

    def test_evaluationmetrics_has_required_fields(self):
        """EvaluationMetrics must have precision, recall, f1_score, and auc fields."""
        metrics = EvaluationMetrics(
            precision=0.85,
            recall=0.90,
            f1_score=0.87,
            auc=0.92
        )
        assert hasattr(metrics, "precision")
        assert hasattr(metrics, "recall")
        assert hasattr(metrics, "f1_score")
        assert hasattr(metrics, "auc")

    def test_evaluationmetrics_values_are_floats(self):
        """EvaluationMetrics values must be floats."""
        metrics = EvaluationMetrics(
            precision=0.85,
            recall=0.90,
            f1_score=0.87,
            auc=0.92
        )
        assert isinstance(metrics.precision, float)
        assert isinstance(metrics.recall, float)
        assert isinstance(metrics.f1_score, float)
        assert isinstance(metrics.auc, float)

    def test_evaluationmetrics_values_in_range(self):
        """EvaluationMetrics values must be between 0 and 1."""
        metrics = EvaluationMetrics(
            precision=0.85,
            recall=0.90,
            f1_score=0.87,
            auc=0.92
        )
        assert 0 <= metrics.precision <= 1
        assert 0 <= metrics.recall <= 1
        assert 0 <= metrics.f1_score <= 1
        assert 0 <= metrics.auc <= 1

    def test_evaluationmetrics_can_serialize(self):
        """EvaluationMetrics instances should be serializable to dict."""
        metrics = EvaluationMetrics(
            precision=0.85,
            recall=0.90,
            f1_score=0.87,
            auc=0.92
        )
        from dataclasses import asdict
        serialized = asdict(metrics)
        assert "precision" in serialized
        assert "recall" in serialized
        assert "f1_score" in serialized
        assert "auc" in serialized

    def test_compute_f1_score_function_exists(self):
        """compute_f1_score function must exist and be callable."""
        assert callable(compute_f1_score)

    def test_compute_precision_function_exists(self):
        """compute_precision function must exist and be callable."""
        assert callable(compute_precision)

    def test_compute_recall_function_exists(self):
        """compute_recall function must exist and be callable."""
        assert callable(compute_recall)

    def test_compute_f1_score_returns_float(self):
        """compute_f1_score must return a float."""
        tp, fp, fn = 10, 5, 3
        f1 = compute_f1_score(tp, fp, fn)
        assert isinstance(f1, float)

    def test_compute_precision_returns_float(self):
        """compute_precision must return a float."""
        tp, fp = 10, 5
        precision = compute_precision(tp, fp)
        assert isinstance(precision, float)

    def test_compute_recall_returns_float(self):
        """compute_recall must return a float."""
        tp, fn = 10, 3
        recall = compute_recall(tp, fn)
        assert isinstance(recall, float)
