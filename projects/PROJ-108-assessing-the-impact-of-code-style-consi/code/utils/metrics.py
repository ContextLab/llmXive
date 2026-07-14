"""
Metrics utility functions for statistical analysis and code evaluation.

This module provides helper functions for calculating common metrics used
in the code style consistency research pipeline, including BLEU scores,
F1 scores, effect sizes, and statistical tests.
"""

import math
import statistics
from typing import List, Tuple, Optional, Union, Iterable
from collections import Counter


def bleu_score(
    candidate: Union[str, List[str]],
    references: Union[List[str], List[List[str]]],
    n_gram: int = 4
) -> float:
    """
    Calculate BLEU score for a candidate text against one or more references.

    Args:
        candidate: The generated text (string or list of tokens).
        references: List of reference texts (strings or lists of tokens).
        n_gram: Maximum n-gram order to consider (default 4).

    Returns:
        BLEU score between 0.0 and 1.0. Returns 0.0 if candidate is empty.
    """
    if not candidate:
        return 0.0

    if isinstance(candidate, str):
        candidate = candidate.split()
    if isinstance(references[0], str):
        references = [ref.split() for ref in references]

    if not candidate:
        return 0.0

    # Calculate precision for each n-gram order
    precisions = []
    for n in range(1, n_gram + 1):
        candidate_ngrams = Counter(tuple(candidate[i:i + n]) for i in range(len(candidate) - n + 1))
        reference_ngrams = [Counter(tuple(ref[i:i + n]) for i in range(len(ref) - n + 1)) for ref in references]

        # Count clipped matches
        clipped_count = 0
        total_count = sum(candidate_ngrams.values())

        if total_count == 0:
            precisions.append(0.0)
            continue

        for ngram, count in candidate_ngrams.items():
            max_ref_count = max((ref_counts.get(ngram, 0) for ref_counts in reference_ngrams), default=0)
            clipped_count += min(count, max_ref_count)

        precision = clipped_count / total_count if total_count > 0 else 0.0
        precisions.append(precision)

    # Calculate brevity penalty
    ref_lengths = [len(ref) for ref in references]
    closest_ref_len = min(ref_lengths, key=lambda r: abs(r - len(candidate)))
    candidate_len = len(candidate)

    if candidate_len > closest_ref_len:
        brevity_penalty = 1.0
    else:
        brevity_penalty = math.exp(1 - closest_ref_len / candidate_len) if closest_ref_len > 0 else 0.0

    # Calculate geometric mean of precisions
    if all(p > 0 for p in precisions):
        log_precision = sum(math.log(p) for p in precisions) / len(precisions)
        bleu = math.exp(log_precision)
    else:
        bleu = 0.0

    return min(brevity_penalty * bleu, 1.0)


def f1_score(
    precision: float,
    recall: float
) -> float:
    """
    Calculate F1 score from precision and recall.

    Args:
        precision: Precision value (0.0 to 1.0).
        recall: Recall value (0.0 to 1.0).

    Returns:
        F1 score (harmonic mean of precision and recall). Returns 0.0 if
        both precision and recall are 0.0.
    """
    if precision == 0.0 and recall == 0.0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def compute_cohen_d(
    group1: List[Union[int, float]],
    group2: List[Union[int, float]]
) -> float:
    """
    Calculate Cohen's d effect size for two independent groups.

    Args:
        group1: First group of numerical values.
        group2: Second group of numerical values.

    Returns:
        Cohen's d effect size. Positive values indicate group1 > group2.
    """
    if not group1 or not group2:
        return 0.0

    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)

    var1 = statistics.variance(group1) if len(group1) > 1 else 0.0
    var2 = statistics.variance(group2) if len(group2) > 1 else 0.0

    n1 = len(group1)
    n2 = len(group2)

    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = math.sqrt(pooled_var) if pooled_var > 0 else 0.0

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std


