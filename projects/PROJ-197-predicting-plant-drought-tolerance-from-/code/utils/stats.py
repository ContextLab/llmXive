"""
Statistical utilities for the drought tolerance prediction pipeline.

Implements DeLong's test for comparing paired AUCs and standard statistical
utilities such as paired t-tests and confidence interval calculations.
"""
import numpy as np
from scipy import stats
from typing import Tuple, List, Optional
import warnings

def delong_test_auc(
    y_true: np.ndarray,
    y_pred_model1: np.ndarray,
    y_pred_model2: np.ndarray
) -> Tuple[float, float, float]:
    """
    Perform DeLong's test to compare two paired AUCs.
    
    This function computes the AUC for two models on the same set of true labels
    and performs DeLong's test to determine if the difference in AUCs is statistically
    significant.
    
    Parameters
    ----------
    y_true : np.ndarray
        Binary true labels (0 or 1).
    y_pred_model1 : np.ndarray
        Predicted probabilities (or scores) for model 1.
    y_pred_model2 : np.ndarray
        Predicted probabilities (or scores) for model 2.
        
    Returns
    -------
    tuple
        A tuple containing:
        - auc1 : float, AUC for model 1
        - auc2 : float, AUC for model 2
        - p_value : float, two-sided p-value from DeLong's test
        
    Raises
    ------
    ValueError
        If input arrays have different lengths or are not binary for y_true.
    """
    if len(y_true) != len(y_pred_model1) or len(y_true) != len(y_pred_model2):
        raise ValueError("All input arrays must have the same length.")
    
    if not np.all(np.isin(y_true, [0, 1])):
        raise ValueError("y_true must contain only 0s and 1s.")
        
    n = len(y_true)
    if n < 2:
        raise ValueError("Need at least 2 samples to compute AUC.")
        
    # Calculate AUCs using the Mann-Whitney U statistic approach
    # AUC = P(score_positive > score_negative)
    
    # For model 1
    pos_indices_1 = np.where(y_true == 1)[0]
    neg_indices_1 = np.where(y_true == 0)[0]
    
    if len(pos_indices_1) == 0 or len(neg_indices_1) == 0:
        raise ValueError("Must have at least one positive and one negative sample.")
        
    # Calculate V values for DeLong's test
    # V_i1 = P(S1_i > S1_j | y_i=1, y_j=0) - AUC1
    # V_i2 = P(S2_i > S2_j | y_i=1, y_j=0) - AUC2
    
    # We'll compute the empirical estimates of these values
    
    # Sort predictions for model 1
    sorted_indices_1 = np.argsort(y_pred_model1)
    sorted_y_true_1 = y_true[sorted_indices_1]
    sorted_pred_1 = y_pred_model1[sorted_indices_1]
    
    # Calculate AUC1 using the trapezoidal rule on the ROC curve
    # Or more simply, using the Mann-Whitney U statistic
    auc1 = _calculate_auc_mann_whitney(y_true, y_pred_model1)
    
    # Similarly for model 2
    auc2 = _calculate_auc_mann_whitney(y_true, y_pred_model2)
    
    # DeLong's test implementation
    # We need to compute the covariance matrix of the AUC estimates
    
    # Get V values for each observation
    v1 = _get_delong_v_values(y_true, y_pred_model1)
    v2 = _get_delong_v_values(y_true, y_pred_model2)
    
    # Calculate the variance of the difference
    # Var(AUC1 - AUC2) = Var(V1) + Var(V2) - 2*Cov(V1, V2)
    
    # Group by true label
    pos_mask = y_true == 1
    neg_mask = y_true == 0
    
    n_pos = np.sum(pos_mask)
    n_neg = np.sum(neg_mask)
    
    # Calculate V values for positive and negative classes separately
    v1_pos = v1[pos_mask]
    v1_neg = v1[neg_mask]
    v2_pos = v2[pos_mask]
    v2_neg = v2[neg_mask]
    
    # For positive class
    s11 = np.var(v1_pos, ddof=1) if n_pos > 1 else 0
    s12 = np.var(v2_pos, ddof=1) if n_pos > 1 else 0
    s11_2 = np.cov(v1_pos, v2_pos, ddof=1)[0, 1] if n_pos > 1 else 0
    
    # For negative class
    s21 = np.var(v1_neg, ddof=1) if n_neg > 1 else 0
    s22 = np.var(v2_neg, ddof=1) if n_neg > 1 else 0
    s21_2 = np.cov(v1_neg, v2_neg, ddof=1)[0, 1] if n_neg > 1 else 0
    
    # Variance of the difference
    var_diff = (s11 + s12 - 2 * s11_2) / n_pos + (s21 + s22 - 2 * s21_2) / n_neg
    
    if var_diff <= 0:
        # If variance is zero or negative, we can't compute a z-score
        # This happens if both models have identical predictions
        if abs(auc1 - auc2) < 1e-10:
            p_value = 1.0
        else:
            # Very small variance, treat as significant if difference exists
            p_value = 0.0
    else:
        z_score = (auc1 - auc2) / np.sqrt(var_diff)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return auc1, auc2, p_value

