"""
Two-way ANOVA analysis for Social Memory Networks experiment.

Implements a two-way independent-samples ANOVA to test the interaction
between context condition and metric type on performance metrics.
"""
from __future__ import annotations

import json
import math
import os
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Safe import of statsmodels
def safe_import_statsmodels():
    """Attempt to import statsmodels; return module or None with warning."""
    try:
        import statsmodels.api as sm
        from statsmodels.stats.anova import anova_lm
        from statsmodels.formula.api import ols
        return sm, anova_lm, ols
    except ImportError as e:
        warnings.warn(f"statsmodels not available: {e}. ANOVA analysis skipped.")
        return None, None, None

@dataclass
class TwoWayANOVAResult:
    """Container for two-way ANOVA results."""
    source: str
    df: float
    sum_sq: float
    mean_sq: float
    F: float
    PR_gt_F: float
    eta_squared: Optional[float] = None

@dataclass
class ANOVAOutput:
    """Full ANOVA analysis output."""
    summary: List[Dict[str, Any]]
    interaction_p_value: float
    main_effect_context_p: float
    main_effect_metric_p: float
    interaction_f: float
    model_formula: str
    n_observations: int
    bonferroni_corrected_alpha: Optional[float] = None
    significant_after_correction: bool = False

def compute_effect_size_etasquared(sum_sq: float, total_sum_sq: float) -> float:
    """Compute eta-squared effect size."""
    if total_sum_sq == 0:
        return 0.0
    return sum_sq / total_sum_sq

def load_experiment_results(results_dir: str) -> pd.DataFrame:
    """
    Load and combine results_full.csv and results_limited.csv into a long-format DataFrame.

    Expected columns in CSVs:
      game_id, specialization_index, retrieval_efficiency, context_condition, agent_count

    Returns a DataFrame with columns:
      game_id, context_condition, metric_name, metric_value
    """
    results_path = Path(results_dir)
    full_csv = results_path / "results_full.csv"
    limited_csv = results_path / "results_limited.csv"

    dfs = []

    if full_csv.exists():
        df_full = pd.read_csv(full_csv)
        df_full["context_condition"] = "full"
        dfs.append(df_full)

    if limited_csv.exists():
        df_limited = pd.read_csv(limited_csv)
        df_limited["context_condition"] = "limited"
        dfs.append(df_limited)

    if not dfs:
        raise FileNotFoundError(
            f"No result files found in {results_dir}. Expected results_full.csv and/or results_limited.csv."
        )

    combined = pd.concat(dfs, ignore_index=True)

    # Reshape to long format
    metric_cols = ["specialization_index", "retrieval_efficiency"]
    available_cols = [c for c in metric_cols if c in combined.columns]

    if not available_cols:
        raise ValueError(
            f"Expected metric columns {metric_cols} not found in data. "
            f"Available columns: {combined.columns.tolist()}"
        )

    long_df = combined.melt(
        id_vars=["game_id", "context_condition", "agent_count"],
        value_vars=available_cols,
        var_name="metric_name",
        value_name="metric_value"
    )

    # Drop NaNs
    long_df = long_df.dropna(subset=["metric_value"])

    return long_df

