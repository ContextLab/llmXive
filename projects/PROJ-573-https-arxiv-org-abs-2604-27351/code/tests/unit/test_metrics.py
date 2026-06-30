"""
Unit tests for src/evaluation/metrics.py
"""
import pytest
import numpy as np
from src.evaluation.metrics import compute_f1, compute_mape


class TestComputeF1:
    def test_binary_f1_perfect(self):
        y_true = [1, 0, 1, 1, 0, 1]
        y_pred = [1, 0, 1, 1, 0, 1]
        score = compute_f1(y_true, y_pred)
        assert score == 1.0

    def test_binary_f1_imperfect(self):
        # TP=2, FP=1, FN=1 -> Precision=2/3, Recall=2/3 -> F1=2/3
        y_true = [1, 0, 1, 1, 0, 1]
        y_pred = [1, 1, 1, 1, 0, 0]
        score = compute_f1(y_true, y_pred)
        expected = 2 * (2/3 * 2/3) / (2/3 + 2/3)
        assert pytest.approx(score, abs=1e-5) == expected

    def test_f1_empty_arrays(self):
        y_true = []
        y_pred = []
        score = compute_f1(y_true, y_pred)
        assert score == 0.0

    def test_f1_mismatched_shapes(self):
        y_true = [1, 0, 1]
        y_pred = [1, 0]
        with pytest.raises(ValueError):
            compute_f1(y_true, y_pred)

    def test_f1_no_positive_predictions(self):
        y_true = [1, 1, 1]
        y_pred = [0, 0, 0]
        # Precision = 0, Recall = 0 -> F1 = 0
        score = compute_f1(y_true, y_pred)
        assert score == 0.0

    def test_f1_no_positive_actual(self):
        y_true = [0, 0, 0]
        y_pred = [1, 1, 1]
        # Recall = 0 (TP=0, FN=0) -> F1 = 0
        score = compute_f1(y_true, y_pred)
        assert score == 0.0


class TestComputeMape:
    def test_mape_perfect(self):
        y_true = [10.0, 20.0, 30.0]
        y_pred = [10.0, 20.0, 30.0]
        score = compute_mape(y_true, y_pred)
        assert score == 0.0

    def test_mape_constant_error(self):
        # Errors: |10-12|=2 (20%), |20-22|=2 (10%), |30-32|=2 (6.66%)
        # Mean = (0.2 + 0.1 + 0.0666...) / 3
        y_true = [10.0, 20.0, 30.0]
        y_pred = [12.0, 22.0, 32.0]
        score = compute_mape(y_true, y_pred)
        expected = (0.2 + 0.1 + (2/30)) / 3
        assert pytest.approx(score, abs=1e-5) == expected

    def test_mape_with_zeros_in_true(self):
        # Should ignore the zero entry
        y_true = [0.0, 10.0, 20.0]
        y_pred = [5.0, 12.0, 22.0]
        # Only indices 1 and 2 count: |10-12|/10 = 0.2, |20-22|/20 = 0.1
        # Mean = 0.15
        score = compute_mape(y_true, y_pred)
        expected = 0.15
        assert pytest.approx(score, abs=1e-5) == expected

    def test_mape_all_zeros_in_true(self):
        y_true = [0.0, 0.0, 0.0]
        y_pred = [1.0, 2.0, 3.0]
        score = compute_mape(y_true, y_pred)
        assert score == 0.0

    def test_mape_empty_arrays(self):
        y_true = []
        y_pred = []
        score = compute_mape(y_true, y_pred)
        assert score == 0.0

    def test_mape_mismatched_shapes(self):
        y_true = [1.0, 2.0]
        y_pred = [1.0]
        with pytest.raises(ValueError):
            compute_mape(y_true, y_pred)