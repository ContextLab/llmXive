"""
ANOVA Analysis Module for Social Memory Networks
Implements Two-Way Independent-Samples ANOVA with Bonferroni correction.
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
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ANOVAOutput:
    """Structured output for a single ANOVA test."""
    source: str
    df: float
    sum_sq: float
    mean_sq: float
    f_value: float
    p_value: float
    bonferroni_p_value: Optional[float] = None
    bonferroni_alpha: Optional[float] = None
    significant: Optional[bool] = None

@dataclass
class ANOVAFullResult:
    """Complete ANOVA analysis result including corrections."""
    df_total: int
    df_error: int
    f_statistic: float
    p_value: float
    bonferroni_p_value: float
    bonferroni_alpha: float
    effect_size_eta_squared: float
    significant_at_corrected_alpha: bool
    raw_p_values: Dict[str, float] = field(default_factory=dict)
    corrected_p_values: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def safe_import_statsmodels() -> Optional[Any]:
    """Safely import statsmodels, returning None if unavailable."""
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        return {"sm": sm, "smf": smf}
    except ImportError:
        logger.warning("statsmodels not available. Using manual ANOVA calculation.")
        return None


def load_experiment_results(
    file_path: Union[str, Path],
    expected_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """Load experiment results from CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    df = pd.read_csv(path)

    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing expected columns: {missing}")

    return df


def prepare_data_for_anova(
    full_results_path: Union[str, Path],
    limited_results_path: Union[str, Path]
) -> pd.DataFrame:
    """
    Combine full and limited context results into long format for ANOVA.
    Transforms wide metrics (specialization, retrieval) into long format.
    """
    df_full = load_experiment_results(full_results_path)
    df_limited = load_experiment_results(limited_results_path)

    # Add context condition label
    df_full["context_condition"] = "full"
    df_limited["context_condition"] = "limited"

    # Combine
    df_combined = pd.concat([df_full, df_limited], ignore_index=True)

    # Transform to long format: one row per metric per game
    # We need: game_id, context_condition, metric_name, metric_value
    rows = []
    for _, row in df_combined.iterrows():
        game_id = row.get("game_id")
        context = row["context_condition"]

        # Specialization
        if "specialization_index" in row and not pd.isna(row["specialization_index"]):
            rows.append({
                "game_id": game_id,
                "context_condition": context,
                "metric_name": "specialization",
                "metric_value": row["specialization_index"]
            })

        # Retrieval
        if "retrieval_efficiency" in row and not pd.isna(row["retrieval_efficiency"]):
            rows.append({
                "game_id": game_id,
                "context_condition": context,
                "metric_name": "retrieval",
                "metric_value": row["retrieval_efficiency"]
            })

    df_long = pd.DataFrame(rows)
    return df_long


def compute_effect_size_etasquared(
    ss_effect: float,
    ss_error: float
) -> float:
    """Compute eta-squared effect size."""
    if ss_effect + ss_error == 0:
        return 0.0
    return ss_effect / (ss_effect + ss_error)


def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], float]:
    """
    Apply Bonferroni correction to a list of p-values.
    Returns corrected p-values and the corrected alpha threshold.

    Bonferroni correction:
    - Corrected p-value = min(p * m, 1.0) where m is number of tests
    - Corrected alpha = alpha / m
    """
    m = len(p_values)
    if m == 0:
        return [], alpha

    corrected_alpha = alpha / m
    corrected_p_values = [min(p * m, 1.0) for p in p_values]

    return corrected_p_values, corrected_alpha


