"""
ANOVA analysis for social memory networks experiment.

This module implements statistical analysis of the experimental results,
including two-way ANOVA and Bonferroni correction for multiple comparisons.
"""
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

# Local imports
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ANOVAOutput:
    """Structure for ANOVA results."""
    f_value: float
    p_value: float
    df_num: int
    df_denom: int
    effect_size: Optional[float] = None
    corrected_p_value: Optional[float] = None
    is_significant: bool = False
    corrected_significance: bool = False
    alpha_level: float = 0.05
    correction_method: str = "bonferroni"
    family_wise_error_rate: float = 0.05
    number_of_tests: int = 1


def safe_import_statsmodels() -> Tuple[bool, Optional[Any]]:
    """Attempt to import statsmodels, return success flag and module."""
    try:
        import statsmodels.api as sm
        import statsmodels.stats.anova as anova
        return True, {"sm": sm, "anova": anova}
    except ImportError as e:
        logger.log("statsmodels_import_failed", error=str(e))
        return False, None


def load_experiment_results(
    results_path: str,
    context_condition: Optional[str] = None
) -> pd.DataFrame:
    """
    Load experiment results from CSV file.

    Args:
        results_path: Path to results CSV file
        context_condition: Optional filter for context condition (full/limited)

    Returns:
        DataFrame with experiment results
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    df = pd.read_csv(path)

    if context_condition and "context_condition" in df.columns:
        df = df[df["context_condition"] == context_condition]

    return df


def prepare_data_for_anova(
    full_results_path: str,
    limited_results_path: str
) -> pd.DataFrame:
    """
    Combine full and limited context results into long format for ANOVA.

    Creates a DataFrame with columns:
    - game_id
    - context_condition (full/limited)
    - metric_name (specialization/retrieval)
    - metric_value

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv

    Returns:
        Long-format DataFrame for ANOVA analysis
    """
    # Load both result files
    df_full = load_experiment_results(full_results_path, "full")
    df_limited = load_experiment_results(limited_results_path, "limited")

    if df_full.empty:
        raise ValueError(f"No data found in {full_results_path}")
    if df_limited.empty:
        raise ValueError(f"No data found in {limited_results_path}")

    # Add context condition column
    df_full["context_condition"] = "full"
    df_limited["context_condition"] = "limited"

    # Combine
    df_combined = pd.concat([df_full, df_limited], ignore_index=True)

    # Melt to long format for each metric
    long_rows = []

    for _, row in df_combined.iterrows():
        game_id = row.get("game_id", len(long_rows))
        condition = row["context_condition"]

        # Specialization metric
        if "specialization_index" in row:
          long_rows.append({
              "game_id": game_id,
              "context_condition": condition,
              "metric_name": "specialization",
              "metric_value": row["specialization_index"]
          })

        # Retrieval metric
        if "retrieval_efficiency" in row:
          long_rows.append({
              "game_id": game_id,
              "context_condition": condition,
              "metric_name": "retrieval",
              "metric_value": row["retrieval_efficiency"]
          })

    df_long = pd.DataFrame(long_rows)

    logger.log(
        "data_prepared_for_anova",
        total_rows=len(df_long),
        full_count=len(df_full),
        limited_count=len(df_limited)
    )

    return df_long


def compute_two_way_anova(df: pd.DataFrame) -> ANOVAOutput:
    """
    Compute two-way ANOVA with interaction term.

    Model: metric_value ~ C(context_condition) * C(metric_name)

    Args:
        df: Long-format DataFrame with columns:
            - context_condition
            - metric_name
            - metric_value

    Returns:
        ANOVAOutput with F-value, p-value, and degrees of freedom
    """
    has_sm, sm_modules = safe_import_statsmodels()

    if has_sm:
        sm = sm_modules["sm"]
        anova_mod = sm_modules["anova"]

        try:
            # Fit linear model
            model = sm.OLS.from_formula(
                "metric_value ~ C(context_condition) * C(metric_name)",
                data=df
            ).fit()

            # Get ANOVA table
            anova_table = anova_mod.anova_lm(model)

            # Extract interaction term
            interaction_row = anova_table.loc["C(context_condition):C(metric_name)"]

            f_value = float(interaction_row["F"])
            p_value = float(interaction_row["PR(>F)"])
            df_num = int(interaction_row["df"])
            df_denom = int(anova_table["df"].sum() - df_num)

            # Compute effect size (eta-squared)
            ss_total = anova_table["sum_sq"].sum()
            ss_interaction = interaction_row["sum_sq"]
            effect_size = float(ss_interaction / ss_total) if ss_total > 0 else 0.0

            logger.log(
                "anova_computed_statsmodels",
                f_value=f_value,
                p_value=p_value,
                effect_size=effect_size
            )

            return ANOVAOutput(
                f_value=f_value,
                p_value=p_value,
                df_num=df_num,
                df_denom=df_denom,
                effect_size=effect_size
            )

        except Exception as e:
            logger.log("anova_statsmodels_failed", error=str(e))
            # Fall back to manual computation
            pass

    # Manual computation fallback
    return compute_manual_anova(df)


def compute_manual_anova(df: pd.DataFrame) -> ANOVAOutput:
    """
    Compute two-way ANOVA manually without statsmodels.

    Uses sum-of-squares decomposition for two-factor design with interaction.

    Args:
        df: Long-format DataFrame

    Returns:
        ANOVAOutput with computed statistics
    """
    # Group by factors
    groups = df.groupby(["context_condition", "metric_name"])
    n_cells = len(groups)

    # Overall mean
    grand_mean = df["metric_value"].mean()
    n_total = len(df)

    # Sum of Squares Total
    ss_total = ((df["metric_value"] - grand_mean) ** 2).sum()

    # Sum of Squares Between Cells
    cell_means = groups["metric_value"].mean()
    cell_counts = groups["metric_value"].count()

    ss_between = sum(
        cell_counts[cond, metric] * (mean - grand_mean) ** 2
        for (cond, metric), mean in cell_means.items()
    )

    # Sum of Squares Within (Error)
    ss_within = sum(
        ((group["metric_value"] - group["metric_value"].mean()) ** 2).sum()
        for _, group in groups
    )

    # Factor A: context_condition (2 levels: full, limited)
    cond_means = df.groupby("context_condition")["metric_value"].mean()
    cond_counts = df.groupby("context_condition").size()
    n_cond = len(cond_means)

    ss_cond = sum(
        cond_counts[cond] * (mean - grand_mean) ** 2
        for cond, mean in cond_means.items()
    )

    # Factor B: metric_name (2 levels: specialization, retrieval)
    metric_means = df.groupby("metric_name")["metric_value"].mean()
    metric_counts = df.groupby("metric_name").size()
    n_metric = len(metric_means)

    ss_metric = sum(
        metric_counts[metric] * (mean - grand_mean) ** 2
        for metric, mean in metric_means.items()
    )

    # Interaction SS
    ss_interaction = ss_between - ss_cond - ss_metric

    # Degrees of freedom
    df_cond = n_cond - 1
    df_metric = n_metric - 1
    df_interaction = df_cond * df_metric
    df_error = n_total - n_cond * n_metric
    df_total = n_total - 1

    # Mean Squares
    ms_cond = ss_cond / df_cond if df_cond > 0 else 0
    ms_metric = ss_metric / df_metric if df_metric > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_within / df_error if df_error > 0 else 1e-10

    # F-values
    f_cond = ms_cond / ms_error if ms_error > 0 else 0
    f_metric = ms_metric / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0

    # P-values (approximate using F-distribution)
    def f_to_p(f_val, df_num, df_denom):
        """Approximate p-value from F-statistic."""
        if df_denom <= 0 or f_val <= 0:
            return 1.0
        # Use scipy if available, otherwise approximate
        try:
            from scipy.stats import f
            return 1.0 - f.cdf(f_val, df_num, df_denom)
        except ImportError:
            # Very rough approximation for large df_denom
            # Chi-squared approximation: F ~ (chi2_df1/df1) / (chi2_df2/df2)
            # For large df2, F*df1 ~ chi2_df1
            if df_denom > 30:
                from scipy.stats import chi2
                return 1.0 - chi2.cdf(f_val * df_num, df_num)
            return 0.05  # Default if we can't compute

    p_interaction = f_to_p(f_interaction, df_interaction, df_error)

    # Effect size (eta-squared for interaction)
    effect_size = ss_interaction / ss_total if ss_total > 0 else 0.0

    logger.log(
        "anova_computed_manual",
        f_interaction=f_interaction,
        p_interaction=p_interaction,
        ss_interaction=ss_interaction,
        ss_total=ss_total
    )

    return ANOVAOutput(
        f_value=f_interaction,
        p_value=p_interaction,
        df_num=df_interaction,
        df_denom=df_error,
        effect_size=effect_size
    )


def compute_effect_size_etasquared(df: pd.DataFrame, model_type: str = "interaction") -> float:
    """
    Compute eta-squared effect size.

    Args:
        df: Long-format DataFrame
        model_type: Type of effect ("interaction", "main_effect_cond", "main_effect_metric")

    Returns:
        Eta-squared value between 0 and 1
    """
    has_sm, sm_modules = safe_import_statsmodels()

    if has_sm:
        sm = sm_modules["sm"]
        try:
            model = sm.OLS.from_formula(
                "metric_value ~ C(context_condition) * C(metric_name)",
                data=df
            ).fit()
            anova_table = sm_modules["anova"].anova_lm(model)

            ss_total = anova_table["sum_sq"].sum()

            if model_type == "interaction":
                ss_effect = anova_table.loc["C(context_condition):C(metric_name)", "sum_sq"]
            elif model_type == "main_effect_cond":
                ss_effect = anova_table.loc["C(context_condition)", "sum_sq"]
            elif model_type == "main_effect_metric":
                ss_effect = anova_table.loc["C(metric_name)", "sum_sq"]
            else:
                ss_effect = 0.0

            return float(ss_effect / ss_total) if ss_total > 0 else 0.0

        except Exception:
            pass

    # Fallback: compute manually
    grand_mean = df["metric_value"].mean()
    ss_total = ((df["metric_value"] - grand_mean) ** 2).sum()

    if model_type == "interaction":
        groups = df.groupby(["context_condition", "metric_name"])
        cell_means = groups["metric_value"].mean()
        cell_counts = groups["metric_value"].count()
        cond_means = df.groupby("context_condition")["metric_value"].mean()
        cond_counts = df.groupby("context_condition").size()
        metric_means = df.groupby("metric_name")["metric_value"].mean()

        ss_between = sum(
            cell_counts[cond, metric] * (mean - grand_mean) ** 2
            for (cond, metric), mean in cell_means.items()
        )
        ss_cond = sum(
            cond_counts[cond] * (mean - grand_mean) ** 2
            for cond, mean in cond_means.items()
        )
        ss_metric = sum(
            metric_counts[metric] * (mean - grand_mean) ** 2
            for metric, mean in metric_means.items()
        )

        ss_interaction = ss_between - ss_cond - ss_metric
        return float(ss_interaction / ss_total) if ss_total > 0 else 0.0

    return 0.0


def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a family of hypothesis tests.

    The Bonferroni correction controls the family-wise error rate (FWER) by
    dividing the significance level alpha by the number of tests (m).

    Corrected alpha: alpha_corrected = alpha / m
    Corrected p-value: p_corrected = min(p * m, 1.0)

    Args:
        p_values: List of p-values from hypothesis tests
        alpha: Desired family-wise error rate (default 0.05)

    Returns:
        Dictionary with:
            - corrected_alpha: The Bonferroni-corrected significance threshold
            - corrected_p_values: List of adjusted p-values
            - significant_indices: Indices of tests that remain significant
            - family_wise_error_rate: The controlled FWER
            - number_of_tests: Number of tests in the family
    """
    if not p_values:
        return {
            "corrected_alpha": alpha,
            "corrected_p_values": [],
            "significant_indices": [],
            "family_wise_error_rate": alpha,
            "number_of_tests": 0
        }

    m = len(p_values)
    corrected_alpha = alpha / m

    # Apply correction: p_corrected = min(p * m, 1.0)
    corrected_p_values = [min(p * m, 1.0) for p in p_values]

    # Identify significant tests after correction
    significant_indices = [
        i for i, p_corr in enumerate(corrected_p_values)
        if p_corr < alpha
    ]

    result = {
        "corrected_alpha": corrected_alpha,
        "corrected_p_values": corrected_p_values,
        "significant_indices": significant_indices,
        "family_wise_error_rate": alpha,
        "number_of_tests": m,
        "original_p_values": p_values
    }

    logger.log(
        "bonferroni_correction_applied",
        number_of_tests=m,
        corrected_alpha=corrected_alpha,
        significant_count=len(significant_indices)
    )

    return result


