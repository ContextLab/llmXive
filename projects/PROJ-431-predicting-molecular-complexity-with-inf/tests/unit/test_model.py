"""Unit tests for model training and p-value correction logic (T018, T019, US2).

These tests verify:
1. Reproducible 80/20 train/test split with seed 42 (FR-005).
2. Ridge Regression training and metric computation.
3. Bonferroni correction for family-wise error rate (FR-010).
4. Benjamini-Hochberg correction for false discovery rate (FR-010).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr

# Make sibling modules in code/ importable when pytest runs from the
# project root.
CODE_DIR = Path(__file__).resolve().parents[2] / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from model import (
    train_ridge_model, 
    compute_bonferroni_pvalue, 
    compute_benjamini_hochberg_pvalues
)  # noqa: E402


def _make_dataset(n: int = 100, seed: int = 0):
    """Build a small deterministic regression dataset."""
    rng = np.random.RandomState(seed)
    X = rng.rand(n, 2)
    y = 3.0 * X[:, 0] - 1.5 * X[:, 1] + 0.1 * rng.randn(n)
    return X, y


class TestTrainTestSplit:
    """Tests for the 80/20 split semantics with seed 42."""

    def test_split_ratio_is_80_20(self):
        """train_test_split with test_size=0.2 yields exactly 80/20."""
        X, y = _make_dataset(n=100)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        assert len(X_train) == 80
        assert len(X_test) == 20
        assert len(y_train) == 80
        assert len(y_test) == 20

    def test_split_is_deterministic_with_seed_42(self):
        """Repeated splits with seed 42 produce identical partitions."""
        X, y = _make_dataset(n=50)
        X_tr1, X_te1, y_tr1, y_te1 = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        X_tr2, X_te2, y_tr2, y_te2 = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        np.testing.assert_array_equal(X_tr1, X_tr2)
        np.testing.assert_array_equal(X_te1, X_te2)
        np.testing.assert_array_equal(y_tr1, y_tr2)
        np.testing.assert_array_equal(y_te1, y_te2)

    def test_split_ratio_for_non_round_n(self):
        """For n=101, the test set gets ceil-ish 20% (21 or 20 rows)."""
        X, y = _make_dataset(n=101)
        X_train, X_test, _, _ = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        assert len(X_test) in (20, 21)
        assert len(X_train) + len(X_test) == 101

    def test_train_and_test_are_disjoint(self):
        """No test row appears in the training partition."""
        X, y = _make_dataset(n=60)
        X_train, X_test, _, _ = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        train_rows = {tuple(row) for row in X_train}
        test_rows = {tuple(row) for row in X_test}
        assert train_rows.isdisjoint(test_rows)
        assert train_rows | test_rows == {tuple(r) for r in X}


class TestTrainRidgeModelSplit:
    """Tests that train_ridge_model honors the 80/20 seed-42 split."""

    def test_returns_model_and_metrics(self):
        X, y = _make_dataset(n=80)
        model, metrics = train_ridge_model(X, y, alpha=1.0, random_state=42)
        assert isinstance(model, Ridge)
        assert "rmse" in metrics
        assert "pearson_r" in metrics

    def test_seed_42_is_reproducible(self):
        """Two runs with seed 42 must give identical metrics and coefficients."""
        X, y = _make_dataset(n=100)
        model1, metrics1 = train_ridge_model(X, y, alpha=1.0, random_state=42)
        model2, metrics2 = train_ridge_model(X, y, alpha=1.0, random_state=42)
        assert metrics1["rmse"] == pytest.approx(metrics2["rmse"])
        assert metrics1["pearson_r"] == pytest.approx(metrics2["pearson_r"])
        np.testing.assert_array_equal(model1.coef_, model2.coef_)
        assert model1.intercept_ == pytest.approx(model2.intercept_)

    def test_default_random_state_is_42(self):
        """Calling without an explicit seed must equal the seed-42 run."""
        X, y = _make_dataset(n=90)
        model_default, metrics_default = train_ridge_model(X, y, alpha=1.0)
        model_42, metrics_42 = train_ridge_model(
            X, y, alpha=1.0, random_state=42
        )
        assert metrics_default["rmse"] == pytest.approx(metrics_42["rmse"])
        assert metrics_default["pearson_r"] == pytest.approx(
            metrics_42["pearson_r"]
        )
        np.testing.assert_array_equal(model_default.coef_, model_42.coef_)

    def test_metrics_computed_on_20_percent_test_split(self):
        """Reported metrics must match a manual 80/20 seed-42 evaluation."""
        X, y = _make_dataset(n=200, seed=7)
        model, metrics = train_ridge_model(X, y, alpha=1.0, random_state=42)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        manual = Ridge(alpha=1.0)
        manual.fit(X_train, y_train)
        preds = manual.predict(X_test)

        manual_rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        manual_r = float(pearsonr(y_test, preds)[0])

        assert len(X_test) == 40  # exactly 20% of 200
        assert metrics["rmse"] == pytest.approx(manual_rmse, rel=1e-6)
        assert metrics["pearson_r"] == pytest.approx(manual_r, abs=1e-6)
        np.testing.assert_allclose(model.coef_, manual.coef_, rtol=1e-6)

    def test_metrics_are_finite(self):
        X, y = _make_dataset(n=50)
        _, metrics = train_ridge_model(X, y, alpha=1.0, random_state=42)
        assert np.isfinite(metrics["rmse"])
        assert np.isfinite(metrics["pearson_r"])
        assert metrics["rmse"] >= 0
        assert -1.0 <= metrics["pearson_r"] <= 1.0


class TestPValueCorrection:
    """Tests for Bonferroni and Benjamini-Hochberg correction logic (T019)."""

    def test_bonferroni_correction(self):
        """Verify p_adj = min(p * n, 1.0)."""
        # Case 1: Typical adjustment
        assert compute_bonferroni_pvalue(0.01, 4) == pytest.approx(0.04)
        # Case 2: Capped at 1.0
        assert compute_bonferroni_pvalue(0.3, 4) == 1.0
        # Case 3: Zero p-value
        assert compute_bonferroni_pvalue(0.0, 4) == 0.0
        # Case 4: Single test
        assert compute_bonferroni_pvalue(0.05, 1) == 0.05

    def test_benjamini_hochberg_correction(self):
        """Verify FDR adjustment logic."""
        # Case 1: Sorted p-values with clear separation
        # p = [0.001, 0.01, 0.1, 0.5], n=4
        # i=4: 0.5 * 4/4 = 0.5
        # i=3: 0.1 * 4/3 = 0.1333... -> min(0.1333, 0.5) = 0.1333
        # i=2: 0.01 * 4/2 = 0.02 -> min(0.02, 0.1333) = 0.02
        # i=1: 0.001 * 4/1 = 0.004 -> min(0.004, 0.02) = 0.004
        p_vals = [0.001, 0.01, 0.1, 0.5]
        expected = [0.004, 0.02, 0.13333333333333333, 0.5]
        adjusted = compute_benjamini_hochberg_pvalues(p_vals)
        np.testing.assert_allclose(adjusted, expected, rtol=1e-5)

        # Case 2: Unsorted p-values
        # Original: [0.04, 0.01, 0.03, 0.02] -> Sorted: [0.01, 0.02, 0.03, 0.04]
        # i=4: 0.04 * 4/4 = 0.04
        # i=3: 0.03 * 4/3 = 0.04 -> 0.04
        # i=2: 0.02 * 4/2 = 0.04 -> 0.04
        # i=1: 0.01 * 4/1 = 0.04 -> 0.04
        p_vals_unsorted = [0.04, 0.01, 0.03, 0.02]
        expected_unsorted = [0.04, 0.04, 0.04, 0.04]
        adjusted_unsorted = compute_benjamini_hochberg_pvalues(p_vals_unsorted)
        np.testing.assert_allclose(adjusted_unsorted, expected_unsorted, rtol=1e-5)

    def test_bh_edge_cases(self):
        """Verify BH handles empty and single-element lists."""
        assert compute_benjamini_hochberg_pvalues([]) == []
        assert compute_benjamini_hochberg_pvalues([0.05]) == [0.05]
        assert compute_benjamini_hochberg_pvalues([1.0]) == [1.0]
        assert compute_benjamini_hochberg_pvalues([0.0]) == [0.0]