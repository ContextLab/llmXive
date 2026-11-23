"""
Unit tests for evaluation metrics functions in code/evaluation/metrics.py.
Extends existing tests with coverage for error detection calibration,
sensitivity analysis integration, and edge cases.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score, brier_score_loss

from code.evaluation.metrics import (
    calculate_self_consistency,
    calculate_roc_auc,
    calculate_brier_score,
    calculate_ece,
    calculate_calibration_curve,
    calculate_entropy,
    aggregate_metrics,
    calculate_error_detection_calibration,
    save_calibration_results,
)
from code.evaluation.results import EvaluationResult


class TestCalculateSelfConsistency:
    """Tests for self-consistency calculation."""

    def test_basic_self_consistency(self):
        """Test basic self-consistency calculation with majority vote."""
        # Simulate multiple generations for each item
        generations = [
            ["answer_a", "answer_a", "answer_a"],  # 3/3 agree
            ["answer_b", "answer_c", "answer_b"],  # 2/3 agree
            ["answer_d", "answer_e", "answer_f"],  # 1/3 agree (tie)
            ["answer_g", "answer_g", "answer_h"],  # 2/3 agree
        ]

        consistency = calculate_self_consistency(generations)

        # First: 100%, Second: 100% (majority), Third: 0% (no majority), Fourth: 100%
        # Average: (1 + 1 + 0 + 1) / 4 = 0.75
        expected = 0.75
        assert np.isclose(consistency, expected, atol=1e-4)

    def test_single_generation(self):
        """Test with single generation per item (always consistent)."""
        generations = [
            ["answer_a"],
            ["answer_b"],
            ["answer_c"],
        ]

        consistency = calculate_self_consistency(generations)
        assert np.isclose(consistency, 1.0, atol=1e-4)

    def test_empty_generations(self):
        """Test with empty generations list."""
        generations = []

        consistency = calculate_self_consistency(generations)
        assert np.isclose(consistency, 0.0, atol=1e-4)

    def test_all_empty_lists(self):
        """Test with all empty generation lists."""
        generations = [[], [], []]

        consistency = calculate_self_consistency(generations)
        assert np.isclose(consistency, 0.0, atol=1e-4)

    def test_tie_breaking(self):
        """Test tie-breaking behavior in majority vote."""
        # Two answers with equal count
        generations = [
            ["answer_a", "answer_b"],  # Tie: 1/2 each
            ["answer_c", "answer_c"],  # Clear majority
        ]

        consistency = calculate_self_consistency(generations)

        # First: 0% (no majority), Second: 100%
        # Average: 0.5
        assert np.isclose(consistency, 0.5, atol=1e-4)


class TestCalculateRocAuc:
    """Tests for ROC-AUC calculation."""

    def test_basic_roc_auc(self):
        """Test basic ROC-AUC calculation."""
        y_true = np.array([0, 0, 1, 1, 1, 0])
        y_scores = np.array([0.1, 0.2, 0.8, 0.9, 0.95, 0.3])

        auc = calculate_roc_auc(y_true, y_scores)

        assert 0 <= auc <= 1
        # Perfect separation would give 1.0
        assert auc > 0.5  # Better than random

    def test_perfect_separation(self):
        """Test with perfect separation."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 1.0])

        auc = calculate_roc_auc(y_true, y_scores)
        assert np.isclose(auc, 1.0, atol=1e-4)

    def test_random_separation(self):
        """Test with random scores (should be around 0.5)."""
        np.random.seed(42)
        y_true = np.array([0, 0, 0, 1, 1, 1, 1, 0])
        y_scores = np.random.rand(len(y_true))

        auc = calculate_roc_auc(y_true, y_scores)
        # With random scores, AUC should be around 0.5
        assert 0.3 < auc < 0.7

    def test_single_class(self):
        """Test with only one class present."""
        y_true = np.array([0, 0, 0, 0])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4])

        # ROC-AUC is undefined for single class, should return 0.5 or raise
        # Our implementation should handle this gracefully
        auc = calculate_roc_auc(y_true, y_scores)
        # Typically returns 0.5 or NaN; we expect a numeric value
        assert isinstance(auc, float)


