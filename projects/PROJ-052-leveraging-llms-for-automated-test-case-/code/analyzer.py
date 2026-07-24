"""
code/analyzer.py

Statistical analysis utilities for the LLM test generation pipeline.
Implements hypothesis testing (Shapiro-Wilk, Wilcoxon, t-test) and power analysis
as required by User Story 3 (US3) and FR-008.
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats

from config import get_sample_limit


def check_normality(sample: np.ndarray) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality on the given sample.

    Args:
        sample: 1D numpy array of coverage differences (LLM - Baseline).

    Returns:
        Tuple of (is_normal, p_value).
        is_normal is True if p_value >= 0.05 (fail to reject null hypothesis of normality).
    """
    if len(sample) < 3:
        # Shapiro-Wilk requires at least 3 samples
        return False, 0.0

    stat, p_value = stats.shapiro(sample)
    is_normal = p_value >= 0.05
    return is_normal, p_value


def run_statistical_test(group_a: np.ndarray, group_b: np.ndarray) -> Dict[str, Any]:
    """
    Select and run the appropriate paired statistical test based on normality.

    Per FR-008:
    - If normality holds (p >= 0.05), run paired t-test.
    - Else, run Wilcoxon signed-rank test.

    Args:
        group_a: 1D numpy array (e.g., LLM coverage).
        group_b: 1D numpy array (e.g., Manual baseline coverage).

    Returns:
        Dictionary containing:
            - 'test_type': str ('t-test' or 'wilcoxon')
            - 'statistic': float
            - 'p_value': float
            - 'is_significant': bool (p < 0.05)
            - 'method_description': str
    """
    if len(group_a) != len(group_b) or len(group_a) < 2:
        raise ValueError("Both groups must have equal length >= 2 for paired test.")

    # Check normality of differences
    differences = group_a - group_b
    is_normal, p_normal = check_normality(differences)

    result = {
        'test_type': None,
        'statistic': None,
        'p_value': None,
        'is_significant': False,
        'method_description': None,
        'normality_check': {
            'is_normal': is_normal,
            'p_value': p_normal
        }
    }

    if is_normal:
        # Paired t-test
        stat, p_value = stats.ttest_rel(group_a, group_b)
        result['test_type'] = 'paired_t-test'
        result['method_description'] = "Data passed normality test (Shapiro-Wilk p >= 0.05). Using paired t-test."
    else:
        # Wilcoxon signed-rank test
        stat, p_value = stats.wilcoxon(group_a, group_b)
        result['test_type'] = 'wilcoxon_signed_rank'
        result['method_description'] = "Data failed normality test (Shapiro-Wilk p < 0.05). Using Wilcoxon signed-rank test."

    result['statistic'] = float(stat)
    result['p_value'] = float(p_value)
    result['is_significant'] = result['p_value'] < 0.05

    return result


def calculate_effect_size(group_a: np.ndarray, group_b: np.ndarray, test_type: str) -> Dict[str, float]:
    """
    Calculate effect size based on the test type used.

    - For t-test: Cohen's d (paired)
    - For Wilcoxon: Rank-biserial correlation

    Args:
        group_a: 1D numpy array.
        group_b: 1D numpy array.
        test_type: String indicating which test was used ('paired_t-test' or 'wilcoxon_signed_rank').

    Returns:
        Dictionary with 'effect_size' and 'interpretation'.
    """
    if len(group_a) != len(group_b) or len(group_a) < 2:
        raise ValueError("Both groups must have equal length >= 2.")

    differences = group_a - group_b

    if test_type == 'paired_t-test':
        # Cohen's d for paired samples
        # d = mean(diff) / std(diff)
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        
        if std_diff == 0:
            d = 0.0
        else:
            d = mean_diff / std_diff
        
        interpretation = interpret_cohen_d(abs(d))
        return {'effect_size': float(d), 'metric': 'cohen_d', 'interpretation': interpretation}

    elif test_type == 'wilcoxon_signed_rank':
        # Rank-biserial correlation for Wilcoxon
        # r = Z / sqrt(N)
        # We need to re-run wilcoxon to get Z if not provided, or approximate.
        # scipy.stats.wilcoxon does not return Z directly in all versions, 
        # but we can use the statistic to approximate or use statsmodels if available.
        # However, a common approximation for rank-biserial is:
        # r = 1 - (2 * W) / (n * (n + 1)) where W is the smaller sum of ranks?
        # Or use the Z-score from the normal approximation if n is large.
        
        # Let's use the normal approximation Z-score for large n (n > 20 usually)
        # scipy.stats.wilcoxon returns (statistic, pvalue).
        # We need Z. We can compute it manually or use stats.ranksums if independent (not paired).
        # For paired, we can use the formula: Z = (W - 0.5 * n * (n + 1)) / sqrt(n * (n + 1) * (2 * n + 1) / 6)
        # where W is the sum of signed ranks? No, Wilcoxon statistic is usually sum of positive ranks.
        
        # Alternative: Use the p-value to back-calculate Z? No, loses sign.
        # Let's implement the Z calculation for Wilcoxon signed-rank.
        n = len(differences)
        # Calculate signed ranks
        abs_diffs = np.abs(differences)
        # Handle zeros by dropping them
        non_zero_mask = abs_diffs > 0
        abs_diffs = abs_diffs[non_zero_mask]
        signs = np.sign(differences[non_zero_mask])
        
        if len(abs_diffs) == 0:
            return {'effect_size': 0.0, 'metric': 'rank_biserial', 'interpretation': 'No difference'}

        ranks = stats.rankdata(abs_diffs)
        W_plus = np.sum(ranks[signs == 1])
        W_minus = np.sum(ranks[signs == -1])
        W = min(W_plus, W_minus) # Statistic used by scipy usually
        
        # Mean and SD of W under null
        mean_W = n * (n + 1) / 4
        sd_W = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        
        if sd_W == 0:
            z = 0.0
        else:
            # Continuity correction
            if W_plus > W_minus:
                z = (W_minus - mean_W + 0.5) / sd_W
            else:
                z = (W_plus - mean_W - 0.5) / sd_W
        
        r = z / np.sqrt(n)
        interpretation = interpret_rank_biserial(abs(r))
        return {'effect_size': float(r), 'metric': 'rank_biserial', 'interpretation': interpretation}

    else:
        raise ValueError(f"Unknown test type: {test_type}")