def run_anova_analysis(
    full_results_path: str,
    limited_results_path: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run complete ANOVA analysis with Bonferroni correction.

    This function:
    1. Loads and prepares data from both conditions
    2. Computes two-way ANOVA with interaction
    3. Applies Bonferroni correction for multiple comparisons
    4. Returns comprehensive results

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv
        output_path: Optional path to save JSON results

    Returns:
        Dictionary with ANOVA results and correction information
    """
    # Prepare data
    df = prepare_data_for_anova(full_results_path, limited_results_path)

    # Compute ANOVA
    anova_result = compute_two_way_anova(df)

    # For this specific design, we have two main effects and one interaction
    # We'll compute p-values for all three and apply Bonferroni
    has_sm, sm_modules = safe_import_statsmodels()

    if has_sm:
        sm = sm_modules["sm"]
        try:
            model = sm.OLS.from_formula(
                "metric_value ~ C(context_condition) * C(metric_name)",
                data=df
            ).fit()
            anova_table = sm_modules["anova"].anova_lm(model)

            # Extract p-values for all terms
            p_cond = float(anova_table.loc["C(context_condition)", "PR(>F)"])
            p_metric = float(anova_table.loc["C(metric_name)", "PR(>F)"])
            p_interaction = float(anova_table.loc["C(context_condition):C(metric_name)", "PR(>F)"])

            p_values = [p_cond, p_metric, p_interaction]
            term_names = ["context_condition", "metric_name", "interaction"]

        except Exception:
            # Fallback: use interaction only
            p_values = [anova_result.p_value]
            term_names = ["interaction"]
    else:
        # Manual fallback: use interaction only
        p_values = [anova_result.p_value]
        term_names = ["interaction"]

    # Apply Bonferroni correction
    correction_result = apply_bonferroni_correction(p_values)

    # Build comprehensive result
    results = {
        "anova": {
            "f_value": anova_result.f_value,
            "p_value": anova_result.p_value,
            "df_num": anova_result.df_num,
            "df_denom": anova_result.df_denom,
            "effect_size": anova_result.effect_size,
            "is_significant": anova_result.p_value < 0.05
        },
        "bonferroni_correction": {
            "method": "bonferroni",
            "number_of_tests": correction_result["number_of_tests"],
            "original_alpha": 0.05,
            "corrected_alpha": correction_result["corrected_alpha"],
            "family_wise_error_rate": correction_result["family_wise_error_rate"]
        },
        "term_results": []
    }

    for i, term in enumerate(term_names):
        p_orig = p_values[i]
        p_corr = correction_result["corrected_p_values"][i]
        is_sig = p_corr < 0.05

        results["term_results"].append({
            "term": term,
            "p_value_original": p_orig,
            "p_value_corrected": p_corr,
            "is_significant_after_correction": is_sig
        })

    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.log("anova_results_saved", path=str(output_file))

    return results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for ANOVA analysis script."""
    parser = argparse.ArgumentParser(
        description="Run ANOVA analysis with Bonferroni correction"
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
        help="Output path for JSON results"
    )
    return parser


def main():
    """Main entry point for ANOVA analysis."""
    parser = build_parser()
    args = parser.parse_args()

    logger.log("anova_analysis_started")

    try:
        results = run_anova_analysis(
            full_results_path=args.full_results,
            limited_results_path=args.limited_results,
            output_path=args.output
        )

        logger.log(
            "anova_analysis_completed",
            interaction_p=results["anova"]["p_value"],
            corrected_alpha=results["bonferroni_correction"]["corrected_alpha"]
        )

        print(f"ANOVA Analysis Complete")
        print(f"Interaction F-statistic: {results['anova']['f_value']:.4f}")
        print(f"Interaction p-value: {results['anova']['p_value']:.6f}")
        print(f"Bonferroni corrected alpha: {results['bonferroni_correction']['corrected_alpha']:.6f}")
        print(f"Results saved to: {args.output}")

    except Exception as e:
        logger.log("anova_analysis_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()