class TestCalculateBrierScore:
    """Tests for Brier score calculation."""

    def test_basic_brier_score(self):
        """Test basic Brier score calculation."""
        y_true = np.array([0, 0, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.8, 0.9])

        brier = calculate_brier_score(y_true, y_scores)

        # Manual calculation:
        # (0.1-0)^2 + (0.2-0)^2 + (0.8-1)^2 + (0.9-1)^2
        # = 0.01 + 0.04 + 0.04 + 0.01 = 0.10
        # Mean = 0.10 / 4 = 0.025
        expected = 0.025
        assert np.isclose(brier, expected, atol=1e-4)

    def test_perfect_predictions(self):
        """Test with perfect predictions."""
        y_true = np.array([0, 0, 1, 1])
        y_scores = np.array([0.0, 0.0, 1.0, 1.0])

        brier = calculate_brier_score(y_true, y_scores)
        assert np.isclose(brier, 0.0, atol=1e-4)

    def test_worst_predictions(self):
        """Test with worst predictions (opposite of truth)."""
        y_true = np.array([0, 0, 1, 1])
        y_scores = np.array([1.0, 1.0, 0.0, 0.0])

        brier = calculate_brier_score(y_true, y_scores)
        # Each squared error is 1.0, mean = 1.0
        assert np.isclose(brier, 1.0, atol=1e-4)

    def test_random_predictions(self):
        """Test with random predictions."""
        np.random.seed(42)
        y_true = np.array([0, 1, 0, 1, 1, 0])
        y_scores = np.random.rand(len(y_true))

        brier = calculate_brier_score(y_true, y_scores)
        # Should be between 0 and 1
        assert 0 <= brier <= 1


class TestCalculateECE:
    """Tests for Expected Calibration Error (ECE) calculation."""

    def test_basic_ece(self):
        """Test basic ECE calculation."""
        y_true = np.array([1, 1, 0, 0, 1, 1, 0, 0])
        y_scores = np.array([0.9, 0.9, 0.1, 0.1, 0.8, 0.8, 0.2, 0.2])

        ece = calculate_ece(y_true, y_scores, n_bins=2)

        # With 2 bins: [0-0.5, 0.5-1.0]
        # Bin 1: scores [0.1, 0.1, 0.2, 0.2], avg score = 0.15, accuracy = 0/4 = 0.0
        # Bin 2: scores [0.9, 0.9, 0.8, 0.8], avg score = 0.85, accuracy = 4/4 = 1.0
        # ECE = (4/8)*|0.15-0| + (4/8)*|0.85-1| = 0.5*0.15 + 0.5*0.15 = 0.15
        assert ece >= 0
        assert ece <= 1

    def test_perfectly_calibrated(self):
        """Test with perfectly calibrated predictions."""
        # If confidence matches accuracy exactly
        y_true = np.array([1, 1, 1, 0, 0, 0])
        y_scores = np.array([0.6, 0.6, 0.6, 0.4, 0.4, 0.4])

        # This is a simplified case; ECE should be low
        ece = calculate_ece(y_true, y_scores, n_bins=2)
        assert ece >= 0
        assert ece <= 1

    def test_single_bin(self):
        """Test with single bin."""
        y_true = np.array([1, 0, 1, 0])
        y_scores = np.array([0.7, 0.3, 0.8, 0.2])

        ece = calculate_ece(y_true, y_scores, n_bins=1)
        # Single bin: overall accuracy vs average confidence
        assert ece >= 0
        assert ece <= 1

    def test_empty_inputs(self):
        """Test with empty inputs."""
        y_true = np.array([])
        y_scores = np.array([])

        ece = calculate_ece(y_true, y_scores, n_bins=10)
        assert np.isclose(ece, 0.0, atol=1e-4)