def interpret_cohen_d(d: float) -> str:
    """Interpret Cohen's d effect size."""
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"


def interpret_rank_biserial(r: float) -> str:
    """Interpret Rank-biserial correlation effect size."""
    if r < 0.1:
        return "negligible"
    elif r < 0.3:
        return "small"
    elif r < 0.5:
        return "medium"
    else:
        return "large"


def run_power_analysis(effect_size: float, alpha: float = 0.05, power_target: float = 0.80) -> Dict[str, Any]:
    """
    Calculate required sample size and achieved power for a paired t-test.
    
    Note: This is descriptive only, not used for validation (FR-009).
    
    Args:
        effect_size: Cohen's d.
        alpha: Significance level.
        power_target: Target power (0.80).
        
    Returns:
        Dictionary with 'required_n', 'achieved_power' (if n is known), 'notes'.
    """
    # Using statsmodels is ideal, but to avoid extra deps not in requirements.txt,
    # we use a simplified approximation or raise a warning if statsmodels is missing.
    # However, the requirements.txt listed in T002 does NOT include statsmodels.
    # We must implement a basic approximation or rely on scipy if possible.
    # scipy.stats does not have power analysis.
    # We will implement a basic approximation for paired t-test sample size:
    # n = 2 * ((Z_alpha + Z_beta) / d)^2 (for independent) -> for paired, it's similar but d is standardized mean diff.
    # Actually, for paired: n = ((Z_alpha/2 + Z_beta) / d)^2 * 2? 
    # Standard formula: n = ( (Z_alpha + Z_beta) / d )^2 * 2 is for independent.
    # For paired, variance is reduced. The formula n = ( (Z_alpha + Z_beta) / d )^2 is often cited for paired if d is defined on the difference.
    # Let's use the standard approximation: n = ( (1.96 + 0.84) / d )^2 for 80% power, 5% alpha.
    
    try:
        from scipy.stats import norm
    except ImportError:
        # Fallback to hardcoded Z values if scipy.stats.norm is somehow missing (unlikely)
        Z_alpha = 1.96
        Z_beta = 0.84
    else:
        Z_alpha = norm.ppf(1 - alpha/2)
        Z_beta = norm.ppf(power_target)
    
    if effect_size == 0:
        return {
            'required_n': float('inf'),
            'achieved_power': 0.0,
            'notes': "Effect size is zero; infinite sample size required to detect difference."
        }

    # Approximation for paired t-test sample size
    # n = ( (Z_alpha + Z_beta) / d )^2
    n_req = ((Z_alpha + Z_beta) / effect_size) ** 2
    
    return {
        'required_n': int(np.ceil(n_req)),
        'achieved_power': None, # Requires actual N to calculate
        'notes': f"Estimated required N for power={power_target}, alpha={alpha}, d={effect_size:.3f}."
    }


def calculate_confidence_interval(group_a: np.ndarray, group_b: np.ndarray, confidence: float = 0.95) -> Dict[str, float]:
    """
    Calculate 95% confidence interval for the mean difference.
    
    Args:
        group_a, group_b: Arrays of equal length.
        confidence: Confidence level (default 0.95).
        
    Returns:
        Dictionary with 'mean_diff', 'ci_lower', 'ci_upper'.
    """
    if len(group_a) != len(group_b) or len(group_a) < 2:
        raise ValueError("Both groups must have equal length >= 2.")
        
    differences = group_a - group_b
    mean_diff = np.mean(differences)
    sem = stats.sem(differences)
    
    try:
        from scipy.stats import norm
    except ImportError:
        # Fallback to t-distribution if norm is missing? No, sem uses t if n is small.
        # stats.sem uses t-distribution by default if ddof is set?
        # Let's use t.interval which is robust for small n.
        pass
        
    ci = stats.t.interval(confidence, len(differences)-1, loc=mean_diff, scale=sem)
    
    return {
        'mean_diff': float(mean_diff),
        'ci_lower': float(ci[0]),
        'ci_upper': float(ci[1]),
        'confidence_level': confidence
    }