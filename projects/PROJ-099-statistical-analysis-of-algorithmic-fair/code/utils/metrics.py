"""
Fairness metric computation module for algorithmic fairness analysis.

This module implements standard fairness metrics used in algorithmic auditing.
All formulas include LaTeX notation and citations to Appendix A of the project
specification document.

Metrics implemented:
- Demographic Parity Difference
- Equalized Odds Difference
- Predictive Parity
- Calibration Within Groups
- Disparate Impact Ratio
- False Positive Rate Disparity
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from sklearn.metrics import confusion_matrix, precision_score, recall_score


def demographic_parity_difference(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    protected_attribute: np.ndarray
) -> float:
    """
    Calculate the Demographic Parity Difference.

    Demographic parity requires that the probability of a positive prediction
    is independent of the protected attribute.

    Formula:
    .. math::

        DP_{diff} = |P(\\hat{Y}=1 | A=1) - P(\\hat{Y}=1 | A=0)|

    Where:
    - :math:`\\hat{Y}` is the predicted outcome
    - :math:`A` is the protected attribute (binary: 0 or 1)

    Citation:
    - Dwork, C., Hardt, M., Pitassi, T., Reingold, O., & Rothblum, G. (2012).
      Fairness through awareness. In Proceedings of the 3rd Innovations in
      Theoretical Computer Science Conference (pp. 214-226).
      Appendix A, Section A.1.

    Args:
        y_true: True labels (not used in this metric, but included for consistency)
        y_pred: Predicted labels
        protected_attribute: Binary protected attribute values (0 or 1)

    Returns:
        Absolute difference in positive prediction rates between groups
    """
    # Calculate positive prediction rate for group A=1
    mask_1 = protected_attribute == 1
    rate_1 = np.mean(y_pred[mask_1]) if np.sum(mask_1) > 0 else 0.0

    # Calculate positive prediction rate for group A=0
    mask_0 = protected_attribute == 0
    rate_0 = np.mean(y_pred[mask_0]) if np.sum(mask_0) > 0 else 0.0

    return abs(rate_1 - rate_0)


def equalized_odds_difference(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    protected_attribute: np.ndarray
) -> float:
    """
    Calculate the Equalized Odds Difference.

    Equalized odds requires that the true positive rate and false positive rate
    are equal across groups defined by the protected attribute.

    Formula:
    .. math::

        EO_{diff} = |TPR_1 - TPR_0| + |FPR_1 - FPR_0|

    Where:
    - :math:`TPR_a = P(\\hat{Y}=1 | Y=1, A=a)` (True Positive Rate)
    - :math:`FPR_a = P(\\hat{Y}=1 | Y=0, A=a)` (False Positive Rate)

    Citation:
    - Hardt, M., Price, E., & Srebro, N. (2016). Equality of opportunity in
      supervised learning. In Advances in Neural Information Processing Systems
      (pp. 3315-3323). Appendix A, Section A.2.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        protected_attribute: Binary protected attribute values (0 or 1)

    Returns:
        Sum of absolute differences in TPR and FPR between groups
    """
    # Calculate for group A=1
    mask_1 = protected_attribute == 1
    y_true_1 = y_true[mask_1]
    y_pred_1 = y_pred[mask_1]

    # Calculate for group A=0
    mask_0 = protected_attribute == 0
    y_true_0 = y_true[mask_0]
    y_pred_0 = y_pred[mask_0]

    def calculate_rates(y_true_group, y_pred_group):
        if len(y_true_group) == 0:
            return 0.0, 0.0

        # True Positive Rate: P(Y_hat=1 | Y=1)
        positive_actual = y_true_group == 1
        tpr = np.mean(y_pred_group[positive_actual]) if np.sum(positive_actual) > 0 else 0.0

        # False Positive Rate: P(Y_hat=1 | Y=0)
        negative_actual = y_true_group == 0
        fpr = np.mean(y_pred_group[negative_actual]) if np.sum(negative_actual) > 0 else 0.0

        return tpr, fpr

    tpr_1, fpr_1 = calculate_rates(y_true_1, y_pred_1)
    tpr_0, fpr_0 = calculate_rates(y_true_0, y_pred_0)

    return abs(tpr_1 - tpr_0) + abs(fpr_1 - fpr_0)


def predictive_parity(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    protected_attribute: np.ndarray
) -> float:
    """
    Calculate the Predictive Parity Difference.

    Predictive parity requires that the positive predictive value (precision)
    is equal across groups.

    Formula:
    .. math::

        PP_{diff} = |PPV_1 - PPV_0|

    Where:
    - :math:`PPV_a = P(Y=1 | \\hat{Y}=1, A=a)` (Positive Predictive Value)

    Citation:
    - Chouldechova, A. (2017). Fair prediction with disparate impact: A
      study of bias in recidivism prediction instruments. Big Data, 5(2),
      153-163. Appendix A, Section A.3.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        protected_attribute: Binary protected attribute values (0 or 1)

    Returns:
        Absolute difference in positive predictive values between groups
    """
    # Calculate for group A=1
    mask_1 = protected_attribute == 1
    y_true_1 = y_true[mask_1]
    y_pred_1 = y_pred[mask_1]

    # Calculate for group A=0
    mask_0 = protected_attribute == 0
    y_true_0 = y_true[mask_0]
    y_pred_0 = y_pred[mask_0]

    def calculate_ppv(y_true_group, y_pred_group):
        if np.sum(y_pred_group) == 0:
            return 0.0
        return np.mean(y_true_group[y_pred_group == 1])

    ppv_1 = calculate_ppv(y_true_1, y_pred_1)
    ppv_0 = calculate_ppv(y_true_0, y_pred_0)

    return abs(ppv_1 - ppv_0)


def calibration_within_groups(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    protected_attribute: np.ndarray,
    bins: int = 10
) -> float:
    """
    Calculate the Calibration Within Groups metric.

    Calibration requires that among instances with predicted probability p,
    the fraction of positive outcomes is approximately p, for each group.

    Formula:
    .. math::

        Cal_{diff} = \\sum_{a \\in \\{0,1\\}} \\frac{1}{B} \\sum_{b=1}^{B}
        |P(Y=1 | \\hat{P} \\in B_b, A=a) - \\text{mean}(\\hat{P} | \\hat{P} \\in B_b, A=a)|

    Where:
    - :math:`B` is the number of bins
    - :math:`B_b` is the b-th bin of predicted probabilities

    Citation:
    - Pleiss, G., Raghu, M., Weninger, S., Kleinberg, J., & Weinberger, K. Q.
      (2017). On fairness and calibration. In Advances in Neural Information
      Processing Systems (pp. 5680-5689). Appendix A, Section A.4.

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities (not binary predictions)
        protected_attribute: Binary protected attribute values (0 or 1)
        bins: Number of bins for calibration calculation

    Returns:
        Average absolute calibration error across groups and bins
    """
    total_error = 0.0
    group_count = 0

    for group in [0, 1]:
        mask = protected_attribute == group
        y_true_group = y_true[mask]
        y_pred_group = y_pred_proba[mask]

        if len(y_true_group) == 0:
            continue

        group_count += 1
        bin_edges = np.linspace(0, 1, bins + 1)
        group_error = 0.0

        for i in range(bins):
            bin_mask = (y_pred_group >= bin_edges[i]) & (y_pred_group < bin_edges[i + 1])
            if i == bins - 1:  # Include right edge for last bin
                bin_mask = (y_pred_group >= bin_edges[i]) & (y_pred_group <= bin_edges[i + 1])

            if np.sum(bin_mask) == 0:
                continue

            bin_y_true = y_true_group[bin_mask]
            bin_y_pred = y_pred_group[bin_mask]

            actual_rate = np.mean(bin_y_true)
            predicted_rate = np.mean(bin_y_pred)
            group_error += abs(actual_rate - predicted_rate)

        avg_group_error = group_error / bins
        total_error += avg_group_error

    return total_error / group_count if group_count > 0 else 0.0


def disparate_impact_ratio(
    y_pred: np.ndarray,
    protected_attribute: np.ndarray
) -> float:
    """
    Calculate the Disparate Impact Ratio.

    Disparate impact is the ratio of positive prediction rates between groups.
    A ratio below 0.8 (or above 1.25) is often considered indicative of disparate impact.

    Formula:
    .. math::

        DI = \\frac{P(\\hat{Y}=1 | A=1)}{P(\\hat{Y}=1 | A=0)}

    Citation:
    - Feldman, M., Friedler, S. A., Moeller, J., Scheidegger, C., & Venkatasubramanian, S.
      (2015). Certifying and removing disparate impact. In Proceedings of the 21th ACM
      SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 259-268).
      Appendix A, Section A.5.

    Args:
        y_pred: Predicted labels
        protected_attribute: Binary protected attribute values (0 or 1)

    Returns:
        Ratio of positive prediction rates (A=1 / A=0)
    """
    # Calculate positive prediction rate for group A=1
    mask_1 = protected_attribute == 1
    rate_1 = np.mean(y_pred[mask_1]) if np.sum(mask_1) > 0 else 0.0

    # Calculate positive prediction rate for group A=0
    mask_0 = protected_attribute == 0
    rate_0 = np.mean(y_pred[mask_0]) if np.sum(mask_0) > 0 else 0.0

    # Avoid division by zero
    if rate_0 == 0:
        return float('inf') if rate_1 > 0 else 1.0

    return rate_1 / rate_0


def false_positive_rate_disparity(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    protected_attribute: np.ndarray
) -> float:
    """
    Calculate the False Positive Rate Disparity.

    This metric measures the absolute difference in false positive rates
    between groups.

    Formula:
    .. math::

        FPR_{diff} = |FPR_1 - FPR_0|

    Where:
    - :math:`FPR_a = P(\\hat{Y}=1 | Y=0, A=a)`

    Citation:
    - Menon, A. K., & Williamson, R. C. (2018). The cost of fairness in
      binary classification. In Conference on Fairness, Accountability and
      Transparency (pp. 107-118). Appendix A, Section A.6.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        protected_attribute: Binary protected attribute values (0 or 1)

    Returns:
        Absolute difference in false positive rates between groups
    """
    # Calculate for group A=1
    mask_1 = protected_attribute == 1
    y_true_1 = y_true[mask_1]
    y_pred_1 = y_pred[mask_1]

    # Calculate for group A=0
    mask_0 = protected_attribute == 0
    y_true_0 = y_true[mask_0]
    y_pred_0 = y_pred[mask_0]

    def calculate_fpr(y_true_group, y_pred_group):
        negative_actual = y_true_group == 0
        if np.sum(negative_actual) == 0:
            return 0.0
        return np.mean(y_pred_group[negative_actual])

    fpr_1 = calculate_fpr(y_true_1, y_pred_1)
    fpr_0 = calculate_fpr(y_true_0, y_pred_0)

    return abs(fpr_1 - fpr_0)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: Optional[np.ndarray] = None,
    protected_attribute: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Calculate all fairness metrics for a given model prediction.

    This function computes all implemented fairness metrics and returns
    them in a dictionary.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_pred_proba: Predicted probabilities (required for calibration)
        protected_attribute: Binary protected attribute values

    Returns:
        Dictionary mapping metric names to their values
    """
    if protected_attribute is None:
        raise ValueError("Protected attribute is required for fairness metrics")

    results = {}

    # Demographic Parity
    results['demographic_parity_difference'] = demographic_parity_difference(
        y_true, y_pred, protected_attribute
    )

    # Equalized Odds
    results['equalized_odds_difference'] = equalized_odds_difference(
        y_true, y_pred, protected_attribute
    )

    # Predictive Parity
    results['predictive_parity'] = predictive_parity(
        y_true, y_pred, protected_attribute
    )

    # Calibration (requires probabilities)
    if y_pred_proba is not None:
        results['calibration_within_groups'] = calibration_within_groups(
            y_true, y_pred_proba, protected_attribute
        )
    else:
        results['calibration_within_groups'] = float('nan')

    # Disparate Impact
    results['disparate_impact_ratio'] = disparate_impact_ratio(
        y_pred, protected_attribute
    )

    # False Positive Rate Disparity
    results['false_positive_rate_disparity'] = false_positive_rate_disparity(
        y_true, y_pred, protected_attribute
    )

    return results