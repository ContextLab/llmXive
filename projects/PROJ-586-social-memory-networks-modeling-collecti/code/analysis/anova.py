"""ANOVA analysis module for social memory networks."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ANOVAOutput:
    """Container for ANOVA results."""
    f_statistic: float
    p_value: float
    df_between: int
    df_within: int
    ss_between: float
    ss_within: float
    ms_between: float
    ms_within: float
    interaction_p_value: Optional[float] = None
    bonferroni_corrected_alpha: Optional[float] = None


def safe_import_statsmodels() -> Optional[Any]:
    """Safely import statsmodels, returning None if not available."""
    try:
        import statsmodels.api as sm
        from statsmodels.stats.anova import anova_lm
        return sm, anova_lm
    except ImportError:
        logger.warning("statsmodels not available, using manual ANOVA")
        return None


def load_experiment_results(
    results_path: Path,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load full and limited context results.
    
    Returns:
        Tuple of (full_results, limited_results)
    """
    full_results = []
    limited_results = []

    # Load full context results
    full_path = results_path / "results_full.csv"
    if full_path.exists():
        with open(full_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                full_results.append(row)
    else:
        logger.warning("Full results not found: %s", full_path)

    # Load limited context results
    limited_path = results_path / "results_limited.csv"
    if limited_path.exists():
        with open(limited_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                limited_results.append(row)
    else:
        logger.warning("Limited results not found: %s", limited_path)

    return full_results, limited_results


def prepare_data_for_anova(
    full_results: List[Dict[str, Any]],
    limited_results: List[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Prepare data for two-way ANOVA.
    
    Creates a long-format DataFrame with columns:
    game_id, context_condition, metric_name, metric_value
    """
    rows = []

    # Process full context results
    for row in full_results:
        game_id = row.get("game_id", 0)
        spec_val = float(row.get("specialization_index", 0))
        ret_val = float(row.get("retrieval_efficiency", 0))

        rows.append({
            "game_id": game_id,
            "context_condition": "full",
            "metric_name": "specialization",
            "metric_value": spec_val
        })
        rows.append({
            "game_id": game_id,
            "context_condition": "full",
            "metric_name": "retrieval",
            "metric_value": ret_val
        })

    # Process limited context results
    for row in limited_results:
        game_id = row.get("game_id", 0)
        spec_val = float(row.get("specialization_index", 0))
        ret_val = float(row.get("retrieval_efficiency", 0))

        rows.append({
            "game_id": game_id,
            "context_condition": "limited",
            "metric_name": "specialization",
            "metric_value": spec_val
        })
        rows.append({
            "game_id": game_id,
            "context_condition": "limited",
            "metric_name": "retrieval",
            "metric_value": ret_val
        })

    return pd.DataFrame(rows)


def compute_two_way_anova(df: pd.DataFrame) -> ANOVAOutput:
    """
    Compute two-way ANOVA with interaction.
    
    Model: metric_value ~ C(context_condition) * C(metric_name)
    """
    sm, anova_lm = safe_import_statsmodels()

    if sm is not None:
        try:
            from statsmodels.formula.api import ols

            model = ols("metric_value ~ C(context_condition) * C(metric_name)", data=df).fit()
            anova_table = anova_lm(model, typ=2)

            # Extract values
            f_stat = float(anova_table["F"][0])
            p_val = float(anova_table["PR(>F)"][0])
            df_between = int(anova_table["df"][0])
            ss_between = float(anova_table["sum_sq"][0])

            # Interaction term
            interaction_row = anova_table.loc["C(context_condition):C(metric_name)"]
            interaction_p = float(interaction_row["PR(>F)"]) if not np.isnan(interaction_row["PR(>F)"]) else None

            return ANOVAOutput(
                f_statistic=f_stat,
                p_value=p_val,
                df_between=df_between,
                df_within=len(df) - df_between - 1,
                ss_between=ss_between,
                ss_within=float(anova_table["sum_sq"].sum() - ss_between),
                ms_between=ss_between / df_between if df_between > 0 else 0,
                ms_within=float(anova_table["sum_sq"].iloc[-1]) / float(anova_table["df"].iloc[-1]) if len(anova_table) > 0 else 0,
                interaction_p_value=interaction_p
            )
        except Exception as e:
            logger.warning("statsmodels ANOVA failed: %s, using manual", e)
            sm = None

    # Manual ANOVA calculation
    return compute_manual_anova(df)


def compute_manual_anova(df: pd.DataFrame) -> ANOVAOutput:
    """
    Manual two-way ANOVA calculation when statsmodels is unavailable.
    """
    # Group by factors
    context_levels = df["context_condition"].unique()
    metric_levels = df["metric_name"].unique()

    n_context = len(context_levels)
    n_metric = len(metric_levels)
    n_total = len(df)

    # Grand mean
    grand_mean = df["metric_value"].mean()

    # Sum of squares
    ss_total = ((df["metric_value"] - grand_mean) ** 2).sum()

    # Group means
    group_means = df.groupby(["context_condition", "metric_name"])["metric_value"].mean()

    # Main effects
    context_means = df.groupby("context_condition")["metric_value"].mean()
    metric_means = df.groupby("metric_name")["metric_value"].mean()

    # Count per group
    counts = df.groupby(["context_condition", "metric_name"]).size()

    # SS for context
    ss_context = 0
    for ctx in context_levels:
        n_ctx = len(df[df["context_condition"] == ctx])
        ss_context += n_ctx * (context_means[ctx] - grand_mean) ** 2

    # SS for metric
    ss_metric = 0
    for met in metric_levels:
        n_met = len(df[df["metric_name"] == met])
        ss_metric += n_met * (metric_means[met] - grand_mean) ** 2

    # SS interaction
    ss_interaction = 0
    for ctx in context_levels:
        for met in metric_levels:
            mask = (df["context_condition"] == ctx) & (df["metric_name"] == met)
            n_cell = mask.sum()
            if n_cell > 0:
                cell_mean = df[mask]["metric_value"].mean()
                ss_interaction += n_cell * (
                    cell_mean - context_means[ctx] - metric_means[met] + grand_mean
                ) ** 2

    # SS error
    ss_error = ss_total - ss_context - ss_metric - ss_interaction

    # Degrees of freedom
    df_context = n_context - 1
    df_metric = n_metric - 1
    df_interaction = df_context * df_metric
    df_error = n_total - (n_context * n_metric)

    # Mean squares
    ms_context = ss_context / df_context if df_context > 0 else 0
    ms_metric = ss_metric / df_metric if df_metric > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 1

    # F-statistics
    f_context = ms_context / ms_error if ms_error > 0 else 0
    f_metric = ms_metric / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0

    # P-values (approximation using F-distribution)
    def f_pvalue(f_val, df_num, df_den):
        if df_den <= 0:
            return 1.0
        # Use scipy if available, else return approximation
        try:
            from scipy.stats import f
            return 1 - f.cdf(f_val, df_num, df_den)
        except ImportError:
            # Very rough approximation
            if f_val > 4:
                return 0.01
            elif f_val > 2:
                return 0.05
            return 0.5

    p_context = f_pvalue(f_context, df_context, df_error)
    p_metric = f_pvalue(f_metric, df_metric, df_error)
    p_interaction = f_pvalue(f_interaction, df_interaction, df_error)

    return ANOVAOutput(
        f_statistic=f_interaction,
        p_value=p_interaction,
        df_between=df_interaction,
        df_within=df_error,
        ss_between=ss_interaction,
        ss_within=ss_error,
        ms_between=ms_interaction,
        ms_within=ms_error,
        interaction_p_value=p_interaction
    )


def apply_bonferroni_correction(
    p_values: List[float], alpha: float = 0.05
) -> Tuple[float, List[float]]:
    """
    Apply Bonferroni correction to multiple hypothesis tests.
    
    Returns:
        Tuple of (corrected_alpha, corrected_p_values)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return alpha, []

    corrected_alpha = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]

    return corrected_alpha, corrected_p_values


def compute_effect_size_etasquared(ss_between: float, ss_total: float) -> float:
    """Compute eta-squared effect size."""
    if ss_total == 0:
        return 0.0
    return ss_between / ss_total


def run_anova_analysis(
    results_dir: Path, output_dir: Path, alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run complete ANOVA analysis pipeline.
    
    Args:
        results_dir: Directory containing results CSV files
        output_dir: Directory to save analysis results
        alpha: Significance level
    
    Returns:
        Dictionary with analysis results
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    full_results, limited_results = load_experiment_results(results_dir)

    if not full_results and not limited_results:
        raise ValueError("No results found in %s" % results_dir)

    # Prepare data
    df = prepare_data_for_anova(full_results, limited_results)

    # Compute ANOVA
    anova_result = compute_two_way_anova(df)

    # Apply Bonferroni
    p_values = [anova_result.p_value]
    if anova_result.interaction_p_value is not None:
        p_values.append(anova_result.interaction_p_value)

    corrected_alpha, corrected_p = apply_bonferroni_correction(p_values, alpha)

    # Compute effect size
    ss_total = anova_result.ss_between + anova_result.ss_within
    eta_squared = compute_effect_size_etasquared(
        anova_result.ss_between, ss_total
    )

    # Prepare output
    output = {
        "anova": {
            "f_statistic": anova_result.f_statistic,
            "p_value": anova_result.p_value,
            "interaction_p_value": anova_result.interaction_p_value,
            "df_between": anova_result.df_between,
            "df_within": anova_result.df_within,
        },
        "bonferroni": {
            "original_alpha": alpha,
            "corrected_alpha": corrected_alpha,
            "corrected_p_values": corrected_p,
        },
        "effect_size": {
            "eta_squared": eta_squared,
        },
        "data_summary": {
            "full_games": len(full_results),
            "limited_games": len(limited_results),
            "total_observations": len(df),
        }
    }

    # Save results
    output_path = output_dir / "anova_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info("ANOVA results saved to %s", output_path)

    return output


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for ANOVA analysis."""
    parser = argparse.ArgumentParser(
        description="Run two-way ANOVA on experiment results"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory containing results CSV files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to save analysis results"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for hypothesis tests"
    )
    return parser


def main() -> None:
    """Main entry point for ANOVA analysis."""
    parser = build_parser()
    args = parser.parse_args()

    logger.info("Starting ANOVA analysis")
    logger.info("Results directory: %s", args.results_dir)
    logger.info("Output directory: %s", args.output_dir)

    try:
        results = run_anova_analysis(args.results_dir, args.output_dir, args.alpha)
        logger.info("ANOVA analysis completed successfully")
        logger.info("Interaction p-value: %.6f", results["anova"]["interaction_p_value"])
        logger.info("Bonferroni corrected alpha: %.6f", results["bonferroni"]["corrected_alpha"])

    except Exception as e:
        logger.error("ANOVA analysis failed: %s", e)
        raise


if __name__ == "__main__":
    main()
