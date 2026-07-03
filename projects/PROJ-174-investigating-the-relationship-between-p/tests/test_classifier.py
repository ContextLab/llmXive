"""
Unit tests for the sensitivity analysis logic in the classification pipeline.
This module tests the sensitivity analysis component for User Story 3.
"""

import os
import sys
import tempfile
import shutil
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add the code directory to the path to allow imports from sibling modules
# Note: In a real environment, the code/ directory would be in the PYTHONPATH
# or installed as a package. For testing, we adjust sys.path.
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Import the sensitivity analysis logic we are testing
# Since the actual implementation is in code/classification/sensitivity.py (to be created in T031),
# we will test the logic that would be there. For now, we implement a minimal version
# of the sensitivity analysis function to test against, as the full implementation
# is part of T031.
# However, per the task description, T027 is about testing the *logic* of sensitivity analysis.
# We will create a mock of the expected interface and test the logic.

# We will assume the existence of a function `run_sensitivity_analysis` in a module
# that we are about to test. Since T031 is not yet implemented, we will create a
# temporary module for testing purposes that contains the logic we want to verify.
# In the actual project, this logic would reside in `code/classification/sensitivity.py`.

# For the purpose of this test, we will define the function here to ensure the test
# logic is correct. The actual implementation in T031 will move this logic to the
# proper module.

def run_sensitivity_analysis_logic(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    thresholds: list,
    metric: str = "accuracy"
) -> pd.DataFrame:
    """
    Core logic for sensitivity analysis.

    Args:
        predictions: Array of predicted probabilities (0.0 to 1.0).
        ground_truth: Array of binary ground truth labels (0 or 1).
        thresholds: List of threshold values to test (e.g., [0.40, 0.50, 0.60]).
        metric: Metric to calculate ('accuracy', 'precision', 'recall', 'f1', 'auc').

    Returns:
        DataFrame with columns: threshold, metric_value, and relative_decrease (if applicable).
    """
    results = []

    # Calculate baseline at 0.50 if present, otherwise use first threshold
    baseline_threshold = 0.50 if 0.50 in thresholds else thresholds[0]
    baseline_y_pred = (predictions >= baseline_threshold).astype(int)
    baseline_metric = None

    if metric == "accuracy":
        baseline_metric = np.mean(baseline_y_pred == ground_truth)
    elif metric == "precision":
        tp = np.sum((baseline_y_pred == 1) & (ground_truth == 1))
        fp = np.sum((baseline_y_pred == 1) & (ground_truth == 0))
        if tp + fp > 0:
            baseline_metric = tp / (tp + fp)
        else:
            baseline_metric = 0.0
    elif metric == "recall":
        tp = np.sum((baseline_y_pred == 1) & (ground_truth == 1))
        fn = np.sum((baseline_y_pred == 0) & (ground_truth == 1))
        if tp + fn > 0:
            baseline_metric = tp / (tp + fn)
        else:
            baseline_metric = 0.0
    elif metric == "f1":
        tp = np.sum((baseline_y_pred == 1) & (ground_truth == 1))
        fp = np.sum((baseline_y_pred == 1) & (ground_truth == 0))
        fn = np.sum((baseline_y_pred == 0) & (ground_truth == 1))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if precision + recall > 0:
            baseline_metric = 2 * (precision * recall) / (precision + recall)
        else:
            baseline_metric = 0.0
    elif metric == "auc":
        # Simple AUC calculation for binary case
        from sklearn.metrics import roc_auc_score
        try:
            baseline_metric = roc_auc_score(ground_truth, predictions)
        except ValueError:
            # If only one class is present
            baseline_metric = 0.5

    for thresh in thresholds:
        y_pred = (predictions >= thresh).astype(int)

        if metric == "accuracy":
            value = np.mean(y_pred == ground_truth)
        elif metric == "precision":
            tp = np.sum((y_pred == 1) & (ground_truth == 1))
            fp = np.sum((y_pred == 1) & (ground_truth == 0))
            value = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        elif metric == "recall":
            tp = np.sum((y_pred == 1) & (ground_truth == 1))
            fn = np.sum((y_pred == 0) & (ground_truth == 1))
            value = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        elif metric == "f1":
            tp = np.sum((y_pred == 1) & (ground_truth == 1))
            fp = np.sum((y_pred == 1) & (ground_truth == 0))
            fn = np.sum((y_pred == 0) & (ground_truth == 1))
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            value = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        elif metric == "auc":
            try:
                value = roc_auc_score(ground_truth, predictions)
            except ValueError:
                value = 0.5

        # Calculate relative decrease from baseline
        relative_decrease = None
        if baseline_metric is not None and baseline_metric > 0:
            relative_decrease = (baseline_metric - value) / baseline_metric

        results.append({
            "threshold": thresh,
            "metric_value": value,
            "relative_decrease": relative_decrease
        })

    return pd.DataFrame(results)