class TestCalculateCalibrationCurve:
    """Tests for calibration curve calculation."""

    def test_basic_calibration_curve(self):
        """Test basic calibration curve calculation."""
        y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
        y_scores = np.array([0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1, 0.5, 0.55])

        result = calculate_calibration_curve(y_true, y_scores, n_bins=5)

        assert "bin_edges" in result
        assert "bin_counts" in result
        assert "observed_accuracies" in result
        assert len(result["bin_edges"]) == len(result["bin_counts"]) + 1
        assert len(result["bin_edges"]) == len(result["observed_accuracies"]) + 1

        # Check counts sum to total
        assert sum(result["bin_counts"]) == len(y_true)

    def test_calibration_curve_bins(self):
        """Test that calibration curve has correct number of bins."""
        y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        y_scores = np.array([0.8, 0.2, 0.7, 0.3, 0.9, 0.1, 0.6, 0.4])

        for n_bins in [2, 5, 10]:
            result = calculate_calibration_curve(y_true, y_scores, n_bins=n_bins)
            assert len(result["bin_edges"]) == n_bins + 1
            assert len(result["bin_counts"]) == n_bins
            assert len(result["observed_accuracies"]) == n_bins

    def test_calibration_curve_empty(self):
        """Test with empty inputs."""
        y_true = np.array([])
        y_scores = np.array([])

        result = calculate_calibration_curve(y_true, y_scores, n_bins=5)
        assert result["bin_counts"] == []
        assert result["observed_accuracies"] == []


