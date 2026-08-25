"""
Unit test for Equalized Odds Difference formula.

This test validates the implementation of the Equalized Odds Difference metric
as defined in the project specification. Equalized Odds requires that the true
positive rate (TPR) and false positive rate (FPR) are equal across protected
groups.

Formula:
  Equalized Odds Difference = max(|TPR_0 - TPR_1|, |FPR_0 - FPR_1|)

Where:
  TPR = TP / (TP + FN)
  FPR = FP / (FP + TN)
  Groups are defined by the protected attribute (0 and 1).

Citation: Hardt, M., Price, E., & Srebro, N. (2016). Equality of Opportunity
in Supervised Learning. NIPS.
"""

import pytest
import numpy as np
import pandas as pd
from typing import Tuple, List

# Import the metric implementation from the project's utility module
# The formula is implemented in code/utils/metrics.py as per T006
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.metrics import compute_equalized_odds_difference


def test_equalized_odds_perfect_parity():
    """
    Test case where both TPR and FPR are identical across groups.
    Expected difference should be 0.0.
    """
    y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    protected = np.array([0, 0, 0, 0, 1, 1, 1, 1])

    # Group 0: TPR = 2/4 = 0.5, FPR = 2/4 = 0.5
    # Group 1: TPR = 2/4 = 0.5, FPR = 2/4 = 0.5
    # Diff = max(|0.5-0.5|, |0.5-0.5|) = 0.0

    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.0, rel=1e-9)


def test_equalized_odds_tpr_disparity_only():
    """
    Test case where TPR differs but FPR is equal.
    """
    # Group 0: 4 positives, 4 negatives
    # y_true: [1,1,1,1, 0,0,0,0]
    # y_pred: [1,1,1,0, 0,0,0,0] -> TP=3, FN=1 -> TPR=0.75
    #         -> TN=4, FP=0 -> FPR=0.0
    y_true_0 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_0 = np.array([1, 1, 1, 0, 0, 0, 0, 0])
    protected_0 = np.zeros(8, dtype=int)

    # Group 1: 4 positives, 4 negatives
    # y_true: [1,1,1,1, 0,0,0,0]
    # y_pred: [1,1,0,0, 0,0,0,0] -> TP=2, FN=2 -> TPR=0.5
    #         -> TN=4, FP=0 -> FPR=0.0
    y_true_1 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_1 = np.array([1, 1, 0, 0, 0, 0, 0, 0])
    protected_1 = np.ones(8, dtype=int)

    y_true = np.concatenate([y_true_0, y_true_1])
    y_pred = np.concatenate([y_pred_0, y_pred_1])
    protected = np.concatenate([protected_0, protected_1])

    # TPR_0 = 0.75, TPR_1 = 0.5 -> |0.25|
    # FPR_0 = 0.0, FPR_1 = 0.0 -> |0.0|
    # Expected = 0.25

    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.25, rel=1e-9)


def test_equalized_odds_fpr_disparity_only():
    """
    Test case where FPR differs but TPR is equal.
    """
    # Group 0: 4 positives, 4 negatives
    # y_true: [1,1,1,1, 0,0,0,0]
    # y_pred: [1,1,1,1, 1,0,0,0] -> TP=4, FN=0 -> TPR=1.0
    #         -> TN=3, FP=1 -> FPR=0.25
    y_true_0 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_0 = np.array([1, 1, 1, 1, 1, 0, 0, 0])
    protected_0 = np.zeros(8, dtype=int)

    # Group 1: 4 positives, 4 negatives
    # y_true: [1,1,1,1, 0,0,0,0]
    # y_pred: [1,1,1,1, 0,0,0,0] -> TP=4, FN=0 -> TPR=1.0
    #         -> TN=4, FP=0 -> FPR=0.0
    y_true_1 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_1 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    protected_1 = np.ones(8, dtype=int)

    y_true = np.concatenate([y_true_0, y_true_1])
    y_pred = np.concatenate([y_pred_0, y_pred_1])
    protected = np.concatenate([protected_0, protected_1])

    # TPR_0 = 1.0, TPR_1 = 1.0 -> |0.0|
    # FPR_0 = 0.25, FPR_1 = 0.0 -> |0.25|
    # Expected = 0.25

    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.25, rel=1e-9)


def test_equalized_odds_combined_disparity():
    """
    Test case where both TPR and FPR differ.
    The metric should return the maximum of the two absolute differences.
    """
    # Group 0
    y_true_0 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_0 = np.array([1, 1, 1, 0, 1, 0, 0, 0])
    # TP=3, FN=1 -> TPR=0.75
    # TN=3, FP=1 -> FPR=0.25
    protected_0 = np.zeros(8, dtype=int)

    # Group 1
    y_true_1 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_1 = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    # TP=2, FN=2 -> TPR=0.5
    # TN=2, FP=2 -> FPR=0.5
    protected_1 = np.ones(8, dtype=int)

    y_true = np.concatenate([y_true_0, y_true_1])
    y_pred = np.concatenate([y_pred_0, y_pred_1])
    protected = np.concatenate([protected_0, protected_1])

    # |TPR_0 - TPR_1| = |0.75 - 0.5| = 0.25
    # |FPR_0 - FPR_1| = |0.25 - 0.5| = 0.25
    # Max = 0.25
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.25, rel=1e-9)


