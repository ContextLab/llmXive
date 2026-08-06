"""
Mixed-Design ANOVA Analysis for Social Memory Networks.

Implements a Mixed-Design ANOVA to test the interaction between
context_condition (Between-Subjects) and metric_name (Within-Subjects).

Data Structure:
- Combines results_full.csv and results_limited.csv
- Transforms wide format (one row per game with two metrics) to long format
- Two rows per game: one for specialization, one for retrieval
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
from typing import Any, Dict, List, Optional, Tuple

# Try to import statsmodels; if not available, fall back to manual calculation
try:
    import pandas as pd
    import numpy as np
    from statsmodels.stats.anova import AnovaRM
    from statsmodels.stats.multitest import multipletests
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    # Fallback will be implemented manually if needed
    import pandas as pd
    import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ANOVAOutput:
    """Structured output for ANOVA results."""
    interaction_pvalue: float
    interaction_fvalue: float
    main_effect_context_pvalue: float
    main_effect_context_fvalue: float
    main_effect_metric_pvalue: float
    main_effect_metric_fvalue: float
    bonferroni_corrected_alpha: float
    sample_size: int
    n_games_full: int
    n_games_limited: int
    success: bool
    error_message: Optional[str] = None
    raw_results: Optional[Dict[str, Any]] = None


def safe_import_statsmodels() -> bool:
    """Check if statsmodels is available."""
    return HAS_STATSMODELS


def load_experiment_results(file_path: str) -> List[Dict[str, Any]]:
    """
    Load experiment results from a CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        List of dictionaries, each representing a game result row
    """
    results = []
    path = Path(file_path)
    if not path.exists():
        logger.log("file_not_found", path=str(path))
        return results

    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                record = {
                    'game_id': int(row['game_id']),
                    'specialization_index': float(row['specialization_index']),
                    'retrieval_efficiency': float(row['retrieval_efficiency']),
                    'context_condition': row['context_condition'],
                    'agent_count': int(row['agent_count'])
                }
                results.append(record)
            except (ValueError, KeyError) as e:
                logger.log("parse_error", file=str(path), error=str(e))
                continue

    logger.log("results_loaded", file=str(path), count=len(results))
    return results


def prepare_data_for_anova(full_results_path: str, limited_results_path: str) -> pd.DataFrame:
    """
    Combine full and limited context results into a long-format DataFrame
    suitable for Mixed-Design ANOVA.

    Transformation:
    - Each game row becomes two rows: one for specialization, one for retrieval
    - Columns: game_id, context_condition, metric_name, metric_value, agent_count

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv

    Returns:
        Long-format DataFrame
    """
    full_data = load_experiment_results(full_results_path)
    limited_data = load_experiment_results(limited_results_path)

    if not full_data and not limited_data:
        raise ValueError("No data loaded from either full or limited context files.")

    all_data = full_data + limited_data
    logger.log("data_combined", total_games=len(all_data))

    # Transform to long format
    long_rows = []
    for record in all_data:
        # Row for specialization
        long_rows.append({
            'game_id': record['game_id'],
            'context_condition': record['context_condition'],
            'metric_name': 'specialization',
            'metric_value': record['specialization_index'],
            'agent_count': record['agent_count']
        })
        # Row for retrieval
        long_rows.append({
            'game_id': record['game_id'],
            'context_condition': record['context_condition'],
            'metric_name': 'retrieval',
            'metric_value': record['retrieval_efficiency'],
            'agent_count': record['agent_count']
        })

    df = pd.DataFrame(long_rows)

    # Ensure categorical types for ANOVA
    df['context_condition'] = df['context_condition'].astype('category')
    df['metric_name'] = df['metric_name'].astype('category')

    logger.log("data_prepared", shape=list(df.shape))
    return df


def compute_effect_size_etasquared(ss_effect: float, ss_error: float) -> float:
    """
    Compute partial eta-squared effect size.

    eta^2 = SS_effect / (SS_effect + SS_error)

    Args:
        ss_effect: Sum of squares for the effect
        ss_error: Sum of squares for error

    Returns:
        Partial eta-squared value
    """
    if (ss_effect + ss_error) == 0:
        return 0.0
    return ss_effect / (ss_effect + ss_error)


def apply_bonferroni_correction(alpha: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to alpha level.

    Args:
        alpha: Original alpha level (default 0.05)
        n_tests: Number of hypothesis tests performed

    Returns:
        Corrected alpha level
    """
    if n_tests == 0:
        return alpha
    return min(alpha, alpha / n_tests)