class TestCalculateEntropy:
    """Tests for entropy calculation."""

    def test_basic_entropy(self):
        """Test basic entropy calculation."""
        probs = np.array([0.5, 0.5])
        entropy = calculate_entropy(probs)

        # Binary entropy at p=0.5 is 1.0 (in bits) or log(2) (in nats)
        # Our implementation uses natural log
        assert entropy > 0

    def test_zero_entropy(self):
        """Test with deterministic distribution (zero entropy)."""
        probs = np.array([1.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert np.isclose(entropy, 0.0, atol=1e-4)

    def test_max_entropy(self):
        """Test with uniform distribution (maximum entropy)."""
        probs = np.array([1/3, 1/3, 1/3])
        entropy = calculate_entropy(probs)

        # Max entropy for 3 classes is log(3)
        expected = np.log(3)
        assert np.isclose(entropy, expected, rtol=1e-4)

    def test_invalid_probs(self):
        """Test with invalid probability distribution."""
        probs = np.array([0.5, 0.6])  # Sum > 1

        with pytest.raises(ValueError):
            calculate_entropy(probs)


class TestAggregateMetrics:
    """Tests for metrics aggregation."""

    def test_basic_aggregation(self):
        """Test basic metrics aggregation."""
        metrics_list = [
            {"self_consistency": 0.8, "brier_score": 0.1},
            {"self_consistency": 0.9, "brier_score": 0.05},
            {"self_consistency": 0.85, "brier_score": 0.08},
        ]

        aggregated = aggregate_metrics(metrics_list)

        assert "self_consistency" in aggregated
        assert "brier_score" in aggregated
        assert np.isclose(aggregated["self_consistency"], 0.85, atol=1e-4)
        assert np.isclose(aggregated["brier_score"], 0.0766, atol=1e-4)

    def test_aggregation_with_missing_keys(self):
        """Test aggregation when some metrics are missing."""
        metrics_list = [
            {"self_consistency": 0.8},
            {"self_consistency": 0.9, "brier_score": 0.05},
            {"brier_score": 0.08},
        ]

        aggregated = aggregate_metrics(metrics_list)

        assert "self_consistency" in aggregated
        assert "brier_score" in aggregated
        # self_consistency: (0.8 + 0.9) / 2 = 0.85
        assert np.isclose(aggregated["self_consistency"], 0.85, atol=1e-4)

    def test_aggregation_empty_list(self):
        """Test aggregation with empty list."""
        metrics_list = []

        aggregated = aggregate_metrics(metrics_list)
        assert aggregated == {}

    def test_aggregation_with_std(self):
        """Test aggregation returns standard deviation."""
        metrics_list = [
            {"self_consistency": 0.8, "brier_score": 0.1},
            {"self_consistency": 0.9, "brier_score": 0.05},
            {"self_consistency": 0.7, "brier_score": 0.15},
        ]

        aggregated = aggregate_metrics(metrics_list)

        # Check that std is present and non-zero
        assert "self_consistency_std" in aggregated
        assert aggregated["self_consistency_std"] > 0


class TestCalculateErrorDetectionCalibration:
    """Tests for error detection calibration calculation."""

    def test_basic_error_detection_calibration(self):
        """Test basic error detection calibration."""
        # Simulate model outputs with confidence scores and correctness
        confidence_scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2])
        is_correct = np.array([1, 1, 1, 1, 0, 0, 0, 0])  # High confidence = correct

        result = calculate_error_detection_calibration(
            confidence_scores,
            is_correct,
            n_bins=4
        )

        assert "bin_edges" in result
        assert "bin_counts" in result
        assert "predicted_error_rates" in result
        assert "observed_error_rates" in result

        # Check that observed error rates decrease with confidence
        # (higher confidence -> lower error rate)
        # This is a simplified check
        assert len(result["bin_edges"]) == 5
        assert len(result["bin_counts"]) == 4
        assert len(result["observed_error_rates"]) == 4

    def test_error_detection_calibration_all_correct(self):
        """Test when all predictions are correct."""
        confidence_scores = np.array([0.9, 0.8, 0.7, 0.6])
        is_correct = np.array([1, 1, 1, 1])

        result = calculate_error_detection_calibration(
            confidence_scores,
            is_correct,
            n_bins=2
        )

        # All observed error rates should be 0
        assert all(rate == 0.0 for rate in result["observed_error_rates"])

    def test_error_detection_calibration_all_wrong(self):
        """Test when all predictions are wrong."""
        confidence_scores = np.array([0.9, 0.8, 0.7, 0.6])
        is_correct = np.array([0, 0, 0, 0])

        result = calculate_error_detection_calibration(
            confidence_scores,
            is_correct,
            n_bins=2
        )

        # All observed error rates should be 1
        assert all(rate == 1.0 for rate in result["observed_error_rates"])

    def test_error_detection_calibration_empty(self):
        """Test with empty inputs."""
        confidence_scores = np.array([])
        is_correct = np.array([])

        result = calculate_error_detection_calibration(
            confidence_scores,
            is_correct,
            n_bins=5
        )

        assert result["bin_counts"] == []
        assert result["observed_error_rates"] == []

    def test_error_detection_calibration_single_bin(self):
        """Test with single bin."""
        confidence_scores = np.array([0.9, 0.8, 0.7, 0.6])
        is_correct = np.array([1, 1, 0, 0])

        result = calculate_error_detection_calibration(
            confidence_scores,
            is_correct,
            n_bins=1
        )

        assert len(result["bin_edges"]) == 2
        assert len(result["bin_counts"]) == 1
        assert len(result["observed_error_rates"]) == 1
        # Overall error rate = 2/4 = 0.5
        assert np.isclose(result["observed_error_rates"][0], 0.5, atol=1e-4)