def pearson_correlation(
    x: List[Union[int, float]],
    y: List[Union[int, float]]
) -> float:
    """
    Calculate Pearson correlation coefficient between two variables.

    Args:
        x: First variable (list of numerical values).
        y: Second variable (list of numerical values).

    Returns:
        Pearson correlation coefficient between -1.0 and 1.0.
        Returns 0.0 if either list is empty or has only one element.
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


def t_test_independent(
    group1: List[Union[int, float]],
    group2: List[Union[int, float]]
) -> Tuple[float, float]:
    """
    Perform independent two-sample t-test.

    Args:
        group1: First group of numerical values.
        group2: Second group of numerical values.

    Returns:
        Tuple of (t-statistic, p-value). Returns (0.0, 1.0) if
        either group is empty or has insufficient data.
    """
    if not group1 or not group2 or len(group1) < 2 or len(group2) < 2:
        return 0.0, 1.0

    n1 = len(group1)
    n2 = len(group2)

    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)

    var1 = statistics.variance(group1)
    var2 = statistics.variance(group2)

    # Pooled standard error
    se = math.sqrt(var1 / n1 + var2 / n2)

    if se == 0:
        return 0.0, 1.0

    t_stat = (mean1 - mean2) / se

    # Approximate p-value using t-distribution (degrees of freedom)
    # Using Welch-Satterthwaite equation for degrees of freedom
    df_num = (var1 / n1 + var2 / n2) ** 2
    df_den = ((var1 / n1) ** 2 / (n1 - 1)) + ((var2 / n2) ** 2 / (n2 - 1))

    df = df_num / df_den if df_den > 0 else n1 + n2 - 2

    # Approximate p-value (two-tailed)
    # Using a simple approximation for the t-distribution CDF
    # For a more accurate implementation, scipy.stats would be preferred
    # but we avoid external dependencies beyond standard library
    abs_t = abs(t_stat)

    # Simple approximation: for large df, t approaches normal
    # This is a rough approximation for demonstration
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs_t / math.sqrt(2))))

    # Clamp p-value to [0, 1]
    p_value = max(0.0, min(1.0, p_value))

    return t_stat, p_value


def ancova(
    dependent: List[Union[int, float]],
    independent: List[str],
    covariate: List[Union[int, float]]
) -> Dict[str, Union[float, str]]:
    """
    Perform one-way ANCOVA (Analysis of Covariance).

    Args:
        dependent: Dependent variable values.
        independent: Independent variable (group labels).
        covariate: Covariate values (control variable).

    Returns:
        Dictionary containing F-statistic, p-value, and covariate coefficient.
        Returns {'F': 0.0, 'p': 1.0, 'covariate_coef': 0.0} if data is insufficient.
    """
    if len(dependent) < 3 or len(set(independent)) < 2:
        return {'F': 0.0, 'p': 1.0, 'covariate_coef': 0.0}

    # Group the data
    groups = {}
    for i, group in enumerate(independent):
        if group not in groups:
            groups[group] = {'y': [], 'x': []}
        groups[group]['y'].append(dependent[i])
        groups[group]['x'].append(covariate[i])

    # Calculate overall means
    mean_y = statistics.mean(dependent)
    mean_x = statistics.mean(covariate)

    # Calculate total sum of squares
    ss_total = sum((y - mean_y) ** 2 for y in dependent)

    # Calculate within-group sum of squares (adjusted for covariate)
    ss_within = 0.0
    ss_covariate = 0.0

    for group_data in groups.values():
        group_y = group_data['y']
        group_x = group_data['x']

        if len(group_y) < 2:
            continue

        mean_group_y = statistics.mean(group_y)
        mean_group_x = statistics.mean(group_x)

        # Calculate regression slope for this group
        if len(group_x) > 1:
            cov_xy = sum((group_x[i] - mean_group_x) * (group_y[i] - mean_group_y) for i in range(len(group_x)))
            var_x = sum((xi - mean_group_x) ** 2 for xi in group_x)

            if var_x > 0:
                slope = cov_xy / var_x
                ss_residual = sum((group_y[i] - mean_group_y - slope * (group_x[i] - mean_group_x)) ** 2
                                 for i in range(len(group_x)))
                ss_within += ss_residual
            else:
                ss_within += sum((y - mean_group_y) ** 2 for y in group_y)
        else:
            ss_within += sum((y - mean_group_y) ** 2 for y in group_y)

    # Calculate between-group sum of squares (adjusted)
    ss_between = ss_total - ss_within

    # Degrees of freedom
    k = len(groups)
    n = len(dependent)

    df_between = k - 1
    df_within = n - k - 1  # Adjusted for covariate
    df_covariate = 1

    if df_within <= 0:
        return {'F': 0.0, 'p': 1.0, 'covariate_coef': 0.0}

    # Mean squares
    ms_between = ss_between / df_between if df_between > 0 else 0.0
    ms_within = ss_within / df_within if df_within > 0 else 0.0

    # F-statistic
    if ms_within == 0:
        f_stat = 0.0
    else:
        f_stat = ms_between / ms_within

    # Approximate p-value (same approximation as t-test)
    abs_f = abs(f_stat)
    p_value = 1.0 / (1 + abs_f)  # Very rough approximation

    # Calculate covariate coefficient (pooled slope)
    total_cov_xy = 0.0
    total_var_x = 0.0

    for group_data in groups.values():
        group_y = group_data['y']
        group_x = group_data['x']
        mean_group_y = statistics.mean(group_y)
        mean_group_x = statistics.mean(group_x)

        cov_xy = sum((group_x[i] - mean_group_x) * (group_y[i] - mean_group_y) for i in range(len(group_x)))
        var_x = sum((xi - mean_group_x) ** 2 for xi in group_x)

        total_cov_xy += cov_xy
        total_var_x += var_x

    covariate_coef = total_cov_xy / total_var_x if total_var_x > 0 else 0.0

    return {
        'F': f_stat,
        'p': max(0.0, min(1.0, p_value)),
        'covariate_coef': covariate_coef
    }