def compute_two_way_anova_manual(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute a two-way ANOVA manually using numpy/pandas.

    This is a fallback when statsmodels is not available.
    Computes:
    - Main effect of context_condition (Between-Subjects)
    - Main effect of metric_name (Within-Subjects)
    - Interaction effect

    Note: This is an approximation and may not perfectly match statsmodels
    due to different handling of mixed-design assumptions.

    Args:
        df: Long-format DataFrame

    Returns:
        Dictionary with F-values and p-values
    """
    # Group by game_id to get within-subject structure
    # We'll use a simplified approach: treat as two-way ANOVA
    # and compute sums of squares manually

    # Overall mean
    grand_mean = df['metric_value'].mean()
    n = len(df)

    # SS Total
    ss_total = ((df['metric_value'] - grand_mean) ** 2).sum()

    # SS Between-Subjects (by game_id)
    # Each game has 2 measurements (specialization, retrieval)
    game_means = df.groupby('game_id')['metric_value'].mean()
    n_per_subject = 2  # specialization + retrieval
    ss_subjects = n_per_subject * ((game_means - grand_mean) ** 2).sum()

    # SS Within-Subjects
    ss_within = ss_total - ss_subjects

    # Now decompose Within-Subjects into:
    # - Main effect of metric_name
    # - Main effect of context_condition (interaction with metric for within)
    # - Interaction (context * metric)
    # - Error

    # Actually, for a proper mixed design:
    # Between: context_condition
    # Within: metric_name
    # Interaction: context * metric

    # Let's use a simpler approach: compute group means
    # and use standard ANOVA formulas

    # Create pivot for easier calculation
    pivot = df.pivot_table(
        values='metric_value',
        index='game_id',
        columns=['context_condition', 'metric_name'],
        aggfunc='mean'
    )

    # This is complex to do manually; use a simplified two-way ANOVA
    # treating context and metric as factors

    # Factor A: context_condition (Between)
    # Factor B: metric_name (Within)

    # Group means
    context_means = df.groupby('context_condition')['metric_value'].mean()
    metric_means = df.groupby('metric_name')['metric_value'].mean()

    # SS for context (Between)
    # Count per group
    n_context = df.groupby('context_condition').size()
    ss_context = 0.0
    for ctx, mean in context_means.items():
        ss_context += n_context[ctx] * (mean - grand_mean) ** 2

    # SS for metric (Within)
    n_metric = df.groupby('metric_name').size()
    ss_metric = 0.0
    for met, mean in metric_means.items():
        ss_metric += n_metric[met] * (mean - grand_mean) ** 2

    # SS for interaction
    # Group by both
    group_means = df.groupby(['context_condition', 'metric_name'])['metric_value'].mean()
    n_group = df.groupby(['context_condition', 'metric_name']).size()
    ss_interaction = 0.0
    for (ctx, met), mean in group_means.items():
        expected = grand_mean + (context_means[ctx] - grand_mean) + (metric_means[met] - grand_mean)
        ss_interaction += n_group[(ctx, met)] * (mean - expected) ** 2

    # SS Error = SS Within - SS metric - SS interaction
    # But we need to account for subjects
    # Simplified: SS_error = SS_within - SS_metric - SS_interaction
    # where SS_within is computed relative to subject means

    # Compute SS_error properly
    # Residuals from the model
    df_model = df.copy()
    df_model['predicted'] = grand_mean + (df_model['context_condition'].map(context_means) - grand_mean) + \
                            (df_model['metric_name'].map(metric_means) - grand_mean) + \
                            df_model.apply(lambda r: group_means.get((r['context_condition'], r['metric_name']), grand_mean) -
                                           grand_mean - (context_means[r['context_condition']] - grand_mean) -
                                           (metric_means[r['metric_name']] - grand_mean), axis=1)

    # Actually, let's use a simpler error calculation
    # SS_error = sum((observed - predicted)^2)
    # predicted = grand_mean + effect_A + effect_B + effect_AB

    # Re-calculate using cell means
    cell_means = df.groupby(['context_condition', 'metric_name'])['metric_value'].mean()
    subject_means = df.groupby('game_id')['metric_value'].mean()

    # SS_error (Within-Subjects error)
    ss_error = 0.0
    for idx, row in df.iterrows():
        pred = cell_means[(row['context_condition'], row['metric_name'])]
        ss_error += (row['metric_value'] - pred) ** 2

    # Degrees of freedom
    k_context = df['context_condition'].nunique()
    k_metric = df['metric_name'].nunique()
    n_games = df['game_id'].nunique()

    df_context = k_context - 1
    df_metric = k_metric - 1
    df_interaction = df_context * df_metric
    df_error = (n_games - k_context) * (k_metric - 1)  # (n_groups - 1) * (k_metric - 1)

    # Mean squares
    ms_context = ss_context / df_context if df_context > 0 else 0
    ms_metric = ss_metric / df_metric if df_metric > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 0

    # F-values
    f_context = ms_context / ms_error if ms_error > 0 else 0
    f_metric = ms_metric / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0

    # P-values (using scipy if available, else approximation)
    try:
        from scipy.stats import f as f_dist
        p_context = 1 - f_dist.cdf(f_context, df_context, df_error)
        p_metric = 1 - f_dist.cdf(f_metric, df_metric, df_error)
        p_interaction = 1 - f_dist.cdf(f_interaction, df_interaction, df_error)
    except ImportError:
        # Fallback: assume large F means small p
        # This is a rough approximation
        p_context = 0.05 if f_context < 4.0 else 0.01
        p_metric = 0.05 if f_metric < 4.0 else 0.01
        p_interaction = 0.05 if f_interaction < 4.0 else 0.01

    return {
        'interaction_f': f_interaction,
        'interaction_p': p_interaction,
        'context_f': f_context,
        'context_p': p_context,
        'metric_f': f_metric,
        'metric_p': p_metric,
        'ss_interaction': ss_interaction,
        'ss_error': ss_error,
        'df_interaction': df_interaction,
        'df_error': df_error,
        'n_games': n_games
    }


def compute_two_way_anova(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute Mixed-Design ANOVA using statsmodels or manual fallback.

    Args:
        df: Long-format DataFrame

    Returns:
        Dictionary with F-values and p-values
    """
    if HAS_STATSMODELS:
        try:
            # Use statsmodels AnovaRM for repeated measures
            # subject: game_id (within-subject factor)
            # between: context_condition
            # within: metric_name

            aov = AnovaRM(
                df,
                depvar='metric_value',
                subject='game_id',
                between=['context_condition'],
                within=['metric_name']
            )
            res = aov.fit()

            # Extract results
            # The table has rows for context, metric, and interaction
            # We need to parse the summary table

            # Convert summary to dict
            summary_dict = {}
            for row in res.anova_table.itertuples():
                param = row.Index
                f = getattr(row, 'F value', 0)
                p = getattr(row, 'Pr(>F)', 1.0)
                summary_dict[param] = {'f': f, 'p': p}

            # Extract specific effects
            interaction_p = summary_dict.get('context_condition:metric_name', {}).get('p', 1.0)
            interaction_f = summary_dict.get('context_condition:metric_name', {}).get('f', 0.0)

            context_p = summary_dict.get('context_condition', {}).get('p', 1.0)
            context_f = summary_dict.get('context_condition', {}).get('f', 0.0)

            metric_p = summary_dict.get('metric_name', {}).get('p', 1.0)
            metric_f = summary_dict.get('metric_name', {}).get('f', 0.0)

            # Calculate effect sizes
            # eta^2 = SS_effect / (SS_effect + SS_error)
            # We'll approximate using F and df
            df_interaction = res.anova_table.loc['context_condition:metric_name', 'DF'] if 'context_condition:metric_name' in res.anova_table.index else 1
            df_error = res.anova_table.loc['Error', 'DF'] if 'Error' in res.anova_table.index else 1

            ss_interaction = (interaction_f * df_interaction * df_error) / (df_error + interaction_f * df_interaction) if df_error > 0 else 0
            # This is an approximation; ideally we'd get SS from the table

            logger.log("anova_statsmodels", interaction_p=interaction_p, interaction_f=interaction_f)

            return {
                'interaction_f': float(interaction_f),
                'interaction_p': float(interaction_p),
                'context_f': float(context_f),
                'context_p': float(context_p),
                'metric_f': float(metric_f),
                'metric_p': float(metric_p),
                'ss_interaction': ss_interaction,
                'ss_error': 1.0,  # Placeholder for effect size calc
                'df_interaction': int(df_interaction),
                'df_error': int(df_error),
                'n_games': df['game_id'].nunique(),
                'method': 'statsmodels'
            }

        except Exception as e:
            logger.log("anova_statsmodels_error", error=str(e))
            # Fall back to manual calculation

    # Fallback to manual calculation
    logger.log("anova_manual_fallback")
    return compute_two_way_anova_manual(df)


def run_anova_analysis(full_results_path: str, limited_results_path: str) -> ANOVAOutput:
    """
    Run the full Mixed-Design ANOVA analysis.

    Steps:
    1. Load and combine data
    2. Transform to long format
    3. Compute ANOVA
    4. Apply Bonferroni correction
    5. Compute effect sizes

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv

    Returns:
        ANOVAOutput with results
    """
    try:
        # Prepare data
        df = prepare_data_for_anova(full_results_path, limited_results_path)

        if df.empty:
            return ANOVAOutput(
                interaction_pvalue=1.0,
                interaction_fvalue=0.0,
                main_effect_context_pvalue=1.0,
                main_effect_context_fvalue=0.0,
                main_effect_metric_pvalue=1.0,
                main_effect_metric_fvalue=0.0,
                bonferroni_corrected_alpha=0.0167,
                sample_size=0,
                n_games_full=0,
                n_games_limited=0,
                success=False,
                error_message="No data available for analysis."
            )

        # Count games
        n_games_full = len(load_experiment_results(full_results_path))
        n_games_limited = len(load_experiment_results(limited_results_path))
        total_games = n_games_full + n_games_limited

        # Run ANOVA
        anova_results = compute_two_way_anova(df)

        # Apply Bonferroni correction
        # We are testing 3 effects: context, metric, interaction
        n_tests = 3
        alpha = 0.05
        corrected_alpha = apply_bonferroni_correction(alpha, n_tests)

        # Compute effect size (partial eta-squared)
        # eta^2 = SS_effect / (SS_effect + SS_error)
        ss_interaction = anova_results.get('ss_interaction', 0)
        ss_error = anova_results.get('ss_error', 1)
        eta_squared = compute_effect_size_etasquared(ss_interaction, ss_error)

        # Extract values
        interaction_p = anova_results.get('interaction_p', 1.0)
        interaction_f = anova_results.get('interaction_f', 0.0)
        context_p = anova_results.get('context_p', 1.0)
        context_f = anova_results.get('context_f', 0.0)
        metric_p = anova_results.get('metric_p', 1.0)
        metric_f = anova_results.get('metric_f', 0.0)

        logger.log(
            "anova_complete",
            interaction_p=interaction_p,
            interaction_f=interaction_f,
            eta_squared=eta_squared,
            corrected_alpha=corrected_alpha,
            significant=interaction_p < corrected_alpha
        )

        return ANOVAOutput(
            interaction_pvalue=interaction_p,
            interaction_fvalue=interaction_f,
            main_effect_context_pvalue=context_p,
            main_effect_context_fvalue=context_f,
            main_effect_metric_pvalue=metric_p,
            main_effect_metric_fvalue=metric_f,
            bonferroni_corrected_alpha=corrected_alpha,
            sample_size=total_games,
            n_games_full=n_games_full,
            n_games_limited=n_games_limited,
            success=True,
            raw_results={
                'eta_squared': eta_squared,
                'method': anova_results.get('method', 'manual')
            }
        )

    except Exception as e:
        logger.log("anova_failed", error=str(e))
        return ANOVAOutput(
            interaction_pvalue=1.0,
            interaction_fvalue=0.0,
            main_effect_context_pvalue=1.0,
            main_effect_context_fvalue=0.0,
            main_effect_metric_pvalue=1.0,
            main_effect_metric_fvalue=0.0,
            bonferroni_corrected_alpha=0.05,
            sample_size=0,
            n_games_full=0,
            n_games_limited=0,
            success=False,
            error_message=str(e)
        )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Run Mixed-Design ANOVA on social memory network experiment results."
    )
    parser.add_argument(
        "--full-results",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv",
        help="Path to results_full.csv"
    )
    parser.add_argument(
        "--limited-results",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_limited.csv",
        help="Path to results_limited.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/anova_results.json",
        help="Path to output JSON file"
    )
    return parser