def prepare_data_for_anova(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for ANOVA: ensure numeric types, handle outliers, check assumptions.

    Returns cleaned DataFrame ready for modeling.
    """
    df = df.copy()
    df["metric_value"] = pd.to_numeric(df["metric_value"], errors="coerce")
    df = df.dropna(subset=["metric_value"])

    # Log transform if highly skewed (optional, but good practice)
    # For now, we use raw values as per spec
    return df

def compute_two_way_anova(df: pd.DataFrame, model_formula: str = None) -> Tuple[Optional[Any], List[TwoWayANOVAResult], float, float, float]:
    """
    Compute two-way ANOVA using statsmodels.

    Args:
        df: Long-format DataFrame with columns: context_condition, metric_name, metric_value
        model_formula: Optional formula string. Defaults to 'metric_value ~ C(context_condition) * C(metric_name)'

    Returns:
        (anova_table, result_list, interaction_p, context_p, metric_p)
    """
    if model_formula is None:
        model_formula = "metric_value ~ C(context_condition) * C(metric_name)"

    sm, anova_lm, ols = safe_import_statsmodels()
    if sm is None:
        raise ImportError("statsmodels is required for ANOVA analysis. Install with: pip install statsmodels")

    try:
        model = ols(model_formula, data=df)
        anova_table = anova_lm(model, typ=2)
    except Exception as e:
        raise RuntimeError(f"ANOVA model fitting failed: {e}")

    # Extract p-values
    interaction_term = "C(context_condition):C(metric_name)"
    context_term = "C(context_condition)"
    metric_term = "C(metric_name)"

    interaction_p = anova_table.loc[interaction_term, "PR > F"] if interaction_term in anova_table.index else np.nan
    context_p = anova_table.loc[context_term, "PR > F"] if context_term in anova_table.index else np.nan
    metric_p = anova_table.loc[metric_term, "PR > F"] if metric_term in anova_table.index else np.nan

    # Build result list
    result_list = []
    for idx, row in anova_table.iterrows():
        result_list.append(TwoWayANOVAResult(
            source=str(idx),
            df=row["df"],
            sum_sq=row["sum_sq"],
            mean_sq=row["mean_sq"],
            F=row["F"],
            PR_gt_F=row["PR > F"],
            eta_squared=compute_effect_size_etasquared(row["sum_sq"], anova_table["sum_sq"].sum())
        ))

    return anova_table, result_list, interaction_p, context_p, metric_p

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[float, List[float]]:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of raw p-values
        alpha: Family-wise error rate (default 0.05)

    Returns:
        (corrected_alpha, corrected_p_values)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return alpha, []

    corrected_alpha = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]

    return corrected_alpha, corrected_p_values

def run_anova_analysis(results_dir: str, output_path: Optional[str] = None, alpha: float = 0.05) -> ANOVAOutput:
    """
    Run the full two-way ANOVA analysis pipeline.

    Args:
        results_dir: Path to directory containing results_full.csv and results_limited.csv
        output_path: Optional path to write JSON results
        alpha: Significance level for Bonferroni correction

    Returns:
        ANOVAOutput object with results
    """
    df = load_experiment_results(results_dir)
    df = prepare_data_for_anova(df)

    if len(df) < 4:
        raise ValueError("Insufficient data for ANOVA (need at least 4 observations).")

    anova_table, results, interaction_p, context_p, metric_p = compute_two_way_anova(df)

    # Bonferroni correction for the three main tests
    p_values = [interaction_p, context_p, metric_p]
    corrected_alpha, corrected_p_values = apply_bonferroni_correction(p_values, alpha)

    summary = [
        {
            "source": r.source,
            "df": r.df,
            "sum_sq": r.sum_sq,
            "mean_sq": r.mean_sq,
            "F": r.F,
            "p_value": r.PR_gt_F,
            "eta_squared": r.eta_squared
        }
        for r in results
    ]

    # Determine significance after correction
    interaction_sig = corrected_p_values[0] < alpha if not np.isnan(corrected_p_values[0]) else False

    output = ANOVAOutput(
        summary=summary,
        interaction_p_value=interaction_p,
        main_effect_context_p=context_p,
        main_effect_metric_p=metric_p,
        interaction_f=next((r.F for r in results if r.source == "C(context_condition):C(metric_name)"), np.nan),
        model_formula="metric_value ~ C(context_condition) * C(metric_name)",
        n_observations=len(df),
        bonferroni_corrected_alpha=corrected_alpha,
        significant_after_correction=interaction_sig
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({
                "summary": output.summary,
                "interaction_p_value": output.interaction_p_value,
                "main_effect_context_p": output.main_effect_context_p,
                "main_effect_metric_p": output.main_effect_metric_p,
                "interaction_f": output.interaction_f,
                "model_formula": output.model_formula,
                "n_observations": output.n_observations,
                "bonferroni_corrected_alpha": output.bonferroni_corrected_alpha,
                "significant_after_correction": output.significant_after_correction
            }, f, indent=2)

    return output

def build_parser() -> Any:
    """Build argument parser for CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Run two-way ANOVA on social memory network results.")
    parser.add_argument("--results-dir", type=str, default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
                      help="Directory containing results_full.csv and results_limited.csv")
    parser.add_argument("--output", type=str, default=None,
                      help="Path to write JSON results (default: stdout)")
    parser.add_argument("--alpha", type=float, default=0.05,
                      help="Significance level for Bonferroni correction (default: 0.05)")
    return parser

def main() -> None:
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = run_anova_analysis(args.results_dir, args.output, args.alpha)
        if not args.output:
            print(json.dumps({
                "interaction_p_value": result.interaction_p_value,
                "main_effect_context_p": result.main_effect_context_p,
                "main_effect_metric_p": result.main_effect_metric_p,
                "interaction_f": result.interaction_f,
                "model_formula": result.model_formula,
                "n_observations": result.n_observations,
                "bonferroni_corrected_alpha": result.bonferroni_corrected_alpha,
                "significant_after_correction": result.significant_after_correction
            }, indent=2))
    except Exception as e:
        print(f"ANOVA analysis failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()