def compute_two_way_anova_manual(
    df: pd.DataFrame,
    factor1: str = "context_condition",
    factor2: str = "metric_name",
    response: str = "metric_value"
) -> Dict[str, Any]:
    """
    Compute Two-Way Independent-Samples ANOVA manually.
    Treats both factors as between-subjects (independent) as per FR-006.

    Returns dictionary with SS, df, MS, F, p-values for:
    - Factor 1 main effect
    - Factor 2 main effect
    - Interaction
    - Error
    """
    # Group by both factors
    grouped = df.groupby([factor1, factor2])[response].agg(["mean", "count", "sum"])
    grouped = grouped.reset_index()

    # Calculate grand mean
    grand_mean = df[response].mean()
    n_total = len(df)

    # Calculate sums of squares
    # SS_total
    ss_total = ((df[response] - grand_mean) ** 2).sum()

    # SS_factor1 (main effect of context_condition)
    means_f1 = df.groupby(factor1)[response].mean()
    counts_f1 = df.groupby(factor1).size()
    ss_factor1 = sum(
        counts_f1[f] * (means_f1[f] - grand_mean) ** 2
        for f in means_f1.index
    )

    # SS_factor2 (main effect of metric_name)
    means_f2 = df.groupby(factor2)[response].mean()
    counts_f2 = df.groupby(factor2).size()
    ss_factor2 = sum(
        counts_f2[f] * (means_f2[f] - grand_mean) ** 2
        for f in means_f2.index
    )

    # SS_interaction
    # Calculate cell means and expected means under additivity
    cell_means = df.groupby([factor1, factor2])[response].mean()
    cell_counts = df.groupby([factor1, factor2]).size()

    ss_interaction = 0.0
    for f1 in df[factor1].unique():
        for f2 in df[factor2].unique():
            mask = (df[factor1] == f1) & (df[factor2] == f2)
            n_cell = mask.sum()
            if n_cell > 0:
                cell_mean = cell_means[(f1, f2)]
                main_f1_effect = means_f1[f1] - grand_mean
                main_f2_effect = means_f2[f2] - grand_mean
                interaction_effect = cell_mean - grand_mean - main_f1_effect - main_f2_effect
                ss_interaction += n_cell * (interaction_effect ** 2)

    # SS_error (residual)
    ss_error = ss_total - ss_factor1 - ss_factor2 - ss_interaction
    if ss_error < 0:
        ss_error = 0.0  # Numerical stability

    # Degrees of freedom
    n_f1 = df[factor1].nunique()
    n_f2 = df[factor2].nunique()

    df_factor1 = n_f1 - 1
    df_factor2 = n_f2 - 1
    df_interaction = df_factor1 * df_factor2
    df_error = n_total - (n_f1 * n_f2)
    df_total = n_total - 1

    if df_error <= 0:
        df_error = 1  # Prevent division by zero

    # Mean squares
    ms_factor1 = ss_factor1 / df_factor1 if df_factor1 > 0 else 0
    ms_factor2 = ss_factor2 / df_factor2 if df_factor2 > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 1.0

    # F-statistics
    f_factor1 = ms_factor1 / ms_error if ms_error > 0 else 0
    f_factor2 = ms_factor2 / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0

    # P-values (using scipy if available, else approximation)
    try:
        from scipy import stats
        p_factor1 = 1 - stats.f.cdf(f_factor1, df_factor1, df_error)
        p_factor2 = 1 - stats.f.cdf(f_factor2, df_factor2, df_error)
        p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)
    except ImportError:
        # Fallback: use a simple approximation or return 1.0
        logger.warning("scipy not available. Using p-value approximation.")
        p_factor1 = 1.0 / (1.0 + f_factor1)
        p_factor2 = 1.0 / (1.0 + f_factor2)
        p_interaction = 1.0 / (1.0 + f_interaction)

    return {
        "ss_factor1": ss_factor1,
        "df_factor1": df_factor1,
        "ms_factor1": ms_factor1,
        "f_factor1": f_factor1,
        "p_factor1": p_factor1,

        "ss_factor2": ss_factor2,
        "df_factor2": df_factor2,
        "ms_factor2": ms_factor2,
        "f_factor2": f_factor2,
        "p_factor2": p_factor2,

        "ss_interaction": ss_interaction,
        "df_interaction": df_interaction,
        "ms_interaction": ms_interaction,
        "f_interaction": f_interaction,
        "p_interaction": p_interaction,

        "ss_error": ss_error,
        "df_error": df_error,
        "ms_error": ms_error,

        "ss_total": ss_total,
        "df_total": df_total
    }