class TestSensitivityAnalysisLogic:
    """Tests for the sensitivity analysis logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a simple synthetic dataset for testing
        np.random.seed(42)
        self.n_samples = 1000
        self.predictions = np.random.rand(self.n_samples)
        # Create ground truth that is somewhat correlated with predictions
        self.ground_truth = (self.predictions > 0.5).astype(int)
        # Add some noise
        noise_indices = np.random.choice(self.n_samples, size=50, replace=False)
        self.ground_truth[noise_indices] = 1 - self.ground_truth[noise_indices]

        self.thresholds = [0.40, 0.50, 0.60]

    def test_sensitivity_analysis_accuracy(self):
        """Test sensitivity analysis with accuracy metric."""
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            self.thresholds,
            metric="accuracy"
        )

        assert len(df) == len(self.thresholds)
        assert "threshold" in df.columns
        assert "metric_value" in df.columns
        assert "relative_decrease" in df.columns

        # Check that metric values are between 0 and 1
        assert all(df["metric_value"] >= 0)
        assert all(df["metric_value"] <= 1)

        # Check that relative decrease is calculated correctly for 0.50 threshold
        baseline_row = df[df["threshold"] == 0.50]
        assert baseline_row["relative_decrease"].iloc[0] == 0.0  # Baseline has 0 decrease

    def test_sensitivity_analysis_precision(self):
        """Test sensitivity analysis with precision metric."""
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            self.thresholds,
            metric="precision"
        )

        assert len(df) == len(self.thresholds)
        assert all(df["metric_value"] >= 0)
        assert all(df["metric_value"] <= 1)

    def test_sensitivity_analysis_recall(self):
        """Test sensitivity analysis with recall metric."""
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            self.thresholds,
            metric="recall"
        )

        assert len(df) == len(self.thresholds)
        assert all(df["metric_value"] >= 0)
        assert all(df["metric_value"] <= 1)

    def test_sensitivity_analysis_f1(self):
        """Test sensitivity analysis with F1 metric."""
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            self.thresholds,
            metric="f1"
        )

        assert len(df) == len(self.thresholds)
        assert all(df["metric_value"] >= 0)
        assert all(df["metric_value"] <= 1)

    def test_sensitivity_analysis_auc(self):
        """Test sensitivity analysis with AUC metric."""
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            self.thresholds,
            metric="auc"
        )

        assert len(df) == len(self.thresholds)
        # AUC should be between 0 and 1
        assert all(df["metric_value"] >= 0)
        assert all(df["metric_value"] <= 1)

    def test_sensitivity_analysis_edge_cases(self):
        """Test sensitivity analysis with edge cases."""
        # Test with all same predictions
        same_predictions = np.ones(self.n_samples) * 0.5
        same_ground_truth = np.ones(self.n_samples)
        df = run_sensitivity_analysis_logic(
            same_predictions,
            same_ground_truth,
            self.thresholds,
            metric="accuracy"
        )
        assert len(df) == len(self.thresholds)

        # Test with empty thresholds
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            [],
            metric="accuracy"
        )
        assert len(df) == 0

    def test_sensitivity_analysis_relative_decrease_calculation(self):
        """Test that relative decrease is calculated correctly."""
        # Create a scenario where we know the exact values
        predictions = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        ground_truth = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        thresholds = [0.5, 0.6, 0.7]

        df = run_sensitivity_analysis_logic(
            predictions,
            ground_truth,
            thresholds,
            metric="accuracy"
        )

        # At threshold 0.5: predictions >= 0.5 are [0.5, 0.6, 0.7, 0.8, 0.9, 1.0] -> [1, 1, 1, 1, 1, 1]
        # Ground truth: [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
        # Matches: [0, 0, 0, 0, 1, 1, 1, 1, 1, 1] -> 8/10 = 0.8
        # At threshold 0.6: predictions >= 0.6 are [0.6, 0.7, 0.8, 0.9, 1.0] -> [1, 1, 1, 1, 1]
        # Matches: [0, 0, 0, 0, 1, 1, 1, 1, 1, 1] -> 7/10 = 0.7
        # At threshold 0.7: predictions >= 0.7 are [0.7, 0.8, 0.9, 1.0] -> [1, 1, 1, 1]
        # Matches: [0, 0, 0, 0, 1, 1, 1, 1, 1, 1] -> 6/10 = 0.6

        # Baseline is 0.5 -> 0.8
        # 0.6 -> 0.7 -> relative decrease = (0.8 - 0.7) / 0.8 = 0.125
        # 0.7 -> 0.6 -> relative decrease = (0.8 - 0.6) / 0.8 = 0.25

        assert df[df["threshold"] == 0.5]["metric_value"].iloc[0] == 0.8
        assert df[df["threshold"] == 0.6]["metric_value"].iloc[0] == 0.7
        assert df[df["threshold"] == 0.7]["metric_value"].iloc[0] == 0.6

        assert df[df["threshold"] == 0.5]["relative_decrease"].iloc[0] == 0.0
        assert np.isclose(df[df["threshold"] == 0.6]["relative_decrease"].iloc[0], 0.125)
        assert np.isclose(df[df["threshold"] == 0.7]["relative_decrease"].iloc[0], 0.25)

    def test_sensitivity_analysis_with_missing_baseline(self):
        """Test sensitivity analysis when baseline threshold (0.50) is not in list."""
        thresholds = [0.40, 0.60]  # No 0.50
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            thresholds,
            metric="accuracy"
        )

        # Baseline should be the first threshold (0.40)
        baseline_row = df[df["threshold"] == 0.40]
        assert baseline_row["relative_decrease"].iloc[0] == 0.0

    def test_sensitivity_analysis_output_format(self):
        """Test that the output DataFrame has the correct format."""
        df = run_sensitivity_analysis_logic(
            self.predictions,
            self.ground_truth,
            self.thresholds,
            metric="accuracy"
        )

        expected_columns = ["threshold", "metric_value", "relative_decrease"]
        assert list(df.columns) == expected_columns
        assert df["threshold"].dtype in [np.float64, np.float32, int]
        assert df["metric_value"].dtype in [np.float64, np.float32]
        # relative_decrease can be float or NaN
        assert df["relative_decrease"].dtype in [np.float64, np.float32]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])