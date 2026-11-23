import numpy as np
import pandas as pd
import scipy.stats as stats
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from analysis.logging import get_effect_sizes_logger

logger = get_effect_sizes_logger()


@dataclass
class PairwiseComparison:
    """Represents a single pairwise comparison result."""
    group1: str
    group2: str
    mean_diff: float
    cohens_d: float
    p_value: float
    p_value_adjusted: float
    significant: bool
    stratum: str
    n1: int
    n2: int


@dataclass
class EffectSizeResult:
    """Container for effect size analysis results."""
    comparisons: List[Dict[str, Any]]
    correction_method: str
    alpha: float
    n_tests: int
    significant_count: int
    family_wise_error_rate: float
    raw_p_values: List[float]
    adjusted_p_values: List[float]


def calculate_cohens_d(
    group1_data: np.ndarray,
    group2_data: np.ndarray,
    pooled_std: Optional[float] = None
) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d effect size for two independent groups.

    Args:
        group1_data: Array of values for group 1.
        group2_data: Array of values for group 2.
        pooled_std: Optional pre-calculated pooled standard deviation.

    Returns:
        Tuple of (cohens_d, mean_diff, pooled_std).
    """
    mean1 = np.mean(group1_data)
    mean2 = np.mean(group2_data)
    mean_diff = mean1 - mean2

    n1 = len(group1_data)
    n2 = len(group2_data)

    if pooled_std is None:
        var1 = np.var(group1_data, ddof=1)
        var2 = np.var(group2_data, ddof=1)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Cohen's d undefined.")
        return 0.0, mean_diff, 0.0

    cohens_d = mean_diff / pooled_std

    logger.debug(
        f"Cohen's d calculated: d={cohens_d:.4f}, "
        f"mean_diff={mean_diff:.4f}, pooled_std={pooled_std:.4f}"
    )

    return cohens_d, mean_diff, pooled_std


def calculate_paired_cohens_d(
    pre_data: np.ndarray,
    post_data: np.ndarray
) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d for paired samples (e.g., pre/post test).

    Args:
        pre_data: Array of pre-intervention values.
        post_data: Array of post-intervention values.

    Returns:
        Tuple of (cohens_d, mean_diff, std_diff).
    """
    if len(pre_data) != len(post_data):
        raise ValueError("Pre and post data must have the same length for paired calculation.")

    diff = pre_data - post_data
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)

    if std_diff == 0:
        logger.warning("Standard deviation of differences is zero. Cohen's d undefined.")
        return 0.0, mean_diff, 0.0

    # For paired data, Cohen's d is often calculated as mean_diff / std_diff
    cohens_d = mean_diff / std_diff

    logger.debug(
        f"Paired Cohen's d calculated: d={cohens_d:.4f}, "
        f"mean_diff={mean_diff:.4f}, std_diff={std_diff:.4f}"
    )

    return cohens_d, mean_diff, std_diff


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, float, bool]]:
    """
    Apply Bonferroni correction to a list of p-values.

    The Bonferroni correction adjusts the significance threshold by dividing alpha
    by the number of tests (m). Alternatively, p-values can be multiplied by m
    and compared to alpha.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).

    Returns:
        List of tuples (raw_p, adjusted_p, significant) for each test.
    """
    m = len(p_values)
    if m == 0:
        return []

    # Adjusted alpha threshold
    adjusted_alpha = alpha / m

    results = []
    for p in p_values:
        # Adjusted p-value (capped at 1.0)
        adjusted_p = min(p * m, 1.0)
        significant = adjusted_p < alpha
        results.append((p, adjusted_p, significant))
        logger.debug(f"Bonferroni: raw={p:.4f}, adj={adjusted_p:.4f}, sig={significant}")

    return results


def holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, float, bool]]:
    """
    Apply Holm-Bonferroni correction (step-down method) to a list of p-values.

    This method is more powerful than standard Bonferroni while still controlling
    the family-wise error rate. It sequentially tests the smallest p-value against
    alpha/m, the second smallest against alpha/(m-1), etc.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).

    Returns:
        List of tuples (raw_p, adjusted_p, significant) for each test.
    """
    m = len(p_values)
    if m == 0:
        return []

    # Create indexed list to track original positions
    indexed_p = list(enumerate(p_values))
    # Sort by p-value
    sorted_p = sorted(indexed_p, key=lambda x: x[1])

    # Calculate adjusted p-values using step-down method
    adjusted_p_values = [0.0] * m
    is_significant = [True] * m

    # Track the maximum adjusted p-value seen so far (monotonicity constraint)
    max_adj_p = 0.0

    for i, (orig_idx, p_val) in enumerate(sorted_p):
        # Holm's adjusted p-value: p * (m - i)
        # But we must ensure monotonicity: adj_p[i] >= adj_p[i-1]
        current_adj_p = p_val * (m - i)
        # Ensure monotonicity
        adjusted_p_values[orig_idx] = max(current_adj_p, max_adj_p)
        # Cap at 1.0
        adjusted_p_values[orig_idx] = min(adjusted_p_values[orig_idx], 1.0)

        # Update max for next iteration
        max_adj_p = adjusted_p_values[orig_idx]

        # Determine significance based on step-down logic
        # A test is significant only if all previous (smaller) p-values were significant
        # against their respective thresholds
        threshold = alpha / (m - i)
        if p_val >= threshold:
            is_significant[orig_idx] = False
            # Once one fails, all subsequent (larger) ones also fail in step-down
            # But we've already calculated adjusted p-values, so we just mark this one
            # Actually, in step-down, we stop as soon as we find a non-significant one.
            # The adjusted p-value approach handles this naturally: if p_val >= threshold,
            # then adjusted_p >= alpha, so it's not significant.

    results = []
    for i in range(m):
        p = p_values[i]
        adj_p = adjusted_p_values[i]
        sig = adj_p < alpha
        results.append((p, adj_p, sig))
        logger.debug(f"Holm-Bonferroni: raw={p:.4f}, adj={adj_p:.4f}, sig={sig}")

    return results


def perform_pairwise_comparisons_by_stratum(
    df: pd.DataFrame,
    outcome_var: str,
    group_var: str,
    stratum_var: str,
    alpha: float = 0.05,
    correction_method: str = 'holm'
) -> EffectSizeResult:
    """
    Perform pairwise comparisons of group means within each stratum,
    calculate Cohen's d, and apply multiple comparison correction.

    Args:
        df: Input DataFrame.
        outcome_var: Name of the outcome variable (e.g., 'task_time').
        group_var: Name of the grouping variable (e.g., 'tool_usage').
        stratum_var: Name of the stratification variable (e.g., 'experience_level').
        alpha: Significance level (default 0.05).
        correction_method: 'bonferroni' or 'holm' (default 'holm').

    Returns:
        EffectSizeResult object containing all comparisons and correction details.
    """
    comparisons = []
    raw_p_values = []
    stratum_groups = df[stratum_var].unique()

    logger.info(f"Starting pairwise comparisons by stratum for {outcome_var}")

    for stratum in stratum_groups:
        stratum_df = df[df[stratum_var] == stratum]
        groups = stratum_df[group_var].unique()

        if len(groups) < 2:
            logger.warning(f"Not enough groups in stratum {stratum} for pairwise comparison")
            continue

        # Perform all pairwise combinations within this stratum
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                g1, g2 = groups[i], groups[j]
                data1 = stratum_df[stratum_df[group_var] == g1][outcome_var].values
                data2 = stratum_df[stratum_df[group_var] == g2][outcome_var].values

                if len(data1) == 0 or len(data2) == 0:
                    continue

                # Calculate Cohen's d
                cohens_d, mean_diff, pooled_std = calculate_cohens_d(data1, data2)

                # Perform t-test for p-value
                # Using Welch's t-test by default (unequal variances)
                t_stat, p_val = stats.ttest_ind(data1, data2, equal_var=False)

                comparison = PairwiseComparison(
                    group1=g1,
                    group2=g2,
                    mean_diff=mean_diff,
                    cohens_d=cohens_d,
                    p_value=p_val,
                    p_value_adjusted=p_val,  # Will be updated after correction
                    significant=False,  # Will be updated after correction
                    stratum=stratum,
                    n1=len(data1),
                    n2=len(data2)
                )
                comparisons.append(asdict(comparison))
                raw_p_values.append(p_val)

    # Apply multiple comparison correction
    n_tests = len(raw_p_values)
    if n_tests == 0:
        logger.warning("No comparisons performed. Returning empty result.")
        return EffectSizeResult(
            comparisons=[],
            correction_method=correction_method,
            alpha=alpha,
            n_tests=0,
            significant_count=0,
            family_wise_error_rate=alpha,
            raw_p_values=[],
            adjusted_p_values=[]
        )

    if correction_method.lower() == 'bonferroni':
        corrected_results = bonferroni_correction(raw_p_values, alpha)
    elif correction_method.lower() in ['holm', 'holm-bonferroni']:
        corrected_results = holm_bonferroni_correction(raw_p_values, alpha)
    else:
        logger.error(f"Unknown correction method: {correction_method}. Defaulting to Holm.")
        corrected_results = holm_bonferroni_correction(raw_p_values, alpha)

    # Update comparisons with adjusted values
    significant_count = 0
    for idx, (raw_p, adj_p, sig) in enumerate(corrected_results):
        comparisons[idx]['p_value_adjusted'] = adj_p
        comparisons[idx]['significant'] = sig
        if sig:
            significant_count += 1

    logger.info(
        f"Pairwise comparisons complete: {n_tests} tests, "
        f"{significant_count} significant at alpha={alpha} ({correction_method})"
    )

    return EffectSizeResult(
        comparisons=comparisons,
        correction_method=correction_method,
        alpha=alpha,
        n_tests=n_tests,
        significant_count=significant_count,
        family_wise_error_rate=alpha,
        raw_p_values=raw_p_values,
        adjusted_p_values=[x[1] for x in corrected_results]
    )