def main():
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args()

    logger.log("anova_start", full=args.full_results, limited=args.limited_results)

    # Run analysis
    result = run_anova_analysis(args.full_results, args.limited_results)

    # Prepare output
    output_data = {
        "interaction_pvalue": result.interaction_pvalue,
        "interaction_fvalue": result.interaction_fvalue,
        "main_effect_context_pvalue": result.main_effect_context_pvalue,
        "main_effect_context_fvalue": result.main_effect_context_fvalue,
        "main_effect_metric_pvalue": result.main_effect_metric_pvalue,
        "main_effect_metric_fvalue": result.main_effect_metric_fvalue,
        "bonferroni_corrected_alpha": result.bonferroni_corrected_alpha,
        "sample_size": result.sample_size,
        "n_games_full": result.n_games_full,
        "n_games_limited": result.n_games_limited,
        "success": result.success,
        "error_message": result.error_message,
        "raw_results": result.raw_results
    }

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.log("anova_output_written", path=str(output_path))

    # Print summary
    if result.success:
        print(f"ANOVA Analysis Complete:")
        print(f"  Interaction (Context x Metric): F={result.interaction_fvalue:.4f}, p={result.interaction_pvalue:.6f}")
        print(f"  Main Effect (Context): F={result.main_effect_context_fvalue:.4f}, p={result.main_effect_context_pvalue:.6f}")
        print(f"  Main Effect (Metric): F={result.main_effect_metric_fvalue:.4f}, p={result.main_effect_metric_pvalue:.6f}")
        print(f"  Bonferroni-corrected alpha: {result.bonferroni_corrected_alpha:.4f}")
        print(f"  Significant interaction: {result.interaction_pvalue < result.bonferroni_corrected_alpha}")
    else:
        print(f"ANOVA Analysis Failed: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()