"""
ANOVA analysis module for Social Memory Networks.

Implements Two-Way Independent-Samples ANOVA with Bonferroni correction
for family-wise error rate control.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Optional statsmodels import
try:
    import statsmodels.api as sm
    from statsmodels.stats.anova import AnovaRM
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    AnovaRM = None  # type: ignore


@dataclass
class ANOVAOutput:
    """Container for ANOVA results including Bonferroni-corrected values."""
    source: str
    df: float
    sum_sq: float
    mean_sq: float
    F: float
    p_value: float
    p_value_bonferroni: float
    corrected_alpha: float
    significance: str

@dataclass
class ANOVAFullResult:
    """Complete ANOVA analysis result."""
    interaction_p_value: float
    interaction_p_bonferroni: float
    main_effect_context_p: float
    main_effect_context_p_bonferroni: float
    main_effect_metric_p: float
    main_effect_metric_p_bonferroni: float
    corrected_alpha: float
    significant_interaction: bool
    significant_context: bool
    significant_metric: bool
    bonferroni_factor: int
    raw_p_values: Dict[str, float]
    bonferroni_p_values: Dict[str, float]
    effect_sizes: Dict[str, float]
    summary_text: str

def safe_import_statsmodels() -> bool:
    """Check if statsmodels is available."""
    return STATSMODELS_AVAILABLE

def load_experiment_results(
    full_path: Union[str, Path],
    limited_path: Union[str, Path]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load experiment results from CSV files.

    Args:
        full_path: Path to results_full.csv
        limited_path: Path to results_limited.csv

    Returns:
        Tuple of (full_results, limited_results) as lists of dicts
    """
    full_results = []
    limited_results = []

    # Load full context results
    full_path = Path(full_path)
    if full_path.exists():
        with open(full_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                full_results.append({
                    'game_id': int(row['game_id']),
                    'specialization_index': float(row['specialization_index']),
                    'retrieval_efficiency': float(row['retrieval_efficiency']),
                    'context_condition': row['context_condition'],
                    'agent_count': int(row['agent_count'])
                })

    # Load limited context results
    limited_path = Path(limited_path)
    if limited_path.exists():
        with open(limited_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                limited_results.append({
                    'game_id': int(row['game_id']),
                    'specialization_index': float(row['specialization_index']),
                    'retrieval_efficiency': float(row['retrieval_efficiency']),
                    'context_condition': row['context_condition'],
                    'agent_count': int(row['agent_count'])
                })

    return full_results, limited_results

def prepare_data_for_anova(
    full_results: List[Dict[str, Any]],
    limited_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Prepare data in long format for ANOVA analysis.

    Transforms wide format (one row per game with two metrics) to
    long format (two rows per game, one per metric).

    Args:
        full_results: Results from full context condition
        limited_results: Results from limited context condition

    Returns:
        List of dicts in long format with columns:
        game_id, context_condition, metric_name, metric_value
    """
    long_data = []

    # Process full context results
    for game in full_results:
        # Add specialization metric row
        long_data.append({
            'game_id': game['game_id'],
            'context_condition': game['context_condition'],
            'metric_name': 'specialization',
            'metric_value': game['specialization_index']
        })
        # Add retrieval metric row
        long_data.append({
            'game_id': game['game_id'],
            'context_condition': game['context_condition'],
            'metric_name': 'retrieval',
            'metric_value': game['retrieval_efficiency']
        })

    # Process limited context results
    for game in limited_results:
        # Add specialization metric row
        long_data.append({
            'game_id': game['game_id'],
            'context_condition': game['context_condition'],
            'metric_name': 'specialization',
            'metric_value': game['specialization_index']
        })
        # Add retrieval metric row
        long_data.append({
            'game_id': game['game_id'],
            'context_condition': game['context_condition'],
            'metric_name': 'retrieval',
            'metric_value': game['retrieval_efficiency']
        })

    return long_data

def compute_effect_size_etasquared(
    ss_between: float,
    ss_within: float
) -> float:
    """
    Compute eta-squared effect size.

    Args:
        ss_between: Sum of squares between groups
        ss_within: Sum of squares within groups

    Returns:
        Eta-squared value (0 to 1)
    """
    ss_total = ss_between + ss_within
    if ss_total == 0:
        return 0.0
    return ss_between / ss_total

def compute_two_way_anova_manual(
    data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute Two-Way ANOVA manually without statsmodels.

    Implements a Two-Way Independent-Samples ANOVA where:
    - Factor A: context_condition (Between-Subjects)
    - Factor B: metric_name (Within-Subjects, repeated measures)

    Note: Since this is a mixed design (one between, one within),
    we compute the interaction and main effects using standard formulas.

    Args:
        data: Long-format data list

    Returns:
        Dictionary with ANOVA table values
    """
    # Group data by factors
    context_levels = list(set(row['context_condition'] for row in data))
    metric_levels = list(set(row['metric_name'] for row in data))

    n_context = len(context_levels)
    n_metric = len(metric_levels)

    # Calculate grand mean
    all_values = [row['metric_value'] for row in data]
    grand_mean = np.mean(all_values)
    N = len(all_values)

    # Calculate SS_total
    ss_total = sum((v - grand_mean) ** 2 for v in all_values)

    # Calculate SS_context (Factor A - Between Subjects)
    context_means = {}
    context_counts = {}
    for row in data:
        ctx = row['context_condition']
        if ctx not in context_means:
            context_means[ctx] = 0
            context_counts[ctx] = 0
        context_means[ctx] += row['metric_value']
        context_counts[ctx] += 1

    for ctx in context_means:
        context_means[ctx] /= context_counts[ctx]

    ss_context = sum(
        context_counts[ctx] * (context_means[ctx] - grand_mean) ** 2
        for ctx in context_levels
    )

    # Calculate SS_metric (Factor B - Within Subjects)
    metric_means = {}
    metric_counts = {}
    for row in data:
        met = row['metric_name']
        if met not in metric_means:
            metric_means[met] = 0
            metric_counts[met] = 0
        metric_means[met] += row['metric_value']
        metric_counts[met] += 1

    for met in metric_means:
        metric_means[met] /= metric_counts[met]

    ss_metric = sum(
        metric_counts[met] * (metric_means[met] - grand_mean) ** 2
        for met in metric_levels
    )

    # Calculate SS_interaction
    # First, calculate cell means and counts
    cell_data = {}
    for row in data:
        key = (row['context_condition'], row['metric_name'])
        if key not in cell_data:
            cell_data[key] = []
        cell_data[key].append(row['metric_value'])

    cell_means = {}
    cell_counts = {}
    for key, values in cell_data.items():
        cell_means[key] = np.mean(values)
        cell_counts[key] = len(values)

    # SS_interaction = SS_cells - SS_context - SS_metric
    ss_cells = 0
    for key, mean in cell_means.items():
        ctx, met = key
        n = cell_counts[key]
        ss_cells += n * (mean - grand_mean) ** 2

    ss_interaction = ss_cells - ss_context - ss_metric

    # Calculate SS_error (residual)
    ss_error = ss_total - ss_cells

    # Degrees of freedom
    df_context = n_context - 1
    df_metric = n_metric - 1
    df_interaction = df_context * df_metric

    # For repeated measures design, error term for within-subjects and interaction
    # is typically calculated differently, but for independent-samples ANOVA
    # as specified in FR-006, we use:
    df_error = N - (n_context * n_metric)

    # Mean squares
    ms_context = ss_context / df_context if df_context > 0 else 0
    ms_metric = ss_metric / df_metric if df_metric > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 0

    # F-statistics
    f_context = ms_context / ms_error if ms_error > 0 else 0
    f_metric = ms_metric / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0

    # P-values (approximation using F-distribution)
    # Using scipy if available, otherwise approximate
    try:
        from scipy.stats import f as f_dist
        p_context = 1 - f_dist.cdf(f_context, df_context, df_error)
        p_metric = 1 - f_dist.cdf(f_metric, df_metric, df_error)
        p_interaction = 1 - f_dist.cdf(f_interaction, df_interaction, df_error)
    except ImportError:
        # Fallback: use simple approximation
        p_context = _approximate_p_value(f_context, df_context, df_error)
        p_metric = _approximate_p_value(f_metric, df_metric, df_error)
        p_interaction = _approximate_p_value(f_interaction, df_interaction, df_error)

    # Effect sizes (eta-squared)
    eta_context = compute_effect_size_etasquared(ss_context, ss_error)
    eta_metric = compute_effect_size_etasquared(ss_metric, ss_error)
    eta_interaction = compute_effect_size_etasquared(ss_interaction, ss_error)

    return {
        'source': 'context_condition',
        'df': df_context,
        'ss': ss_context,
        'ms': ms_context,
        'f': f_context,
        'p_value': p_context,
        'eta_squared': eta_context
    }, {
        'source': 'metric_name',
        'df': df_metric,
        'ss': ss_metric,
        'ms': ms_metric,
        'f': f_metric,
        'p_value': p_metric,
        'eta_squared': eta_metric
    }, {
        'source': 'interaction',
        'df': df_interaction,
        'ss': ss_interaction,
        'ms': ms_interaction,
        'f': f_interaction,
        'p_value': p_interaction,
        'eta_squared': eta_interaction
    }, {
        'source': 'error',
        'df': df_error,
        'ss': ss_error,
        'ms': ms_error
    }, {
        'total': {
            'df': N - 1,
            'ss': ss_total
        }
    }

def _approximate_p_value(f_stat: float, df_num: int, df_den: int) -> float:
    """
    Approximate p-value for F-distribution when scipy is not available.

    This is a simple approximation for demonstration purposes.
    In production, scipy.stats.f.cdf should be used.

    Args:
        f_stat: F-statistic value
        df_num: Numerator degrees of freedom
        df_den: Denominator degrees of freedom

    Returns:
        Approximate p-value
    """
    # Simple approximation: if F > 4, p < 0.05 typically
    # This is very rough and should be replaced with scipy
    if df_den <= 0:
        return 1.0

    # Use a simplified approximation
    # For large df_den, F ~ chi-squared / df_num
    # This is a crude approximation
    if f_stat <= 1:
        return 0.5
    elif f_stat < 2:
        return 0.2
    elif f_stat < 4:
        return 0.05
    elif f_stat < 10:
        return 0.01
    else:
        return 0.001

def apply_bonferroni_correction(
    p_values: Dict[str, float],
    alpha: float = 0.05
) -> Tuple[Dict[str, float], float, int]:
    """
    Apply Bonferroni correction to a set of p-values.

    The Bonferroni correction controls the family-wise error rate by
    dividing the significance level by the number of tests, or
    equivalently, multiplying p-values by the number of tests.

    Args:
        p_values: Dictionary mapping test names to their p-values
        alpha: Original significance level (default 0.05)

    Returns:
        Tuple of (corrected_p_values, corrected_alpha, num_tests)
    """
    num_tests = len(p_values)
    if num_tests == 0:
        return {}, alpha, 0

    # Corrected alpha (family-wise error rate)
    corrected_alpha = alpha / num_tests

    # Corrected p-values (capped at 1.0)
    corrected_p_values = {}
    for name, p in p_values.items():
        corrected_p = min(p * num_tests, 1.0)
        corrected_p_values[name] = corrected_p

    return corrected_p_values, corrected_alpha, num_tests

def compute_two_way_anova(
    full_path: Union[str, Path],
    limited_path: Union[str, Path],
    alpha: float = 0.05
) -> ANOVAFullResult:
    """
    Perform complete Two-Way ANOVA with Bonferroni correction.

    This function:
    1. Loads results from full and limited context conditions
    2. Prepares data in long format
    3. Computes ANOVA manually (or via statsmodels if available)
    4. Applies Bonferroni correction to all p-values
    5. Returns comprehensive results

    Args:
        full_path: Path to results_full.csv
        limited_path: Path to results_limited.csv
        alpha: Significance level for hypothesis testing (default 0.05)

    Returns:
        ANOVAFullResult containing all ANOVA statistics and corrected values
    """
    # Load data
    full_results, limited_results = load_experiment_results(full_path, limited_path)

    if not full_results and not limited_results:
        raise ValueError("No data found in input files")

    # Prepare data in long format
    long_data = prepare_data_for_anova(full_results, limited_results)

    # Compute ANOVA
    result_context, result_metric, result_interaction, result_error, result_total = \
        compute_two_way_anova_manual(long_data)

    # Collect raw p-values
    raw_p_values = {
        'context_condition': result_context['p_value'],
        'metric_name': result_metric['p_value'],
        'interaction': result_interaction['p_value']
    }

    # Apply Bonferroni correction
    bonferroni_p_values, corrected_alpha, num_tests = \
        apply_bonferroni_correction(raw_p_values, alpha)

    # Extract key statistics
    interaction_p = result_interaction['p_value']
    interaction_p_bonf = bonferroni_p_values['interaction']
    context_p = result_context['p_value']
    context_p_bonf = bonferroni_p_values['context_condition']
    metric_p = result_metric['p_value']
    metric_p_bonf = bonferroni_p_values['metric_name']

    # Determine significance
    significant_interaction = interaction_p_bonf < corrected_alpha
    significant_context = context_p_bonf < corrected_alpha
    significant_metric = metric_p_bonf < corrected_alpha

    # Effect sizes
    effect_sizes = {
        'context_condition': result_context['eta_squared'],
        'metric_name': result_metric['eta_squared'],
        'interaction': result_interaction['eta_squared']
    }

    # Generate summary text
    summary_parts = []
    summary_parts.append(f"Two-Way ANOVA Results (Bonferroni-corrected α = {corrected_alpha:.4f}):")
    summary_parts.append(f"  - Interaction (context × metric): F({result_interaction['df']:.0f}, {result_error['df']:.0f}) = {result_interaction['f']:.4f}, "
                       f"p = {interaction_p:.4f}, p_corrected = {interaction_p_bonf:.4f}, "
                       f"{'significant' if significant_interaction else 'not significant'}")
    summary_parts.append(f"  - Main effect (context): F({result_context['df']:.0f}, {result_error['df']:.0f}) = {result_context['f']:.4f}, "
                       f"p = {context_p:.4f}, p_corrected = {context_p_bonf:.4f}, "
                       f"{'significant' if significant_context else 'not significant'}")
    summary_parts.append(f"  - Main effect (metric): F({result_metric['df']:.0f}, {result_error['df']:.0f}) = {result_metric['f']:.4f}, "
                       f"p = {metric_p:.4f}, p_corrected = {metric_p_bonf:.4f}, "
                       f"{'significant' if significant_metric else 'not significant'}")
    summary_parts.append(f"  - Bonferroni factor: {num_tests} tests")
    summary_parts.append(f"  - Effect sizes (η²): context={effect_sizes['context_condition']:.4f}, "
                       f"metric={effect_sizes['metric_name']:.4f}, interaction={effect_sizes['interaction']:.4f}")

    summary_text = "\n".join(summary_parts)

    return ANOVAFullResult(
        interaction_p_value=interaction_p,
        interaction_p_bonferroni=interaction_p_bonf,
        main_effect_context_p=context_p,
        main_effect_context_p_bonferroni=context_p_bonf,
        main_effect_metric_p=metric_p,
        main_effect_metric_p_bonferroni=metric_p_bonf,
        corrected_alpha=corrected_alpha,
        significant_interaction=significant_interaction,
        significant_context=significant_context,
        significant_metric=significant_metric,
        bonferroni_factor=num_tests,
        raw_p_values=raw_p_values,
        bonferroni_p_values=bonferroni_p_values,
        effect_sizes=effect_sizes,
        summary_text=summary_text
    )

def run_anova_analysis(
    full_path: Union[str, Path],
    limited_path: Union[str, Path],
    output_path: Union[str, Path],
    alpha: float = 0.05
) -> ANOVAFullResult:
    """
    Run complete ANOVA analysis and save results.

    Args:
        full_path: Path to results_full.csv
        limited_path: Path to results_limited.csv
        output_path: Path to save JSON results
        alpha: Significance level (default 0.05)

    Returns:
        ANOVAFullResult object
    """
    result = compute_two_way_anova(full_path, limited_path, alpha)

    # Save results to JSON
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results_dict = {
        'interaction': {
            'p_value': result.interaction_p_value,
            'p_value_bonferroni': result.interaction_p_bonferroni,
            'significant': result.significant_interaction,
            'effect_size_eta_squared': result.effect_sizes['interaction']
        },
        'main_effect_context': {
            'p_value': result.main_effect_context_p,
            'p_value_bonferroni': result.main_effect_context_p_bonferroni,
            'significant': result.significant_context,
            'effect_size_eta_squared': result.effect_sizes['context_condition']
        },
        'main_effect_metric': {
            'p_value': result.main_effect_metric_p,
            'p_value_bonferroni': result.main_effect_metric_p_bonferroni,
            'significant': result.significant_metric,
            'effect_size_eta_squared': result.effect_sizes['metric_name']
        },
        'bonferroni_correction': {
            'original_alpha': alpha,
            'corrected_alpha': result.corrected_alpha,
            'num_tests': result.bonferroni_factor,
            'method': 'Bonferroni'
        },
        'summary': result.summary_text
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)

    return result

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for ANOVA analysis CLI."""
    parser = argparse.ArgumentParser(
        description='Run Two-Way ANOVA with Bonferroni correction'
    )
    parser.add_argument(
        '--full-results',
        type=str,
        required=True,
        help='Path to results_full.csv'
    )
    parser.add_argument(
        '--limited-results',
        type=str,
        required=True,
        help='Path to results_limited.csv'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/anova_results.json',
        help='Output path for JSON results'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level (default: 0.05)'
    )
    return parser

def main() -> None:
    """Main entry point for ANOVA analysis CLI."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = run_anova_analysis(
            args.full_results,
            args.limited_results,
            args.output,
            args.alpha
        )
        print(result.summary_text)
    except Exception as e:
        print(f"Error running ANOVA analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()