def test_equalized_odds_asymmetric_disparity():
    """
    Test case where FPR difference is larger than TPR difference.
    """
    # Group 0: TPR=1.0, FPR=0.0
    y_true_0 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_0 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    protected_0 = np.zeros(8, dtype=int)

    # Group 1: TPR=0.5, FPR=0.5
    y_true_1 = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    y_pred_1 = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    protected_1 = np.ones(8, dtype=int)

    y_true = np.concatenate([y_true_0, y_true_1])
    y_pred = np.concatenate([y_pred_0, y_pred_1])
    protected = np.concatenate([protected_0, protected_1])

    # |TPR_0 - TPR_1| = |1.0 - 0.5| = 0.5
    # |FPR_0 - FPR_1| = |0.0 - 0.5| = 0.5
    # Max = 0.5
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.5, rel=1e-9)


def test_equalized_odds_zero_predictions():
    """
    Test case where all predictions are 0.
    TPR = 0, FPR = 0 for both groups.
    """
    y_true = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    y_pred = np.zeros(8, dtype=int)
    protected = np.array([0, 0, 0, 0, 1, 1, 1, 1])

    # Both groups: TPR=0, FPR=0
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.0, rel=1e-9)


def test_equalized_odds_all_positive_predictions():
    """
    Test case where all predictions are 1.
    TPR = 1, FPR = 1 for both groups.
    """
    y_true = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    y_pred = np.ones(8, dtype=int)
    protected = np.array([0, 0, 0, 0, 1, 1, 1, 1])

    # Both groups: TPR=1, FPR=1
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(0.0, rel=1e-9)


def test_equalized_odds_edge_case_single_sample_per_group():
    """
    Test case with minimal data: one sample per group.
    This tests handling of potential division by zero if logic is flawed,
    though mathematically TPR/FPR are well-defined if denominators > 0.
    """
    # Group 0: 1 positive, predicted positive -> TPR=1, FPR=N/A (no negatives)
    # Actually, we need at least one negative to compute FPR.
    # Let's construct a case where denominators are valid.
    
    # Group 0: 1 pos (pred 1), 1 neg (pred 0) -> TPR=1, FPR=0
    y_true_0 = np.array([1, 0])
    y_pred_0 = np.array([1, 0])
    protected_0 = np.array([0, 0])

    # Group 1: 1 pos (pred 0), 1 neg (pred 1) -> TPR=0, FPR=1
    y_true_1 = np.array([1, 0])
    y_pred_1 = np.array([0, 1])
    protected_1 = np.array([1, 1])

    y_true = np.concatenate([y_true_0, y_true_1])
    y_pred = np.concatenate([y_pred_0, y_pred_1])
    protected = np.concatenate([protected_0, protected_1])

    # |TPR_0 - TPR_1| = |1 - 0| = 1
    # |FPR_0 - FPR_1| = |0 - 1| = 1
    # Max = 1.0
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(1.0, rel=1e-9)


def test_equalized_odds_invalid_input_types():
    """
    Test that the function handles numpy arrays correctly.
    """
    y_true = pd.Series([1, 1, 0, 0])
    y_pred = pd.Series([1, 0, 1, 0])
    protected = pd.Series([0, 0, 1, 1])

    # Should convert or handle pandas series if implemented,
    # or raise error if strict numpy is required.
    # Assuming the implementation handles array-like inputs.
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert isinstance(result, float) or np.isscalar(result)
    assert 0.0 <= result <= 1.0


def test_equalized_odds_large_imbalance():
    """
    Test with highly imbalanced classes to ensure numerical stability.
    """
    n_pos_0 = 10
    n_neg_0 = 990
    n_pos_1 = 10
    n_neg_1 = 990

    # Group 0: All correct
    y_true_0 = np.array([1]*n_pos_0 + [0]*n_neg_0)
    y_pred_0 = np.array([1]*n_pos_0 + [0]*n_neg_0)
    protected_0 = np.zeros(n_pos_0 + n_neg_0, dtype=int)

    # Group 1: All wrong (flip)
    y_true_1 = np.array([1]*n_pos_1 + [0]*n_neg_1)
    y_pred_1 = np.array([0]*n_pos_1 + [1]*n_neg_1)
    protected_1 = np.ones(n_pos_1 + n_neg_1, dtype=int)

    y_true = np.concatenate([y_true_0, y_true_1])
    y_pred = np.concatenate([y_pred_0, y_pred_1])
    protected = np.concatenate([protected_0, protected_1])

    # Group 0: TPR=1, FPR=0
    # Group 1: TPR=0, FPR=1
    # Diff = max(1, 1) = 1.0
    result = compute_equalized_odds_difference(y_true, y_pred, protected)
    assert result == pytest.approx(1.0, rel=1e-9)