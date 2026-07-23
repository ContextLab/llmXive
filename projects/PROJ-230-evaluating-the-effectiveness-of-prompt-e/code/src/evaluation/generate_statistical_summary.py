import os
import sys
import csv
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path if running as script
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(code_root))

from src.evaluation.statistical_analysis import (
    load_quality_metrics,
    load_correctness_results,
    chi_square_test,
    anova_test,
    bonferroni_correction
)
from src.utils.logging import get_logger

def calculate_effect_size_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size for two groups.
    d = (mean1 - mean2) / pooled_std
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0

    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2

    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1) if n2 > 1 else 0

    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = math.sqrt(pooled_var)

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std

def calculate_confidence_interval(
    mean: float,
    std: float,
    n: int,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for a mean.
    CI = mean ± (t * (std / sqrt(n)))
    Using z=1.96 for 95% confidence as approximation for large n.
    """
    if n <= 1:
        return (mean, mean)

    # Approximation for t-distribution with large n (z-score)
    # For 95% confidence, z ≈ 1.96
    z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99% is 2.576

    margin_of_error = z_score * (std / math.sqrt(n))
    return (mean - margin_of_error, mean + margin_of_error)

def generate_statistical_summary(
    quality_metrics_path: str,
    correctness_results_path: str,
    output_path: str
) -> None:
    """
    Generate the final statistical summary CSV.

    Reads quality metrics (complexity) and correctness results (pass/fail),
    performs statistical tests, and computes effect sizes and confidence intervals.
    Outputs a CSV with:
    - prompt_condition
    - p_value
    - confidence_interval (lower, upper)
    - effect_size
    - metric_type (correctness or complexity)
    """
    logger = get_logger(__name__)
    logger.info(f"Generating statistical summary from {quality_metrics_path} and {correctness_results_path}")

    # Load data
    quality_data = load_quality_metrics(quality_metrics_path)
    correctness_data = load_correctness_results(correctness_results_path)

    if not quality_data or not correctness_data:
        logger.error("No data loaded. Cannot generate summary.")
        raise ValueError("Data loading failed. Check input files.")

    # Organize data by condition
    conditions = sorted(set(quality_data.keys()))
    summary_rows = []

    # 1. Correctness Analysis (Binary: pass/fail)
    # Chi-square test for independence
    # Effect size: Phi coefficient or Cramer's V for contingency tables
    logger.info("Analyzing correctness metrics...")

    # Prepare correctness data by condition
    correctness_by_condition = {}
    for condition in conditions:
        if condition in correctness_data:
            # Count passes and total
            passes = sum(1 for item in correctness_data[condition] if item.get('passed', False))
            total = len(correctness_data[condition])
            correctness_by_condition[condition] = {'passes': passes, 'total': total}

    # Perform Chi-square test across all conditions
    # We need a contingency table: conditions x (pass, fail)
    contingency_table = []
    condition_labels = []
    for condition in conditions:
        if condition in correctness_by_condition:
            data = correctness_by_condition[condition]
            fails = data['total'] - data['passes']
            contingency_table.append([data['passes'], fails])
            condition_labels.append(condition)

    if len(contingency_table) >= 2:
        chi2_stat, p_val_correctness, dof_correctness, _ = chi_square_test(contingency_table)
        logger.info(f"Chi-square test for correctness: chi2={chi2_stat:.4f}, p={p_val_correctness:.4f}")

        # Calculate effect size (Phi coefficient for 2x2, Cramer's V for larger)
        # Phi = sqrt(chi2 / N)
        total_n = sum(sum(row) for row in contingency_table)
        if total_n > 0:
            effect_size_correctness = math.sqrt(chi2_stat / total_n)
        else:
            effect_size_correctness = 0.0

        # Confidence interval for proportion difference (approximate)
        # We'll report the overall p-value and effect size for the omnibus test
        # For pairwise, we'd need post-hoc tests
        ci_lower, ci_upper = 0.0, 0.0  # Placeholder for omnibus test

        for condition in conditions:
            if condition in correctness_by_condition:
                data = correctness_by_condition[condition]
                prop = data['passes'] / data['total'] if data['total'] > 0 else 0.0
                # Standard error for proportion
                se = math.sqrt(prop * (1 - prop) / data['total']) if data['total'] > 1 else 0.0
                ci_lower, ci_upper = calculate_confidence_interval(prop, se, data['total'])

                summary_rows.append({
                    'prompt_condition': condition,
                    'metric_type': 'correctness',
                    'p_value': p_val_correctness,
                    'confidence_interval': f"[{ci_lower:.4f}, {ci_upper:.4f}]",
                    'effect_size': effect_size_correctness,
                    'statistic': f"chi2={chi2_stat:.4f}"
                })
    else:
        logger.warning("Not enough conditions for Chi-square test.")

    # 2. Complexity Analysis (Continuous: complexity scores)
    # ANOVA test for means across groups
    logger.info("Analyzing complexity metrics...")

    # Prepare complexity data by condition
    complexity_by_condition = {}
    for condition in conditions:
        if condition in quality_data:
            # Extract complexity scores
            scores = [item.get('complexity', 0.0) for item in quality_data[condition] if 'complexity' in item]
            complexity_by_condition[condition] = scores

    # Perform ANOVA
    groups = [complexity_by_condition[c] for c in conditions if c in complexity_by_condition]
    if len(groups) >= 2 and all(len(g) > 0 for g in groups):
        f_stat, p_val_complexity = anova_test(groups)
        logger.info(f"ANOVA test for complexity: F={f_stat:.4f}, p={p_val_complexity:.4f}")

        # Bonferroni correction for multiple comparisons
        # If we have k groups, we have k*(k-1)/2 pairwise comparisons
        num_comparisons = len(conditions) * (len(conditions) - 1) // 2
        alpha = 0.05
        corrected_alpha = alpha / num_comparisons if num_comparisons > 0 else alpha
        logger.info(f"Bonferroni corrected alpha: {corrected_alpha:.4f}")

        # Calculate effect size (Eta-squared)
        # eta^2 = SS_between / SS_total
        # Approximate using group means and overall mean
        all_scores = [s for group in groups for s in group]
        overall_mean = sum(all_scores) / len(all_scores)

        ss_between = 0.0
        ss_within = 0.0
        n_total = 0

        for i, condition in enumerate(conditions):
            if condition in complexity_by_condition:
                group_scores = complexity_by_condition[condition]
                n_group = len(group_scores)
                n_total += n_group
                group_mean = sum(group_scores) / n_group
                ss_between += n_group * (group_mean - overall_mean) ** 2
                ss_within += sum((s - group_mean) ** 2 for s in group_scores)

        ss_total = ss_between + ss_within
        eta_squared = ss_between / ss_total if ss_total > 0 else 0.0

        # Cohen's f = sqrt(eta^2 / (1 - eta^2))
        effect_size_complexity = math.sqrt(eta_squared / (1 - eta_squared)) if (1 - eta_squared) > 0 else 0.0

        for condition in conditions:
            if condition in complexity_by_condition:
                scores = complexity_by_condition[condition]
                n = len(scores)
                mean_complexity = sum(scores) / n if n > 0 else 0.0
                std_complexity = math.sqrt(sum((x - mean_complexity) ** 2 for x in scores) / (n - 1)) if n > 1 else 0.0

                ci_lower, ci_upper = calculate_confidence_interval(mean_complexity, std_complexity, n)

                summary_rows.append({
                    'prompt_condition': condition,
                    'metric_type': 'complexity',
                    'p_value': p_val_complexity,
                    'confidence_interval': f"[{ci_lower:.4f}, {ci_upper:.4f}]",
                    'effect_size': effect_size_complexity,
                    'statistic': f"F={f_stat:.4f}"
                })
    else:
        logger.warning("Not enough data for ANOVA test.")

    # Write summary CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['prompt_condition', 'metric_type', 'p_value', 'confidence_interval', 'effect_size', 'statistic']

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    logger.info(f"Statistical summary written to {output_path}")

def main():
    """Main entry point for generating the statistical summary."""
    logger = get_logger(__name__)
    logger.info("Starting statistical summary generation...")

    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    quality_metrics_path = project_root / "data" / "evaluation" / "quality_metrics.csv"
    correctness_results_path = project_root / "data" / "evaluation" / "correctness_results.csv"
    output_path = project_root / "data" / "evaluation" / "statistical_summary.csv"

    if not quality_metrics_path.exists():
        logger.error(f"Quality metrics file not found: {quality_metrics_path}")
        sys.exit(1)

    if not correctness_results_path.exists():
        logger.error(f"Correctness results file not found: {correctness_results_path}")
        sys.exit(1)

    try:
        generate_statistical_summary(
            str(quality_metrics_path),
            str(correctness_results_path),
            str(output_path)
        )
        logger.info("Statistical summary generation completed successfully.")
    except Exception as e:
        logger.error(f"Error generating statistical summary: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()