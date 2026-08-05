import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging
from scipy import stats
from code.utils.logger import get_logger

logger = get_logger(__name__)


def mixed_effects_permutation_test(
    auditory_data: np.ndarray,
    visual_data: np.ndarray,
    n_permutations: int = 1000,
    alpha: float = 0.05,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform a mixed-effects permutation test for modality comparison.

    This test assesses whether the source strength differs significantly
    between auditory and visual modalities by permuting labels.

    Args:
        auditory_data: Source strength values for auditory modality (array-like).
        visual_data: Source strength values for visual modality (array-like).
        n_permutations: Number of permutations to perform.
        alpha: Significance level.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - 'statistic': Observed test statistic (t-value)
            - 'p_value': Permutation p-value
            - 'significant': Boolean indicating if p < alpha
            - 'distribution': Array of permuted statistics
    """
    rng = np.random.default_rng(random_state)
    aud = np.asarray(auditory_data)
    vis = np.asarray(visual_data)

    if len(aud) == 0 or len(vis) == 0:
        raise ValueError("Input arrays cannot be empty.")

    # Observed statistic: difference in means
    obs_stat = np.mean(aud) - np.mean(vis)

    # Combine data
    combined = np.concatenate([aud, vis])
    n_aud = len(aud)
    n_total = len(combined)

    perm_stats = np.zeros(n_permutations)

    for i in range(n_permutations):
        # Shuffle indices
        perm_indices = rng.permutation(n_total)
        perm_aud = combined[perm_indices[:n_aud]]
        perm_vis = combined[perm_indices[n_aud:]]
        perm_stats[i] = np.mean(perm_aud) - np.mean(perm_vis)

    # Two-sided p-value
    p_value = (np.sum(np.abs(perm_stats) >= np.abs(obs_stat)) + 1) / (n_permutations + 1)

    result = {
        'statistic': obs_stat,
        'p_value': p_value,
        'significant': p_value < alpha,
        'distribution': perm_stats,
        'n_permutations': n_permutations
    }

    logger.info(f"Permutation test result: t={obs_stat:.4f}, p={p_value:.4f}, significant={result['significant']}")
    return result


def independent_samples_ttest(
    auditory_data: np.ndarray,
    visual_data: np.ndarray,
    equal_var: bool = True
) -> Dict[str, Any]:
    """
    Perform an independent samples t-test for modality comparison.

    Args:
        auditory_data: Source strength values for auditory modality.
        visual_data: Source strength values for visual modality.
        equal_var: If True, perform standard t-test (assume equal variance).
                   If False, perform Welch's t-test.

    Returns:
        Dictionary containing:
            - 'statistic': t-statistic
            - 'p_value': Two-sided p-value
            - 'df': Degrees of freedom
            - 'significant': Boolean indicating if p < 0.05
    """
    aud = np.asarray(auditory_data)
    vis = np.asarray(visual_data)

    if len(aud) < 2 or len(vis) < 2:
        raise ValueError("Each group must have at least 2 samples for t-test.")

    t_stat, p_val = stats.ttest_ind(aud, vis, equal_var=equal_var)

    result = {
        'statistic': t_stat,
        'p_value': p_val,
        'df': len(aud) + len(vis) - 2 if equal_var else "estimated",
        'significant': p_val < 0.05,
        'method': 't-test' if equal_var else "Welch's t-test"
    }

    logger.info(f"Independent t-test result: t={t_stat:.4f}, p={p_val:.4f}, significant={result['significant']}")
    return result


def tost_equivalence_test(
    auditory_data: np.ndarray,
    visual_data: np.ndarray,
    equivalence_margin: float = 0.5,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence.

    Tests the null hypothesis that the difference between means is
    outside the equivalence margin (-delta, delta).

    Args:
        auditory_data: Source strength values for auditory modality.
        visual_data: Source strength values for visual modality.
        equivalence_margin: The equivalence margin (delta).
        alpha: Significance level.

    Returns:
        Dictionary containing:
            - 't_lower': t-statistic for lower bound test
            - 'p_lower': p-value for lower bound test
            - 't_upper': t-statistic for upper bound test
            - 'p_upper': p-value for upper bound test
            - 'equivalent': Boolean indicating if both p < alpha
    """
    aud = np.asarray(auditory_data)
    vis = np.asarray(visual_data)

    if len(aud) < 2 or len(vis) < 2:
        raise ValueError("Each group must have at least 2 samples for TOST.")

    mean_diff = np.mean(aud) - np.mean(vis)
    n1, n2 = len(aud), len(vis)
    var1, var2 = np.var(aud, ddof=1), np.var(vis, ddof=1)
    pooled_se = np.sqrt(var1/n1 + var2/n2)

    # Lower bound test: H0: mean_diff <= -delta
    t_lower = (mean_diff - (-equivalence_margin)) / pooled_se
    # Upper bound test: H0: mean_diff >= delta
    t_upper = (mean_diff - equivalence_margin) / pooled_se

    # One-sided p-values (using t-distribution)
    df = n1 + n2 - 2
    p_lower = 1 - stats.t.cdf(t_lower, df)
    p_upper = stats.t.cdf(t_upper, df)

    # Equivalence is claimed if both one-sided tests reject
    equivalent = (p_lower < alpha) and (p_upper < alpha)

    result = {
        't_lower': t_lower,
        'p_lower': p_lower,
        't_upper': t_upper,
        'p_upper': p_upper,
        'equivalent': equivalent,
        'margin': equivalence_margin,
        'mean_difference': mean_diff
    }

    logger.info(f"TOST result: equivalent={equivalent}, p_lower={p_lower:.4f}, p_upper={p_upper:.4f}")
    return result


def benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).

    This function adjusts p-values for multiple comparisons and determines
    which hypotheses are rejected.

    Args:
        p_values: List of raw p-values from multiple tests.
        alpha: Significance level (FDR threshold).

    Returns:
        Dictionary containing:
            - 'adjusted_p_values': List of BH-adjusted p-values
            - 'rejections': Boolean list indicating which hypotheses are rejected
            - 'n_rejected': Number of rejected hypotheses
            - 'threshold': The effective BH threshold used
    """
    if not p_values:
        logger.warning("Empty list of p-values provided to BH correction.")
        return {
            'adjusted_p_values': [],
            'rejections': [],
            'n_rejected': 0,
            'threshold': 0.0
        }

    p_values = np.asarray(p_values)
    n = len(p_values)
    original_indices = np.argsort(p_values)
    sorted_p = p_values[original_indices]

    # Calculate BH adjusted p-values
    # p_adj[i] = p[i] * n / (i + 1)
    # Ensure monotonicity (cumulative min from the end)
    rank = np.arange(1, n + 1)
    adjusted = sorted_p * n / rank
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0, 1.0)

    # Reorder back to original
    final_adjusted = np.zeros(n)
    final_adjusted[original_indices] = adjusted

    # Determine rejections
    # A hypothesis is rejected if p_adj < alpha
    rejections = final_adjusted < alpha

    # Calculate the effective threshold (max p such that p <= alpha * i / n)
    # This is equivalent to finding the largest k where sorted_p[k] <= alpha * (k+1) / n
    # and rejecting all <= k.
    # However, the standard BH step-up procedure is:
    # Find max k such that p_(k) <= alpha * k / n, reject 1..k.
    # The adjusted p-value method above implements this logic implicitly.
    # Let's explicitly find the threshold for reporting.
    critical_values = alpha * rank / n
    rejected_count = 0
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= critical_values[i]:
            rejected_count = i + 1
            break

    effective_threshold = critical_values[rejected_count - 1] if rejected_count > 0 else 0.0

    result = {
        'adjusted_p_values': final_adjusted.tolist(),
        'rejections': rejections.tolist(),
        'n_rejected': int(np.sum(rejections)),
        'threshold': float(effective_threshold)
    }

    logger.info(f"BH Correction: {result['n_rejected']} of {n} hypotheses rejected at alpha={alpha}")
    return result