def _calculate_auc_mann_whitney(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate AUC using the Mann-Whitney U statistic.
    
    AUC = P(score_positive > score_negative)
    """
    pos_scores = y_scores[y_true == 1]
    neg_scores = y_scores[y_true == 0]
    
    if len(pos_scores) == 0 or len(neg_scores) == 0:
        return 0.5
        
    # Count pairs where positive score > negative score
    # Add 0.5 for ties
    count = 0
    for pos_score in pos_scores:
        count += np.sum(neg_scores < pos_score)
        count += 0.5 * np.sum(neg_scores == pos_score)
        
    auc = count / (len(pos_scores) * len(neg_scores))
    return auc

def _get_delong_v_values(y_true: np.ndarray, y_scores: np.ndarray) -> np.ndarray:
    """
    Calculate V values for DeLong's test.
    
    V_i = P(S_i > S_j | y_i, y_j) - AUC
    where the probability is over all pairs (i, j) with y_i != y_j
    """
    n = len(y_true)
    v_values = np.zeros(n)
    
    # Get AUC first
    auc = _calculate_auc_mann_whitney(y_true, y_scores)
    
    pos_indices = np.where(y_true == 1)[0]
    neg_indices = np.where(y_true == 0)[0]
    
    # For each positive sample, calculate how many negative samples it beats
    for i in pos_indices:
        score_i = y_scores[i]
        # Count negative samples with lower score
        count_lower = np.sum(y_scores[neg_indices] < score_i)
        count_equal = np.sum(y_scores[neg_indices] == score_i)
        v_values[i] = (count_lower + 0.5 * count_equal) / len(neg_indices) - auc
        
    # For each negative sample, calculate how many positive samples it loses to
    for i in neg_indices:
        score_i = y_scores[i]
        # Count positive samples with higher score
        count_higher = np.sum(y_scores[pos_indices] > score_i)
        count_equal = np.sum(y_scores[pos_indices] == score_i)
        v_values[i] = - (count_higher + 0.5 * count_equal) / len(pos_indices) - auc
        
    return v_values

def paired_ttest(
    scores1: np.ndarray,
    scores2: np.ndarray,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Perform a paired t-test on two sets of scores.
    
    Parameters
    ----------
    scores1 : np.ndarray
        First set of scores (e.g., AUCs from k-fold CV).
    scores2 : np.ndarray
        Second set of scores.
    alternative : str, optional
        Alternative hypothesis: 'two-sided', 'greater', or 'less'.
        
    Returns
    -------
    tuple
        A tuple containing:
        - t_statistic : float, the t-statistic
        - p_value : float, the p-value
    """
    if len(scores1) != len(scores2):
        raise ValueError("Both score arrays must have the same length.")
        
    if len(scores1) < 2:
        raise ValueError("Need at least 2 samples to perform a t-test.")
        
    t_stat, p_value = stats.ttest_rel(scores1, scores2, alternative=alternative)
    
    return t_stat, p_value

def calculate_confidence_interval(
    values: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for a set of values.
    
    Parameters
    ----------
    values : np.ndarray
        Array of values.
    confidence : float, optional
        Confidence level (default: 0.95 for 95% CI).
        
    Returns
    -------
    tuple
        A tuple containing:
        - lower_bound : float, lower bound of the CI
        - upper_bound : float, upper bound of the CI
    """
    if len(values) < 2:
        raise ValueError("Need at least 2 values to calculate confidence interval.")
        
    mean = np.mean(values)
    std_err = stats.sem(values)
    
    # Use t-distribution for small samples
    n = len(values)
    df = n - 1
    t_value = stats.t.ppf((1 + confidence) / 2, df)
    
    margin = t_value * std_err
    
    lower_bound = mean - margin
    upper_bound = mean + margin
    
    return lower_bound, upper_bound

def calculate_roc_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate the ROC AUC score.
    
    Parameters
    ----------
    y_true : np.ndarray
        Binary true labels.
    y_scores : np.ndarray
        Predicted probabilities or scores.
        
    Returns
    -------
    float
        ROC AUC score.
    """
    return _calculate_auc_mann_whitney(y_true, y_scores)

def calculate_precision_recall_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """
    Calculate the Precision-Recall AUC score.
    
    Parameters
    ----------
    y_true : np.ndarray
        Binary true labels.
    y_scores : np.ndarray
        Predicted probabilities or scores.
        
    Returns
    -------
    float
        PR AUC score.
    """
    # Sort by scores descending
    sorted_indices = np.argsort(y_scores)[::-1]
    y_true_sorted = y_true[sorted_indices]
    
    # Calculate precision and recall at each threshold
    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    
    if n_pos == 0 or n_neg == 0:
        return 0.5
        
    tp = np.cumsum(y_true_sorted)
    fp = np.cumsum(1 - y_true_sorted)
    
    precision = tp / (tp + fp)
    recall = tp / n_pos
    
    # Calculate PR AUC using trapezoidal rule
    # Sort by recall
    sort_indices = np.argsort(recall)
    recall_sorted = recall[sort_indices]
    precision_sorted = precision[sort_indices]
    
    # Ensure recall is monotonically increasing
    for i in range(1, len(recall_sorted)):
        precision_sorted[i] = max(precision_sorted[i], precision_sorted[i-1])
        
    # Trapezoidal integration
    pr_auc = np.trapz(precision_sorted, recall_sorted)
    
    return pr_auc

def bootstrap_confidence_interval(
    values: np.ndarray,
    statistic: callable = np.mean,
    confidence: float = 0.95,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for a statistic.
    
    Parameters
    ----------
    values : np.ndarray
        Array of values.
    statistic : callable, optional
        Function to calculate the statistic (default: np.mean).
    confidence : float, optional
        Confidence level (default: 0.95).
    n_bootstrap : int, optional
        Number of bootstrap samples (default: 1000).
    random_state : int, optional
        Random seed for reproducibility.
        
    Returns
    -------
    tuple
        A tuple containing:
        - lower_bound : float, lower bound of the CI
        - upper_bound : float, upper bound of the CI
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    n = len(values)
    bootstrap_stats = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(values, size=n, replace=True)
        bootstrap_stats.append(statistic(sample))
        
    bootstrap_stats = np.array(bootstrap_stats)
    
    alpha = 1 - confidence
    lower_bound = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper_bound = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
    
    return lower_bound, upper_bound