class TestSaveCalibrationResults:
    """Tests for saving calibration results to JSON."""

    def test_save_calibration_results(self):
        """Test saving calibration results to a JSON file."""
        result = {
            "bin_edges": [0.0, 0.25, 0.5, 0.75, 1.0],
            "bin_counts": [10, 20, 30, 40],
            "predicted_error_rates": [0.1, 0.2, 0.3, 0.4],
            "observed_error_rates": [0.15, 0.25, 0.35, 0.45]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            save_calibration_results(result, f.name)

            # Load and verify
            with open(f.name, 'r') as loaded:
                data = json.load(loaded)

            assert data["bin_edges"] == result["bin_edges"]
            assert data["bin_counts"] == result["bin_counts"]
            assert data["predicted_error_rates"] == result["predicted_error_rates"]
            assert data["observed_error_rates"] == result["observed_error_rates"]

        os.unlink(f.name)

    def test_save_calibration_results_invalid_path(self):
        """Test saving to an invalid path raises an error."""
        result = {
            "bin_edges": [0.0, 1.0],
            "bin_counts": [10],
            "predicted_error_rates": [0.5],
            "observed_error_rates": [0.6]
        }

        with pytest.raises(OSError):
            save_calibration_results(result, "/nonexistent/directory/result.json")


class TestEvaluationResultDataclass:
    """Tests for the EvaluationResult dataclass."""

    def test_creation(self):
        """Test basic creation of EvaluationResult."""
        result = EvaluationResult(
            model_id="test-model",
            dataset="gsm8k",
            metrics={"accuracy": 0.85, "loss": 0.45},
            raw_predictions=["pred1", "pred2"],
            ground_truth=["ans1", "ans2"],
            metadata={"seed": 42}
        )
        assert result.model_id == "test-model"
        assert result.dataset == "gsm8k"
        assert result.metrics["accuracy"] == 0.85
        assert result.metadata["seed"] == 42

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = EvaluationResult(
            model_id="test",
            dataset="test",
            metrics={"acc": 0.8},
            raw_predictions=[],
            ground_truth=[],
            metadata={}
        )
        d = result.to_dict()
        assert d["model_id"] == "test"
        assert d["metrics"]["acc"] == 0.8

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "model_id": "test",
            "dataset": "test",
            "metrics": {"acc": 0.8},
            "raw_predictions": [],
            "ground_truth": [],
            "metadata": {}
        }
        result = EvaluationResult.from_dict(d)
        assert result.model_id == "test"
        assert result.metrics["acc"] == 0.8

    def test_save_and_load(self):
        """Test saving and loading EvaluationResult."""
        result = EvaluationResult(
            model_id="test-model",
            dataset="gsm8k",
            metrics={"accuracy": 0.85},
            raw_predictions=["pred1"],
            ground_truth=["ans1"],
            metadata={"seed": 42}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            result.save(f.name)

            loaded = EvaluationResult.load(f.name)
            assert loaded.model_id == result.model_id
            assert loaded.metrics["accuracy"] == result.metrics["accuracy"]

        os.unlink(f.name)


class TestEdgeCasesAndRobustness:
    """Tests for edge cases and robustness of metrics functions."""

    def test_very_large_scores(self):
        """Test with very large score values (should be normalized)."""
        y_true = np.array([0, 1])
        y_scores = np.array([1e10, 2e10])  # Very large values

        # Brier score should still work
        brier = calculate_brier_score(y_true, y_scores)
        assert isinstance(brier, float)

    def test_nan_values(self):
        """Test handling of NaN values."""
        y_true = np.array([0, 1, np.nan, 1])
        y_scores = np.array([0.1, 0.9, 0.5, 0.8])

        # Should raise or handle gracefully
        with pytest.raises((ValueError, TypeError)):
            calculate_brier_score(y_true, y_scores)

    def test_inf_values(self):
        """Test handling of infinite values."""
        y_true = np.array([0, 1])
        y_scores = np.array([0.1, np.inf])

        # Should raise or handle gracefully
        with pytest.raises((ValueError, TypeError)):
            calculate_brier_score(y_true, y_scores)

    def test_mixed_precision(self):
        """Test with mixed precision inputs."""
        y_true = np.array([0, 1, 0, 1], dtype=np.float32)
        y_scores = np.array([0.1, 0.9, 0.2, 0.8], dtype=np.float64)

        brier = calculate_brier_score(y_true, y_scores)
        assert isinstance(brier, float)

    def test_very_small_sample(self):
        """Test with very small sample size."""
        y_true = np.array([0, 1])
        y_scores = np.array([0.1, 0.9])

        auc = calculate_roc_auc(y_true, y_scores)
        assert 0 <= auc <= 1

    def test_extreme_calibration(self):
        """Test with extreme calibration scenarios."""
        # All predictions at 0.5 (maximum uncertainty)
        y_true = np.array([0, 1, 0, 1, 0, 1])
        y_scores = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        ece = calculate_ece(y_true, y_scores, n_bins=5)
        # ECE should be high because predictions are uninformative
        assert ece >= 0
        assert ece <= 1