def verify_paired_output(result: EffectSizeResult) -> bool:
    """
    Verify that effect sizes are reported alongside p-values.
    Implements Constitution Principle VI (paired output).

    Args:
        result: EffectSizeResult object to verify.

    Returns:
        True if all comparisons have both effect size and p-value.
    """
    for comp in result.comparisons:
        if 'cohens_d' not in comp or comp['cohens_d'] is None:
            logger.error(f"Missing Cohen's d in comparison: {comp}")
            return False
        if 'p_value' not in comp or comp['p_value'] is None:
            logger.error(f"Missing p-value in comparison: {comp}")
            return False
        if 'p_value_adjusted' not in comp:
            logger.error(f"Missing adjusted p-value in comparison: {comp}")
            return False

    logger.debug("Paired output verification passed: all comparisons have effect sizes and p-values.")
    return True


def run_effect_size_pipeline(
    data_path: str,
    outcome_var: str = 'task_time',
    group_var: str = 'tool_usage',
    stratum_var: str = 'experience_level',
    alpha: float = 0.05,
    correction_method: str = 'holm',
    output_path: Optional[str] = None
) -> EffectSizeResult:
    """
    Run the complete effect size analysis pipeline.

    Args:
        data_path: Path to the CSV file containing the data.
        outcome_var: Name of the outcome variable.
        group_var: Name of the grouping variable.
        stratum_var: Name of the stratification variable.
        alpha: Significance level.
        correction_method: Correction method ('bonferroni' or 'holm').
        output_path: Optional path to save results as JSON.

    Returns:
        EffectSizeResult object.
    """
    logger.info(f"Running effect size pipeline from {data_path}")

    df = pd.read_csv(data_path)

    # Ensure stratum variable is categorical for consistent ordering
    df[stratum_var] = df[stratum_var].astype(str)

    result = perform_pairwise_comparisons_by_stratum(
        df, outcome_var, group_var, stratum_var, alpha, correction_method
    )

    # Verify paired output
    if not verify_paired_output(result):
        logger.error("Paired output verification failed!")
        # Continue anyway but log the error

    # Save results if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        result_dict = {
            'correction_method': result.correction_method,
            'alpha': result.alpha,
            'n_tests': result.n_tests,
            'significant_count': result.significant_count,
            'family_wise_error_rate': result.family_wise_error_rate,
            'comparisons': result.comparisons
        }

        import json
        with open(output_file, 'w') as f:
            json.dump(result_dict, f, indent=2)

        logger.info(f"Results saved to {output_path}")

    return result


def main():
    """Main entry point for effect size analysis."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Calculate effect sizes with multiple comparison correction')
    parser.add_argument('--data', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--outcome', type=str, default='task_time', help='Outcome variable name')
    parser.add_argument('--group', type=str, default='tool_usage', help='Grouping variable name')
    parser.add_argument('--stratum', type=str, default='experience_level', help='Stratification variable name')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--correction', type=str, default='holm', choices=['bonferroni', 'holm'],
                        help='Multiple comparison correction method')
    parser.add_argument('--output', type=str, help='Output JSON file path')

    args = parser.parse_args()

    try:
        result = run_effect_size_pipeline(
            data_path=args.data,
            outcome_var=args.outcome,
            group_var=args.group,
            stratum_var=args.stratum,
            alpha=args.alpha,
            correction_method=args.correction,
            output_path=args.output
        )

        print(f"Analysis complete. {result.n_tests} comparisons performed.")
        print(f"Significant findings: {result.significant_count} ({result.correction_method} correction)")

        if args.output:
            print(f"Results written to: {args.output}")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
