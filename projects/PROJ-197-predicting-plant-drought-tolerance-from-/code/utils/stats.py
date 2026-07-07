"""
Statistical utilities for the drought tolerance prediction pipeline.

Implements DeLong's test for comparing paired AUCs and standard statistical helpers.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Optional
import warnings


def delong_test_auc(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_bootstraps: int = 1000
) -> Tuple[float, float, float]:
    """
    Perform DeLong's test to compare two paired AUCs.
    
    This implementation uses a non-parametric approach based on the covariance
    of the AUC estimates. For simplicity and robustness in this context, we
    use a bootstrap approximation which is statistically valid for paired comparisons
    when the exact DeLong covariance matrix is difficult to compute without
    specialized libraries (like `delong` which is not in requirements).
    
    However, to strictly adhere to the task "Implementing DeLong's test", 
    we implement the core logic of the U-statistic variance estimation 
    as described in DeLong et al. (1988).
    
    Parameters
    ----------
    y_true : np.ndarray
        Binary ground truth labels (0 or 1).
    y_pred_a : np.ndarray
        Predicted probabilities for model A.
    y_pred_b : np.ndarray
        Predicted probabilities for model B.
    n_bootstraps : int
        Number of bootstrap iterations for confidence interval estimation 
        (used here to verify the variance calculation if exact DeLong is too complex 
        without external deps, but we will implement the analytical DeLong variance).
        
    Returns
    -------
    z_score : float
        The Z-score of the difference in AUCs.
    p_value : float
        Two-tailed p-value.
    auc_diff : float
        Difference in AUC (AUC_A - AUC_B).
        
    Raises
    ------
    ValueError
        If inputs are not the same length or contain invalid values.
    """
    if len(y_true) != len(y_pred_a) or len(y_true) != len(y_pred_b):
        raise ValueError("Input arrays must have the same length.")
    
    if len(np.unique(y_true)) < 2:
        raise ValueError("y_true must contain both classes (0 and 1).")

    # Calculate AUCs using the trapezoidal rule (equivalent to sklearn's roc_auc_score logic)
    # We implement a simple AUC calculation to avoid dependency on sklearn for this specific utility
    # if possible, but since sklearn is in requirements, we can use it for AUC calc 
    # to ensure accuracy, focusing the custom code on the DeLong variance.
    
    auc_a = _calculate_auc(y_true, y_pred_a)
    auc_b = _calculate_auc(y_true, y_pred_b)
    auc_diff = auc_a - auc_b
    
    if abs(auc_diff) < 1e-10:
        return 0.0, 1.0, 0.0

    # DeLong's Test Implementation
    # The core of DeLong's test is estimating the variance of the difference:
    # Var(AUC_a - AUC_b) = Var(AUC_a) + Var(AUC_b) - 2 * Cov(AUC_a, AUC_b)
    
    # We compute the U-statistic components for each sample
    # For a sample i, let V_a(i) be the contribution to AUC_a
    # Let V_b(i) be the contribution to AUC_b
    
    # Sort indices by score to compute ranks efficiently
    # We need to compute the contribution of each observation to the AUC
    
    # Group indices by true label
    idx_pos = np.where(y_true == 1)[0]
    idx_neg = np.where(y_true == 0)[0]
    
    n_pos = len(idx_pos)
    n_neg = len(idx_neg)
    
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Must have at least one positive and one negative sample.")

    # Compute contributions for Model A
    # For each positive sample, count how many negative samples have lower score
    # This is the Mann-Whitney U statistic formulation
    
    # V_a[i] for positive sample i: proportion of negative samples with score < score_i
    # V_a[i] for negative sample i: proportion of positive samples with score > score_i (adjusted)
    # Actually, DeLong's method uses the average of these contributions.
    
    # Let's compute the vector of "ranks" or contributions for each sample
    # V_a is a vector of length N (total samples)
    
    V_a = np.zeros(len(y_true))
    V_b = np.zeros(len(y_true))
    
    # For positive samples (y=1): contribution is (number of negatives with lower score) / n_neg
    for i in idx_pos:
        score_a = y_pred_a[i]
        count_lower_a = np.sum(y_pred_a[idx_neg] < score_a)
        # Handle ties: add 0.5 * (number of ties)
        ties_a = np.sum(y_pred_a[idx_neg] == score_a)
        V_a[i] = (count_lower_a + 0.5 * ties_a) / n_neg
        
        score_b = y_pred_b[i]
        count_lower_b = np.sum(y_pred_b[idx_neg] < score_b)
        ties_b = np.sum(y_pred_b[idx_neg] == score_b)
        V_b[i] = (count_lower_b + 0.5 * ties_b) / n_neg

    # For negative samples (y=0): contribution is (number of positives with higher score) / n_pos
    # Note: The standard definition for V_i in DeLong is often centered or defined slightly differently
    # to make the expectation equal to AUC.
    # Let's use the formulation where E[V] = AUC.
    # For negative samples, the contribution to AUC is 1 - (proportion of positives with lower score)
    # Wait, the standard DeLong V_i is:
    # If y_i = 1: V_i = (1/n_neg) * sum_{j: y_j=0} I(S_i > S_j)
    # If y_i = 0: V_i = 1 - (1/n_pos) * sum_{j: y_i=1} I(S_j > S_i)  <-- This is not quite right for the variance formula
    
    # Correct DeLong V_i formulation:
    # V_a(i) = 
    #   if y_i=1: (1/n_neg) * sum_{j in neg} I(score_i > score_j)
    #   if y_i=0: 1 - (1/n_pos) * sum_{j in pos} I(score_j > score_i)
    # This V_i has expectation AUC.
    
    # Re-calculate for negative samples
    for i in idx_neg:
        score_a = y_pred_a[i]
        # Count positives with score > score_a
        count_higher_a = np.sum(y_pred_a[idx_pos] > score_a)
        ties_a = np.sum(y_pred_a[idx_pos] == score_a)
        # Contribution: 1 - (count_higher + 0.5*ties)/n_pos
        V_a[i] = 1.0 - (count_higher_a + 0.5 * ties_a) / n_pos
        
        score_b = y_pred_b[i]
        count_higher_b = np.sum(y_pred_b[idx_pos] > score_b)
        ties_b = np.sum(y_pred_b[idx_pos] == score_b)
        V_b[i] = 1.0 - (count_higher_b + 0.5 * ties_b) / n_pos

    # Now we have vectors V_a and V_b of length N.
    # The AUC is the mean of V.
    # The variance of the difference is estimated by the variance of (V_a - V_b) / N?
    # No, the variance of the AUC estimate is Var(V) / N.
    # The covariance between AUC_a and AUC_b is Cov(V_a, V_b) / N.
    
    # Variance of difference:
    # Var(AUC_a - AUC_b) = Var(V_a)/N + Var(V_b)/N - 2*Cov(V_a, V_b)/N
    #                    = (1/N) * [ Var(V_a) + Var(V_b) - 2*Cov(V_a, V_b) ]
    #                    = (1/N) * Var(V_a - V_b)
    
    diff_V = V_a - V_b
    var_diff_V = np.var(diff_V, ddof=1) # Sample variance
    
    if var_diff_V == 0:
        # If variance is zero, the difference is constant (unlikely unless identical predictions)
        if abs(auc_diff) < 1e-9:
            return 0.0, 1.0, auc_diff
        else:
            # Perfect separation with constant difference? Treat as infinite z?
            # This is an edge case, return a large z
            return 10.0, 0.0, auc_diff

    std_err_diff = np.sqrt(var_diff_V / len(y_true))
    
    z_score = auc_diff / std_err_diff
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return z_score, p_value, auc_diff


def _calculate_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate Area Under the ROC Curve using the trapezoidal rule.
    """
    # Sort by scores descending
    desc_score_indices = np.argsort(y_scores)[::-1]
    y_true_sorted = y_true[desc_score_indices]
    y_scores_sorted = y_scores[desc_score_indices]
    
    # Compute TPR and FPR
    # TPR = TP / P
    # FPR = FP / N
    
    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    
    if n_pos == 0 or n_neg == 0:
        return 0.5 # Undefined, return random guess
        
    tpr = np.cumsum(y_true_sorted) / n_pos
    fpr = np.cumsum(1 - y_true_sorted) / n_neg
    
    # Add (0,0) point
    tpr = np.concatenate([[0], tpr])
    fpr = np.concatenate([[0], fpr])
    
    # Trapezoidal rule
    auc = np.trapz(tpr, fpr)
    return float(auc)


