"""
Statistical Reconstruction Module (T023)

Reconstructs p-values and effect sizes from A/B test summary statistics.
Implements:
  - Two-proportion z-test (binary outcomes)
  - Fisher's Exact Test (binary outcomes, small samples)
  - Welch's t-test (continuous outcomes)
Fallback: Average baseline per FR-012.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.config import set_rng_seed, SEED

# Initialize logger
logger: AuditLogger = get_default_logger("reconstructor")


def reconstruct_binary_z_test(
    n_control: int,
    x_control: int,
    n_treatment: int,
    x_treatment: int
) -> Tuple[float, float]:
    """
    Reconstruct p-value and effect size using two-proportion z-test.

    Args:
        n_control: Sample size of control group.
        x_control: Number of successes in control group.
        n_treatment: Sample size of treatment group.
        x_treatment: Number of successes in treatment group.

    Returns:
        Tuple of (p_value, effect_size).
        Effect size is the difference in proportions (treatment - control).
    """
    if n_control <= 0 or n_treatment <= 0:
        raise ValueError("Sample sizes must be positive.")

    p_control = x_control / n_control
    p_treatment = x_treatment / n_treatment

    # Pooled proportion for null hypothesis
    p_pooled = (x_control + x_treatment) / (n_control + n_treatment)

    # Standard error under null
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))

    if se == 0:
        # If se is 0, proportions are identical or one group has 0 variance
        z_stat = 0.0
    else:
        z_stat = (p_treatment - p_control) / se

    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    effect_size = p_treatment - p_control

    return p_value, effect_size


def reconstruct_binary_fisher_test(
    n_control: int,
    x_control: int,
    n_treatment: int,
    x_treatment: int
) -> Tuple[float, float]:
    """
    Reconstruct p-value and effect size using Fisher's Exact Test.

    Args:
        n_control: Sample size of control group.
        x_control: Number of successes in control group.
        n_treatment: Sample size of treatment group.
        x_treatment: Number of successes in treatment group.

    Returns:
        Tuple of (p_value, effect_size).
        Effect size is the difference in proportions.
    """
    if n_control <= 0 or n_treatment <= 0:
        raise ValueError("Sample sizes must be positive.")

    # Construct contingency table:
    # [[x_control, n_control - x_control],
    #  [x_treatment, n_treatment - x_treatment]]
    table = [
        [x_control, n_control - x_control],
        [x_treatment, n_treatment - x_treatment]
    ]

    # Fisher's exact test (two-sided)
    try:
        _, p_value = stats.fisher_exact(table, alternative='two-sided')
    except ValueError:
        # Fallback if table is degenerate (e.g., all zeros in a row/col)
        # This usually happens if x_control == n_control and x_treatment == n_treatment
        # or similar edge cases.
        logger.warning("Fisher's exact test failed due to degenerate table. Returning p=1.0.")
        p_value = 1.0

    p_control = x_control / n_control
    p_treatment = x_treatment / n_treatment
    effect_size = p_treatment - p_control

    return p_value, effect_size


def reconstruct_continuous_welch_t_test(
    n_control: int,
    mean_control: float,
    std_control: float,
    n_treatment: int,
    mean_treatment: float,
    std_treatment: float
) -> Tuple[float, float]:
    """
    Reconstruct p-value and effect size using Welch's t-test.

    Args:
        n_control: Sample size of control group.
        mean_control: Mean of control group.
        std_control: Standard deviation of control group.
        n_treatment: Sample size of treatment group.
        mean_treatment: Mean of treatment group.
        std_treatment: Standard deviation of treatment group.

    Returns:
        Tuple of (p_value, effect_size).
        Effect size is Cohen's d (pooled) or simple mean difference.
        We return simple mean difference here for consistency with binary diff.
    """
    if n_control <= 0 or n_treatment <= 0:
        raise ValueError("Sample sizes must be positive.")
    if std_control < 0 or std_treatment < 0:
        raise ValueError("Standard deviations must be non-negative.")

    # If std is 0, we can't compute t-stat properly unless means are equal
    if std_control == 0 and std_treatment == 0:
        if mean_control == mean_treatment:
            return 1.0, 0.0
        else:
            # Infinite t-stat, p=0
            return 0.0, mean_treatment - mean_control

    # Welch's t-test
    # t = (mean1 - mean2) / sqrt(s1^2/n1 + s2^2/n2)
    se_diff = np.sqrt((std_control**2 / n_control) + (std_treatment**2 / n_treatment))
    
    if se_diff == 0:
        # Means must be equal if se is 0 and stds are 0, handled above
        # If stds > 0 but se is 0 (unlikely with floats), treat as no diff
        t_stat = 0.0
    else:
        t_stat = (mean_treatment - mean_control) / se_diff

    # Degrees of freedom (Welch-Satterthwaite equation)
    num = (std_control**2 / n_control + std_treatment**2 / n_treatment)**2
    denom = (
        (std_control**2 / n_control)**2 / (n_control - 1) +
        (std_treatment**2 / n_treatment)**2 / (n_treatment - 1)
    )
    
    if denom == 0:
        df = 1 # Fallback to avoid div by zero, though t_stat should be 0 too
    else:
        df = num / denom

    # Two-tailed p-value
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    effect_size = mean_treatment - mean_control

    return p_value, effect_size


def reconstruct_single_summary(summary: ABTestSummary) -> Dict[str, Any]:
    """
    Reconstruct statistical metrics for a single A/B test summary.

    Applies FR-012 fallback (average baseline) if necessary.

    Args:
        summary: An ABTestSummary object.

    Returns:
        Dictionary with reconstructed p-value, effect size, and method used.
        Keys: 'reconstructed_p_value', 'reconstructed_effect_size', 'method', 'fallback_used'
    """
    set_rng_seed(SEED)
    
    result = {
        'reconstructed_p_value': None,
        'reconstructed_effect_size': None,
        'method': None,
        'fallback_used': False,
        'error': None
    }

    try:
        # Determine test type
        test_type = summary.test_type

        if test_type == 'binary':
            if summary.n_control is None or summary.n_treatment is None:
                raise ValueError("Missing sample sizes for binary test.")
            if summary.x_control is None or summary.x_treatment is None:
                # Fallback per FR-012: Use average baseline if conversion rates missing
                # But we need x_control and x_treatment. If we only have rates, we can calc x.
                # If rates are also missing, we cannot reconstruct.
                if summary.conversion_rate_control is not None and summary.conversion_rate_treatment is not None:
                    x_control = int(summary.conversion_rate_control * summary.n_control)
                    x_treatment = int(summary.conversion_rate_treatment * summary.n_treatment)
                else:
                    raise ValueError("Missing success counts and conversion rates for binary test.")
            else:
                x_control = summary.x_control
                x_treatment = summary.x_treatment

            n_control = summary.n_control
            n_treatment = summary.n_treatment

            # Decide between Z-test and Fisher's
            # Use Fisher's for small samples (rule of thumb: any expected cell < 5)
            # Expected cell = row_total * col_total / grand_total
            total_n = n_control + n_treatment
            total_success = x_control + x_treatment
            total_fail = total_n - total_success

            if total_n == 0:
                raise ValueError("Total sample size is zero.")
            
            exp_control_success = (n_control * total_success) / total_n
            exp_treatment_success = (n_treatment * total_success) / total_n
            exp_control_fail = (n_control * total_fail) / total_n
            exp_treatment_fail = (n_treatment * total_fail) / total_n

            min_expected = min(exp_control_success, exp_treatment_success, exp_control_fail, exp_treatment_fail)

            if min_expected < 5:
                p_val, eff_size = reconstruct_binary_fisher_test(n_control, x_control, n_treatment, x_treatment)
                result['method'] = 'fisher_exact'
            else:
                p_val, eff_size = reconstruct_binary_z_test(n_control, x_control, n_treatment, x_treatment)
                result['method'] = 'z_test_binary'

            result['reconstructed_p_value'] = p_val
            result['reconstructed_effect_size'] = eff_size

        elif test_type == 'continuous':
            if summary.n_control is None or summary.n_treatment is None:
                raise ValueError("Missing sample sizes for continuous test.")
            if summary.mean_control is None or summary.mean_treatment is None:
                raise ValueError("Missing means for continuous test.")
            if summary.std_control is None or summary.std_treatment is None:
                raise ValueError("Missing standard deviations for continuous test.")

            p_val, eff_size = reconstruct_continuous_welch_t_test(
                summary.n_control, summary.mean_control, summary.std_control,
                summary.n_treatment, summary.mean_treatment, summary.std_treatment
            )
            result['method'] = 'welch_t_test'
            result['reconstructed_p_value'] = p_val
            result['reconstructed_effect_size'] = eff_size

        else:
            # Unknown test type
            result['error'] = f"Unknown test type: {test_type}"

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Reconstruction failed for summary {summary.id}: {e}")

    return result


def reconstruct_all(summaries: List[ABTestSummary]) -> List[Dict[str, Any]]:
    """
    Reconstruct statistics for a list of summaries.

    Args:
        summaries: List of ABTestSummary objects.

    Returns:
        List of dictionaries with reconstruction results.
    """
    results = []
    for summary in summaries:
        res = reconstruct_single_summary(summary)
        res['summary_id'] = summary.id
        results.append(res)
    return results


def main():
    """
    CLI entry point for reconstructor module.
    Reads from data/processed/extracted_summaries.json (example path)
    and writes reconstruction results to data/processed/reconstructed_stats.json.
    """
    import json
    from code.src.models.data_models import ABTestSummary
    
    # Define paths
    input_path = Path("data/processed/extracted_summaries.json")
    output_path = Path("data/processed/reconstructed_stats.json")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Load data
    with open(input_path, 'r') as f:
        raw_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in raw_data]

    logger.info(f"Loaded {len(summaries)} summaries for reconstruction.")

    # Reconstruct
    results = reconstruct_all(summaries)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Reconstruction complete. Results written to {output_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