def run_anova_analysis(
    full_results_path: Union[str, Path],
    limited_results_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    alpha: float = 0.05
) -> ANOVAFullResult:
    """
    Run full ANOVA analysis with Bonferroni correction.

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv
        output_path: Optional path to write JSON results
        alpha: Significance level for correction
    """
    # Prepare data
    df = prepare_data_for_anova(full_results_path, limited_results_path)

    # Run ANOVA
    results = compute_two_way_anova_manual(df)

    # Collect p-values for correction
    p_values = [
        results["p_factor1"],   # Context main effect
        results["p_factor2"],   # Metric main effect
        results["p_interaction"] # Interaction
    ]

    # Apply Bonferroni correction
    corrected_p_values, corrected_alpha = apply_bonferroni_correction(p_values, alpha)

    # Map corrected p-values back
    results["p_factor1_corrected"] = corrected_p_values[0]
    results["p_factor2_corrected"] = corrected_p_values[1]
    results["p_interaction_corrected"] = corrected_p_values[2]

    # Compute effect sizes
    eta_sq_factor1 = compute_effect_size_etasquared(
        results["ss_factor1"], results["ss_error"]
    )
    eta_sq_factor2 = compute_effect_size_etasquared(
        results["ss_factor2"], results["ss_error"]
    )
    eta_sq_interaction = compute_effect_size_etasquared(
        results["ss_interaction"], results["ss_error"]
    )

    # Determine significance at corrected alpha
    sig_interaction = results["p_interaction_corrected"] < corrected_alpha

    # Build output object
    full_result = ANOVAFullResult(
        df_total=results["df_total"],
        df_error=results["df_error"],
        f_statistic=results["f_interaction"],
        p_value=results["p_interaction"],
        bonferroni_p_value=results["p_interaction_corrected"],
        bonferroni_alpha=corrected_alpha,
        effect_size_eta_squared=eta_sq_interaction,
        significant_at_corrected_alpha=sig_interaction,
        raw_p_values={
            "context_main": results["p_factor1"],
            "metric_main": results["p_factor2"],
            "interaction": results["p_interaction"]
        },
        corrected_p_values={
            "context_main": results["p_factor1_corrected"],
            "metric_main": results["p_factor2_corrected"],
            "interaction": results["p_interaction_corrected"]
        }
    )

    # Write output if requested
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({
                "df_total": full_result.df_total,
                "df_error": full_result.df_error,
                "f_statistic": full_result.f_statistic,
                "p_value": full_result.p_value,
                "bonferroni_p_value": full_result.bonferroni_p_value,
                "bonferroni_alpha": full_result.bonferroni_alpha,
                "effect_size_eta_squared": full_result.effect_size_eta_squared,
                "significant_at_corrected_alpha": full_result.significant_at_corrected_alpha,
                "raw_p_values": full_result.raw_p_values,
                "corrected_p_values": full_result.corrected_p_values
            }, f, indent=2)
        logger.info(f"ANOVA results written to {output_path}")

    return full_result


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Run Two-Way ANOVA with Bonferroni correction on experiment results."
    )
    parser.add_argument(
        "--full-results",
        type=str,
        required=True,
        help="Path to results_full.csv"
    )
    parser.add_argument(
        "--limited-results",
        type=str,
        required=True,
        help="Path to results_limited.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/anova_results.json",
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for Bonferroni correction"
    )
    return parser


def main() -> None:
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = run_anova_analysis(
            full_results_path=args.full_results,
            limited_results_path=args.limited_results,
            output_path=args.output,
            alpha=args.alpha
        )

        print(f"ANOVA Analysis Complete")
        print(f"  Interaction F-statistic: {result.f_statistic:.4f}")
        print(f"  Raw p-value: {result.p_value:.4f}")
        print(f"  Bonferroni-corrected p-value: {result.bonferroni_p_value:.4f}")
        print(f"  Corrected alpha (Bonferroni): {result.bonferroni_alpha:.4f}")
        print(f"  Significant at corrected alpha: {result.significant_at_corrected_alpha}")
        print(f"  Effect size (eta-squared): {result.effect_size_eta_squared:.4f}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running ANOVA: {e}")
        raise


if __name__ == "__main__":
    main()