def paired_ttest(
    scores_a: np.ndarray,
    scores_b: np.ndarray
) -> Tuple[float, float]:
    """
    Perform a paired t-test on two arrays of scores (e.g., CV scores).
    
    Parameters
    ----------
    scores_a : np.ndarray
        Scores from model A.
    scores_b : np.ndarray
        Scores from model B.
        
    Returns
    -------
    t_stat : float
        The t-statistic.
    p_value : float
        The two-tailed p-value.
    """
    if len(scores_a) != len(scores_b):
        raise ValueError("Input arrays must have the same length.")
    if len(scores_a) < 2:
        raise ValueError("Need at least 2 samples for t-test.")
        
    t_stat, p_value = stats.ttest_rel(scores_a, scores_b)
    return float(t_stat), float(p_value)


def calculate_confidence_interval(
    mean: float,
    std_err: float,
    confidence: float = 0.95,
    n: int = 1
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for a mean.
    
    Parameters
    ----------
    mean : float
        The sample mean.
    std_err : float
        The standard error of the mean.
    confidence : float
        The confidence level (0.95 for 95%).
    n : int
        The sample size.
        
    Returns
    -------
    lower : float
        Lower bound of the CI.
    upper : float
        Upper bound of the CI.
    """
    if n < 2:
        # If n=1, we can't compute a t-distribution based CI
        # Return mean +/- std_err as a rough estimate or raise
        return mean - std_err, mean + std_err
        
    df = n - 1
    t_crit = stats.t.ppf((1 + confidence) / 2, df)
    margin = t_crit * std_err
    return mean - margin, mean + margin