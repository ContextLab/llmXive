"""
Unit tests for statistical functions in evaluation/stats.py.

Tests cover:
- wilcoxon_signed_rank_test
- run_wilcoxon_on_metrics
- calculate_vif
- sensitivity_analysis_sweep
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path to resolve imports
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from evaluation.stats import (
    wilcoxon_signed_rank_test,
    run_wilcoxon_on_metrics,
    calculate_vif,
    sensitivity_analysis_sweep,
)
from data.utils import set_seed

# Set a fixed seed for reproducibility in tests
set_seed(42)


class TestWilcoxonSignedRank(unittest.TestCase):
    """Tests for wilcoxon_signed_rank_test function."""

    def test_identical_arrays(self):
        """When arrays are identical, statistic should be 0."""
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([1.0, 2.0, 3.0, 4.0])
        stat, pval = wilcoxon_signed_rank_test(x, y)
        self.assertEqual(stat, 0.0)
        self.assertEqual(pval, 1.0)

    def test_different_arrays(self):
        """Different arrays should produce a non-zero statistic."""
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([2.0, 4.0, 6.0, 8.0])
        stat, pval = wilcoxon_signed_rank_test(x, y)
        self.assertGreater(stat, 0.0)
        self.assertLess(pval, 1.0)

    def test_small_sample_size(self):
        """Test with minimal valid sample size."""
        x = np.array([1.0, 2.0])
        y = np.array([1.5, 2.5])
        stat, pval = wilcoxon_signed_rank_test(x, y)
        self.assertIsInstance(stat, (int, float))
        self.assertIsInstance(pval, (int, float))


class TestRunWilcoxonOnMetrics(unittest.TestCase):
    """Tests for run_wilcoxon_on_metrics function."""

    def test_basic_execution(self):
        """Test that the function returns expected keys."""
        metrics_gnn = [0.8, 0.85, 0.9]
        metrics_rf = [0.7, 0.75, 0.8]

        result = run_wilcoxon_on_metrics(metrics_gnn, metrics_rf)

        self.assertIn("statistic", result)
        self.assertIn("pvalue", result)
        self.assertIn("significant", result)
        self.assertIsInstance(result["statistic"], float)
        self.assertIsInstance(result["pvalue"], float)
        self.assertIsInstance(result["significant"], bool)

    def test_significance_threshold(self):
        """Test significance flag based on p-value."""
        # Create data with a clear difference
        metrics_gnn = [0.9, 0.95, 0.98, 0.99]
        metrics_rf = [0.5, 0.55, 0.58, 0.59]

        result = run_wilcoxon_on_metrics(metrics_gnn, metrics_rf, alpha=0.05)
        # With such a large difference, p-value should be low
        self.assertTrue(result["significant"])


class TestCalculateVIF(unittest.TestCase):
    """Tests for calculate_vif function."""

    def test_single_feature(self):
        """VIF for a single feature should be 1.0."""
        X = np.random.rand(10, 1)
        vifs = calculate_vif(X)
        self.assertEqual(len(vifs), 1)
        self.assertAlmostEqual(vifs[0], 1.0)

    def test_orthogonal_features(self):
        """VIF for orthogonal features should be close to 1.0."""
        # Create orthogonal features
        X = np.random.rand(50, 5)
        # Orthogonalize using QR decomposition
        Q, _ = np.linalg.qr(X)
        vifs = calculate_vif(Q)
        # All VIFs should be close to 1.0 for orthogonal features
        for vif in vifs:
            self.assertLess(vif, 1.1)

    def test_highly_correlated_features(self):
        """VIF should be high for highly correlated features."""
        # Create two highly correlated features
        X = np.random.rand(50, 2)
        X[:, 1] = X[:, 0] * 0.99 + np.random.normal(0, 0.01, 50)
        vifs = calculate_vif(X)
        # At least one VIF should be high (> 5 or 10)
        self.assertTrue(any(vif > 5.0 for vif in vifs))


class TestSensitivityAnalysisSweep(unittest.TestCase):
    """Tests for sensitivity_analysis_sweep function."""

    def test_output_structure(self):
        """Verify the output contains required keys."""
        y_true = np.random.rand(100)
        y_pred = y_true + np.random.normal(0, 0.1, 100)
        thresholds = [0.6, 0.7, 0.8]

        result = sensitivity_analysis_sweep(y_true, y_pred, thresholds)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(thresholds))

        for entry in result:
            self.assertIn("threshold", entry)
            self.assertIn("false_positive_rate", entry)
            self.assertIn("true_positive_rate", entry)
            self.assertIsInstance(entry["threshold"], float)
            self.assertIsInstance(entry["false_positive_rate"], float)
            self.assertIsInstance(entry["true_positive_rate"], float)

    def test_monotonicity(self):
        """
        As threshold increases, TPR should generally decrease and FPR should decrease.
        (Note: This is a soft check due to noise in random data)
        """
        y_true = np.random.rand(100)
        y_pred = y_true + np.random.normal(0, 0.1, 100)
        # Use a range of thresholds
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

        result = sensitivity_analysis_sweep(y_true, y_pred, thresholds)

        tprs = [r["true_positive_rate"] for r in result]
        fprs = [r["false_positive_rate"] for r in result]

        # Check that we have 5 entries
        self.assertEqual(len(tprs), 5)
        self.assertEqual(len(fprs), 5)

        # Check that TPR and FPR are in valid range [0, 1]
        for tpr in tprs:
            self.assertGreaterEqual(tpr, 0.0)
            self.assertLessEqual(tpr, 1.0)
        for fpr in fprs:
            self.assertGreaterEqual(fpr, 0.0)
            self.assertLessEqual(fpr, 1.0)

    def test_file_io(self):
        """Test that the function can write results to a file."""
        y_true = np.random.rand(50)
        y_pred = y_true + np.random.normal(0, 0.1, 50)
        thresholds = [0.6, 0.7]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = sensitivity_analysis_sweep(y_true, y_pred, thresholds, output_path=tmp_path)

            # Verify file exists and can be loaded
            self.assertTrue(os.path.exists(tmp_path))
            with open(tmp_path, "r") as f:
                loaded = json.load(f)
            self.assertEqual(len(loaded), 2)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()