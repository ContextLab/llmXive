import math
import statistics
from typing import List, Tuple, Optional, Union, Iterable
from collections import Counter

def bleu_score(candidate: Union[str, List[str]], references: List[Union[str, List[str]]], max_n: int = 4) -> float:
    """
    Calculate BLEU score for a single candidate against multiple references.
    
    Args:
        candidate: The generated text (string or list of tokens)
        references: List of reference texts (strings or lists of tokens)
        max_n: Maximum n-gram order (default 4)
    
    Returns:
        BLEU score between 0.0 and 1.0
    """
    if isinstance(candidate, str):
        candidate = candidate.split()
    if isinstance(references[0], str):
        references = [ref.split() for ref in references]
    
    if not candidate:
        return 0.0
    
    # Calculate n-gram precisions
    precisions = []
    for n in range(1, max_n + 1):
        # Count n-grams in candidate
        candidate_ngrams = [tuple(candidate[i:i+n]) for i in range(len(candidate) - n + 1)]
        candidate_counts = Counter(candidate_ngrams)
        
        # Get maximum count for each n-gram across references
        max_counts = Counter()
        for ref in references:
            ref_ngrams = [tuple(ref[i:i+n]) for i in range(len(ref) - n + 1)]
            ref_counts = Counter(ref_ngrams)
            for ngram, count in ref_counts.items():
                max_counts[ngram] = max(max_counts[ngram], count)
        
        # Calculate clipped count
        clipped_count = sum(min(candidate_counts[ngram], max_counts[ngram]) for ngram in candidate_counts)
        total_count = sum(candidate_counts.values())
        
        if total_count == 0:
            precisions.append(0.0)
        else:
            precisions.append(clipped_count / total_count)
    
    # Check for brevity penalty
    candidate_len = len(candidate)
    ref_lens = [len(ref) for ref in references]
    closest_ref_len = min(ref_lens, key=lambda x: abs(x - candidate_len))
    
    if candidate_len > closest_ref_len:
        bp = 1.0
    else:
        if candidate_len == 0:
            bp = 0.0
        else:
            bp = math.exp(1 - closest_ref_len / candidate_len)
    
    # Calculate geometric mean of precisions
    if 0.0 in precisions:
        return 0.0
    
    log_precision = sum(math.log(p) for p in precisions) / len(precisions)
    bleu = bp * math.exp(log_precision)
    
    return bleu

