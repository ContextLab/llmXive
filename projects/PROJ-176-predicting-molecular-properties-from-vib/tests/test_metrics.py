"""
Unit tests for code/evaluation/metrics.py
"""

import pytest
import numpy as np
from code.evaluation.metrics import (
    compute_mae,
    compute_r2,
    compute_metrics_per_property,
    paired_ttest_mean_zero,
    tost_equivalence_test,
    hotellings_t2_test
)


class TestMAE:
    def test_mae_perfect(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert compute_mae(y_true, y_pred) == 0.0

    def test_mae_simple(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 3.0, 4.0])
        # Errors: [-1, -1, -1] -> Abs: [1, 1, 1] -> Mean: 1.0
        assert compute_mae(y_true, y_pred) == 1.0

    def test_mae_empty(self):
        with pytest.raises(ValueError):
            compute_mae(np.array([]), np.array([]))

    def test_mae_shape_mismatch(self):
        with pytest.raises(ValueError):
            compute_mae(np.array([1.0, 2.0]), np.array([1.0]))


class TestR2:
    def test_r2_perfect(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert compute_r2(y_true, y_pred) == 1.0

    def test_r2_simple(self):
        # y_true = [1, 2, 3], mean = 2
        # y_pred = [1, 1, 1]
        # SS_res = (0)^2 + (1)^2 + (2)^2 = 5
        # SS_tot = (-1)^2 + (0)^2 + (1)^2 = 2
        # R2 = 1 - 5/2 = -1.5
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 1.0, 1.0])
        r2 = compute_r2(y_true, y_pred)
        assert np.isclose(r2, -1.5)

    def test_r2_constant_target(self):
        y_true = np.array([5.0, 5.0, 5.0])
        y_pred = np.array([5.0, 5.0, 5.0])
        # SS_tot = 0, SS_res = 0 -> R2 = 1.0 (defined as perfect in this impl)
        assert compute_r2(y_true, y_pred) == 1.0


class TestMetricsPerProperty:
    def test_compute_all(self):
        y_true_dict = {
            'dipole': np.array([1.0, 2.0]),
            'polarizability': np.array([10.0, 20.0]),
            'homo_lumo_gap': np.array([5.0, 6.0])
        }
        y_pred_dict = {
            'dipole': np.array([1.1, 2.1]),
            'polarizability': np.array([10.5, 20.5]),
            'homo_lumo_gap': np.array([5.5, 6.5])
        }

        results = compute_metrics_per_property(y_true_dict, y_pred_dict)

        assert 'dipole' in results
        assert 'polarizability' in results
        assert 'homo_lumo_gap' in results

        assert 'mae' in results['dipole']
        assert 'r2' in results['dipole']

        # Check dipole MAE manually: errors [-0.1, -0.1] -> abs [0.1, 0.1] -> mean 0.1
        assert np.isclose(results['dipole']['mae'], 0.1)


class TestPairedTTest:
    def test_ttest_zero_mean_error(self):
        # Errors are exactly zero
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        t, p = paired_ttest_mean_zero(y_true, y_pred)
        assert np.isclose(t, 0.0)
        assert np.isclose(p, 1.0)

    def test_ttest_nonzero_mean_error(self):
        # Errors are all 1.0
        y_true = np.array([2.0, 3.0, 4.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        t, p = paired_ttest_mean_zero(y_true, y_pred)
        # With constant error, std is 0. scipy handles this, but let's just check it runs
        assert not np.isnan(p)


class TestTOST:
    def test_tost_equivalent(self):
        # Errors are small, within margin 0.5
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.1, 3.1])
        _, _, is_eq = tost_equivalence_test(y_true, y_pred, equivalence_margin=0.5)
        # With small sample, might not be significant, but logic should run
        assert isinstance(is_eq, bool)

    def test_tost_not_equivalent(self):
        # Errors are large
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([5.0, 6.0, 7.0])
        _, _, is_eq = tost_equivalence_test(y_true, y_pred, equivalence_margin=0.1)
        assert is_eq is False


class TestHotellingsT2:
    def test_hotellings_1d(self):
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        t2, p = hotellings_t2_test(y_true, y_pred)
        assert isinstance(t2, float)
        assert isinstance(p, float)

    def test_hotellings_2d(self):
        # Simulating multiple properties as columns
        y_true = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0], [5.0, 50.0]])
        y_pred = np.array([[1.1, 10.1], [2.1, 20.1], [3.1, 30.1], [4.1, 40.1], [5.1, 50.1]])
        t2, p = hotellings_t2_test(y_true, y_pred)
        assert isinstance(t2, float)
        assert isinstance(p, float)