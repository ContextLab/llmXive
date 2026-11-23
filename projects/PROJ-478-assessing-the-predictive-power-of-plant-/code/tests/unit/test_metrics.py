"""
Unit tests for src/modeling/metrics.py
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from src.modeling.metrics import (
    calculate_auc,
    calculate_tss,
    find_optimal_threshold,
    evaluate_model,
    generate_metrics_report
)


class TestCalculateAUC:
    def test_perfect_classifier(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])
        auc = calculate_auc(y_true, y_scores)
        assert auc == 1.0

    def test_random_classifier(self):
        # A random classifier should have AUC around 0.5
        np.random.seed(42)
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_scores = np.random.rand(8)
        auc = calculate_auc(y_true, y_scores)
        assert 0.3 < auc < 0.7  # Allow some variance due to randomness

    def test_empty_input_raises_error(self):
        with pytest.raises(ValueError):
            calculate_auc(np.array([]), np.array([]))

    def test_single_class_raises_warning_returns_half(self):
        y_true = np.array([0, 0, 0])
        y_scores = np.array([0.1, 0.2, 0.3])
        auc = calculate_auc(y_true, y_scores)
        assert auc == 0.5


class TestCalculateTSS:
    def test_perfect_classifier(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1, 1])
        tss = calculate_tss(y_true, y_pred)
        assert tss == 1.0

    def test_worst_classifier(self):
        # Completely wrong predictions
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([1, 1, 1, 0, 0, 0])
        tss = calculate_tss(y_true, y_pred)
        assert tss == -1.0

    def test_random_classifier(self):
        np.random.seed(42)
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_pred = np.random.randint(0, 2, 8)
        tss = calculate_tss(y_true, y_pred)
        # TSS can range from -1 to 1, just check it's a valid float
        assert -1.0 <= tss <= 1.0

    def test_empty_input_raises_error(self):
        with pytest.raises(ValueError):
            calculate_tss(np.array([]), np.array([]))

    def test_imbalanced_classes(self):
        # Test with highly imbalanced data
        y_true = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        y_pred = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        tss = calculate_tss(y_true, y_pred)
        assert tss == 1.0


class TestFindOptimalThreshold:
    def test_perfect_separation(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        threshold = find_optimal_threshold(y_true, y_scores)
        # With perfect separation, threshold should be around 0.5
        assert 0.3 < threshold < 0.7

    def test_empty_input_raises_error(self):
        with pytest.raises(ValueError):
            find_optimal_threshold(np.array([]), np.array([]))

    def test_returns_valid_threshold(self):
        np.random.seed(42)
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_scores = np.random.rand(8)
        threshold = find_optimal_threshold(y_true, y_scores)
        assert 0.0 <= threshold <= 1.0


class TestEvaluateModel:
    def test_full_evaluation(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])

        results = evaluate_model(y_true, y_scores)

        assert "auc" in results
        assert "tss" in results
        assert "threshold" in results
        assert results["auc"] == 1.0
        assert results["tss"] == 1.0
        assert 0.3 < results["threshold"] < 0.7

    def test_custom_threshold(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])

        results = evaluate_model(y_true, y_scores, threshold=0.5)

        assert results["threshold"] == 0.5
        assert results["auc"] == 1.0
        assert results["tss"] == 1.0

    def test_empty_input_raises_error(self):
        with pytest.raises(ValueError):
            evaluate_model(np.array([]), np.array([]))


class TestGenerateMetricsReport:
    def test_report_generation(self):
        results = {
            "metrics": {"auc": 0.95, "tss": 0.85},
            "model_parameters": {"max_depth": 10, "n_estimators": 100},
            "cv_folds": 5,
            "timestamp": "2023-01-01T00:00:00",
            "total_records": 100,
            "presence_records": 50,
            "absence_records": 50,
            "feature_count": 19
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            generated_path = generate_metrics_report(results, output_path, species_name="Helianthus annuus")

            assert generated_path.exists()
            with open(generated_path, 'r') as f:
                report = json.load(f)

            assert report["species"] == "Helianthus annuus"
            assert report["metrics"]["auc"] == 0.95
            assert report["model_parameters"]["max_depth"] == 10

    def test_creates_parent_directories(self):
        results = {
            "metrics": {"auc": 0.9},
            "model_parameters": {},
            "cv_folds": 5,
            "timestamp": "2023-01-01",
            "total_records": 10,
            "presence_records": 5,
            "absence_records": 5,
            "feature_count": 10
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "report.json"
            generated_path = generate_metrics_report(results, output_path)

            assert generated_path.exists()