def f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score from precision and recall.
    
    Args:
        precision: Precision value (0.0 to 1.0)
        recall: Recall value (0.0 to 1.0)
    
    Returns:
        F1 score between 0.0 and 1.0
    """
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

def compute_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values
        group2: Second group of values
    
    Returns:
        Cohen's d value
    """
    if not group1 or not group2:
        return 0.0
    
    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)
    
    var1 = statistics.variance(group1) if len(group1) > 1 else 0
    var2 = statistics.variance(group2) if len(group2) > 1 else 0
    
    # Pooled standard deviation
    n1 = len(group1)
    n2 = len(group2)
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two lists.
    
    Args:
        x: First list of values
        y: Second list of values
    
    Returns:
        Pearson correlation coefficient between -1 and 1
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
    sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)
    
    denominator = math.sqrt(sum_sq_x * sum_sq_y)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def t_test_independent(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Perform independent two-sample t-test.
    
    Args:
        group1: First group of values
        group2: Second group of values
    
    Returns:
        Tuple of (t-statistic, p-value)
    """
    if not group1 or not group2:
        return 0.0, 1.0
    
    n1 = len(group1)
    n2 = len(group2)
    
    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)
    
    var1 = statistics.variance(group1) if n1 > 1 else 0
    var2 = statistics.variance(group2) if n2 > 1 else 0
    
    # Pooled variance
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    
    if pooled_var == 0:
        return 0.0, 1.0
    
    # Standard error
    se = math.sqrt(pooled_var * (1/n1 + 1/n2))
    
    if se == 0:
        return 0.0, 1.0
    
    # t-statistic
    t_stat = (mean1 - mean2) / se
    
    # Degrees of freedom
    df = n1 + n2 - 2
    
    # Approximate p-value using t-distribution (two-tailed)
    # Using a simple approximation for the t-distribution CDF
    # For a more accurate calculation, scipy would be needed
    # This is a simplified approximation
    abs_t = abs(t_stat)
    
    # Approximation for p-value (not exact, but sufficient for demonstration)
    # In production, use scipy.stats.t.sf(abs(t_stat), df) * 2
    if df > 30:
        # Use normal approximation for large df
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs_t / math.sqrt(2))))
    else:
        # Rough approximation for small df
        p_value = max(0.001, 2 * (1 - 0.5 * (1 + math.erf(abs_t / math.sqrt(2 * (1 + 1/df))))))
    
    return t_stat, p_value

def ancova(
    dependent: List[float],
    independent: List[str],
    covariates: List[List[float]],
    covariate_names: List[str]
) -> dict:
    """
    Perform one-way ANCOVA analysis.
    
    Args:
        dependent: Dependent variable values
        independent: Independent variable (group labels)
        covariates: List of covariate value lists (one per covariate)
        covariate_names: Names of the covariates
    
    Returns:
        Dictionary containing ANCOVA results
    """
    if len(dependent) != len(independent):
        raise ValueError("Dependent and independent variables must have same length")
    
    if covariates and len(covariates[0]) != len(dependent):
        raise ValueError("Covariates must have same length as dependent variable")
    
    # Group data
    groups = {}
    for i, group in enumerate(independent):
        if group not in groups:
            groups[group] = {'y': [], 'covariates': [[] for _ in range(len(covariates))]}
        groups[group]['y'].append(dependent[i])
        for j, cov in enumerate(covariates):
            groups[group]['covariates'][j].append(cov[i])
    
    # Calculate overall means
    overall_mean_y = statistics.mean(dependent)
    overall_means_cov = [statistics.mean(cov) for cov in covariates] if covariates else []
    
    # Calculate total sum of squares
    ss_total = sum((y - overall_mean_y) ** 2 for y in dependent)
    
    # Calculate within-group sum of squares (residuals after adjusting for covariates)
    # This is a simplified implementation - a full ANCOVA would require matrix operations
    # For a proper implementation, we would use statsmodels or scipy
    
    # Calculate group means
    group_means = {g: statistics.mean(data['y']) for g, data in groups.items()}
    
    # Calculate adjusted means (simplified)
    adjusted_means = {}
    for g, data in groups.items():
        adj_mean = group_means[g]
        for j, cov in enumerate(covariates):
            cov_group_mean = statistics.mean(data['covariates'][j])
            cov_overall_mean = overall_means_cov[j]
            # Simple adjustment (in reality, this requires regression coefficients)
            adj_mean -= (cov_group_mean - cov_overall_mean) * 0.5  # Placeholder slope
        adjusted_means[g] = adj_mean
    
    # Calculate between-group sum of squares (adjusted)
    ss_between = sum(
        len(data['y']) * (adjusted_means[g] - overall_mean_y) ** 2
        for g, data in groups.items()
    )
    
    # Calculate within-group sum of squares
    ss_within = ss_total - ss_between
    
    # Degrees of freedom
    k = len(groups)  # Number of groups
    n = len(dependent)  # Total sample size
    c = len(covariates)  # Number of covariates
    
    df_between = k - 1
    df_within = n - k - c
    df_total = n - 1
    
    # Mean squares
    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0
    
    # F-statistic
    f_stat = ms_between / ms_within if ms_within > 0 else 0
    
    # Approximate p-value
    if f_stat > 0 and df_within > 0:
        # Simplified p-value calculation
        p_value = max(0.001, 2 * (1 - 0.5 * (1 + math.erf(math.sqrt(f_stat) / math.sqrt(2)))))
    else:
        p_value = 1.0
    
    # Effect size (eta-squared)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0
    
    return {
        'f_statistic': f_stat,
        'p_value': p_value,
        'df_between': df_between,
        'df_within': df_within,
        'ss_between': ss_between,
        'ss_within': ss_within,
        'eta_squared': eta_squared,
        'group_means': group_means,
        'adjusted_means': adjusted_means,
        'covariate_names': covariate_names,
        'overall_mean_y': overall_mean_y,
        'overall_means_cov': overall_means_cov
    }
