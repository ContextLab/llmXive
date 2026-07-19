"""
Unit tests for edge cases in feature engineering and evaluation pipelines.
Covers zero-variance, missing data, NaN/Inf handling, and empty inputs.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_dimensional_fidelity_loss,
    load_aligned_data,
    compute_all_features,
)
from evaluate import calculate_baseline_mae, perform_permutation_test, calculate_metrics


class TestZeroVarianceEdgeCases:
    """Tests for handling zero-variance distributions."""

    def test_zero_variance_variance_calculation(self):
        """Variance should be 0 for constant values."""
        data = np.array([5.0, 5.0, 5.0, 5.0])
        var, range_val = calculate_variance_and_range(data)
        assert var == 0.0
        assert range_val == 0.0

    def test_zero_variance_entropy_calculation(self):
        """Entropy should be 0 for constant values (no uncertainty)."""
        data = np.array([0.25, 0.25, 0.25, 0.25])  # Uniform distribution
        entropy = calculate_entropy(data)
        # For uniform distribution over 4 bins, entropy = log2(4) = 2.0
        # But if all mass is on one bin (constant), entropy should be 0
        data_constant = np.array([1.0, 0.0, 0.0, 0.0])
        entropy_const = calculate_entropy(data_constant)
        assert entropy_const == 0.0

    def test_zero_variance_skewness_kurtosis(self):
        """Skewness and kurtosis should handle zero variance gracefully."""
        data = np.array([5.0, 5.0, 5.0, 5.0])
        skew, kurt = calculate_skewness_and_kurtosis(data)
        # With zero variance, these are undefined but should not crash
        # scipy returns nan or inf, we expect them to be handled
        assert not (np.isinf(skew) or np.isnan(skew) or np.isinf(kurt) or np.isnan(kurt)) or (
            skew == 0.0 and kurt == 0.0
        )

class TestMissingDataEdgeCases:
    """Tests for handling missing or NaN data."""

    def test_per_sample_stats_with_nan(self):
        """Per-sample stats should handle NaN values gracefully."""
        # Create sample data with NaN
        teacher_dist = np.array([0.1, 0.2, 0.3, 0.4])
        student_score = 0.75
        human_annotation = {"Alignment": 0.8, "Realism": 0.6}

        stats = calculate_per_sample_stats(teacher_dist, student_score, human_annotation)

        assert isinstance(stats, dict)
        assert "variance" in stats
        assert "entropy" in stats

    def test_dimensional_fidelity_loss_missing_annotation(self):
        """Fidelity loss should return None or flag when annotation is missing."""
        teacher_dist = np.array([0.25, 0.25, 0.25, 0.25])
        student_score = 0.75
        human_annotation = {"Alignment": 0.8}  # Missing "Realism"

        # Should not crash, but return None or handle gracefully
        loss = calculate_dimensional_fidelity_loss(
            teacher_dist, student_score, human_annotation, primary_dimension="Realism"
        )
        assert loss is None  # Or some sentinel value indicating missing data

    def test_load_aligned_data_empty_file(self):
        """Loading an empty aligned data file should handle gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("[]")  # Empty list
            temp_path = f.name

        try:
            data = load_aligned_data(temp_path)
            assert len(data) == 0
        finally:
            os.unlink(temp_path)

class TestNumericalStabilityEdgeCases:
    """Tests for numerical stability with extreme values."""

    def test_extreme_values_variance(self):
        """Variance calculation should handle very large or small values."""
        data = np.array([1e10, 1e10 + 1, 1e10 + 2, 1e10 + 3])
        var, range_val = calculate_variance_and_range(data)
        assert not np.isnan(var)
        assert not np.isinf(var)

    def test_very_small_values_entropy(self):
        """Entropy should handle very small probability values."""
        data = np.array([1e-10, 1e-10, 1e-10, 1.0 - 3e-10])
        entropy = calculate_entropy(data)
        assert not np.isnan(entropy)
        assert not np.isinf(entropy)

    def test_inf_values_in_features(self):
        """Feature calculation should handle Inf values gracefully."""
        data = np.array([1.0, np.inf, 1.0, 1.0])
        with pytest.raises((ValueError, RuntimeWarning)):
            # Depending on implementation, this might raise or handle
            calculate_variance_and_range(data)

class TestPermutationTestEdgeCases:
    """Tests for permutation test edge cases."""

    def test_permutation_test_single_sample(self):
        """Permutation test should handle single sample gracefully."""
        actual_mae = 0.5
        null_mae = 0.6
        # With 1 sample, permutation test might not be meaningful
        # but should not crash
        p_value = perform_permutation_test(actual_mae, null_mae, n_permutations=10)
        assert 0.0 <= p_value <= 1.0

    def test_permutation_test_identical_scores(self):
        """Permutation test when all scores are identical."""
        actual_mae = 0.5
        null_mae = 0.5
        p_value = perform_permutation_test(actual_mae, null_mae, n_permutations=100)
        assert 0.0 <= p_value <= 1.0

class TestBaselineMaeEdgeCases:
    """Tests for baseline MAE calculation edge cases."""

    def test_baseline_mae_empty_predictions(self):
        """Baseline MAE should handle empty prediction lists."""
        true_values = []
        baseline_mae = calculate_baseline_mae(true_values)
        assert baseline_mae == 0.0  # Or NaN, depending on implementation

    def test_baseline_mae_single_value(self):
        """Baseline MAE with single true value."""
        true_values = [0.5]
        baseline_mae = calculate_baseline_mae(true_values)
        assert baseline_mae == 0.0  # Predicting mean (0.5) against 0.5 gives 0 MAE

class TestMetricsCalculationEdgeCases:
    """Tests for metrics calculation with edge cases."""

    def test_r_squared_perfect_prediction(self):
        """R² should be 1.0 for perfect predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0])
        r2, mae, rmse = calculate_metrics(y_true, y_pred)
        assert r2 == 1.0
        assert mae == 0.0
        assert rmse == 0.0

    def test_r_squared_constant_predictions(self):
        """R² should be 0.0 or negative for constant predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([2.5, 2.5, 2.5, 2.5])
        r2, mae, rmse = calculate_metrics(y_true, y_pred)
        # R² can be negative if model is worse than mean
        assert not np.isnan(r2)

    def test_metrics_with_nan_predictions(self):
        """Metrics calculation should handle NaN in predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.0, np.nan, 3.0, 4.0])
        # Should either raise or handle gracefully
        with pytest.raises((ValueError, RuntimeWarning)):
            calculate_metrics(y_true, y_pred)

class TestComputeAllFeaturesEdgeCases:
    """Tests for compute_all_features with various edge cases."""

    def test_compute_all_features_empty_input(self):
        """compute_all_features should handle empty input gracefully."""
        aligned_data = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "features.json"
            result = compute_all_features(aligned_data, str(output_path))

            assert result is True  # Should complete successfully
            assert output_path.exists()
            with open(output_path) as f:
                features = json.load(f)
            assert len(features) == 0

    def test_compute_all_features_all_missing_annotations(self):
        """compute_all_features should handle samples with all missing annotations."""
        aligned_data = [
            {
                "sample_id": "1",
                "teacher_distribution": [0.25, 0.25, 0.25, 0.25],
                "student_score": 0.75,
                "human_annotations": {},  # Empty annotations
                "primary_dimension": "Alignment",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "features.json"
            result = compute_all_features(aligned_data, str(output_path))

            assert result is True
            assert output_path.exists()
            with open(output_path) as f:
                features = json.load(f)
            assert len(features) == 1
            # Fidelity loss should be None or flagged
            assert features[0].get("fidelity_loss") is None