"""Statistical analysis for fidelity metrics (Task T010).

This script reads the fidelity metrics CSV, performs normality testing on
paired differences for each primary metric (intent precision,
surface precision, hallucination rate), selects either a Friedman test
(non‑parametric) or a repeated‑measures ANOVA (parametric), applies a
Holm‑Bonferroni correction across the three metrics, computes the
appropriate effect size (Kendall's W for Friedman, η² for ANOVA), and
propagates the ``exploratory`` flag from ``results/power_report.md``.
The final JSON report is written to ``results/statistics.json`` with the
required keys:

- ``p_values``: mapping metric → raw p‑value (or ``null`` if not computable)
- ``significant``: mapping metric → boolean indicating significance after
  Holm‑Bonferroni correction (``false`` if p‑value is ``null``)
- ``effect_sizes``: mapping metric → effect‑size value (Kendall's W or η²,
  ``null`` if not computable)
- ``exploratory``: boolean taken from the power‑analysis report
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import scipy.stats as stats
from llmxive_toolkit import get_logger, paths
from statsmodels.stats.anova import AnovaRM

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _read_exploratory_flag() -> bool:
    """Parse ``results/power_report.md`` and return the exploratory flag."""
    report_path = paths.results("power_report.md")
    if not report_path.is_file():
        log.warning("Power report not found at %s – assuming exploratory=True", report_path)
        return True
    text = report_path.read_text(encoding="utf-8")
    # Look for a line like ``- exploratory: true`` (case‑insensitive)
    match = re.search(r"-\s*exploratory:\s*(true|false)", text, re.IGNORECASE)
    if match:
        return match.group(1).lower() == "true"
    # Fallback – older format may contain ``exploratory: true`` without dash
    match = re.search(r"exploratory:\s*(true|false)", text, re.IGNORECASE)
    if match:
        return match.group(1).lower() == "true"
    log.warning("Could not locate exploratory flag in power report – defaulting to True")
    return True

def _load_fidelity_metrics() -> pd.DataFrame:
    """Load ``data/processed/fidelity_metrics.csv`` as a DataFrame."""
    csv_path = paths.data("processed", "fidelity_metrics.csv")
    if not csv_path.is_file():
        log.error("Fidelity metrics file not found at %s", csv_path)
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(csv_path, dtype=str)
    # Convert numeric columns to float where possible
    numeric_cols = [
        "precision_intent",
        "recall_intent",
        "precision_surface",
        "recall_surface",
        "hallucination_rate",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def _pivot_metric(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Return a wide DataFrame: rows = commit_hash, columns = model_id, values = metric."""
    required = {"commit_hash", "model_id", metric}
    if not required.issubset(df.columns):
        raise KeyError(f"Missing columns for metric '{metric}': {required - set(df.columns)}")
    pivot = df.pivot(index="commit_hash", columns="model_id", values=metric)
    # Drop commits where any model is missing (cannot perform within‑subject test)
    pivot = pivot.dropna()
    return pivot

def _shapiro_on_differences(pivot: pd.DataFrame) -> float:
    """Perform Shapiro‑Wilk on the differences between the first two models.

    Returns the p‑value. If there are fewer than 2 models, returns 1.0.
    """
    if pivot.shape[1] < 2:
        return 1.0
    # Compute pairwise differences (model0 - model1)
    diff = pivot.iloc[:, 0] - pivot.iloc[:, 1]
    # Remove NaNs just in case
    diff = diff.dropna()
    if len(diff) < 3:  # Shapiro requires at least 3 observations
        return 1.0
    stat, p = stats.shapiro(diff)
    return p

def _friedman_test(pivot: pd.DataFrame) -> Tuple[float, float]:
    """Run Friedman chi‑square test on the wide pivot.

    Returns (statistic, p‑value). If insufficient data, returns (nan, nan).
    """
    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        return float("nan"), float("nan")
    args = [pivot[col].values for col in pivot.columns]
    stat, p = stats.friedmanchisquare(*args)
    return stat, p

def _kendalls_w(pivot: pd.DataFrame, friedman_stat: float) -> float:
    """Convert Friedman chi‑square statistic to Kendall's W.

    W = χ² / (n * (k‑1)), where n = number of subjects, k = number of treatments.
    """
    n = pivot.shape[0]
    k = pivot.shape[1]
    if n == 0 or k <= 1:
        return float("nan")
    return friedman_stat / (n * (k - 1))

def _repeated_measures_anova(pivot: pd.DataFrame, metric_name: str) -> Tuple[float, float]:
    """Perform repeated‑measures ANOVA using statsmodels.

    Returns (F statistic, p‑value). If insufficient data, returns (nan, nan).
    """
    if pivot.shape[0] < 2 or pivot.shape[1] < 2:
        return float("nan"), float("nan")
    # Convert to long format required by AnovaRM
    df_long = pivot.reset_index().melt(id_vars="commit_hash", var_name="model_id", value_name=metric_name)
    anova = AnovaRM(df_long, depvar=metric_name, subject="commit_hash", within=["model_id"])
    try:
        res = anova.fit()
    except Exception as e:
        log.error("ANOVA failed for metric %s: %s", metric_name, e)
        return float("nan"), float("nan")
    # statsmodels returns a table with columns: 'F Value', 'Pr > F'
    f_val = res.anova_table.loc["model_id", "F Value"]
    p_val = res.anova_table.loc["model_id", "Pr > F"]
    return float(f_val), float(p_val)

def _eta_squared_anova(pivot: pd.DataFrame, anova_f: float) -> float:
    """Compute η² from ANOVA F statistic.

    η² = SS_effect / SS_total.
    For repeated measures with equal group sizes, an approximation:
    η² = (F * (k - 1)) / (F * (k - 1) + (n - 1))
    where k = number of treatments, n = number of subjects.
    """
    n = pivot.shape[0]
    k = pivot.shape[1]
    if n == 0 or k <= 1:
        return float("nan")
    numerator = anova_f * (k - 1)
    denominator = numerator + (n - 1)
    return numerator / denominator if denominator != 0 else float("nan")

def _holm_bonferroni(p_vals: List[float]) -> List[bool]:
    """Apply Holm‑Bonferroni correction to a list of p‑values.

    Returns a list of booleans indicating significance after correction
    (α = 0.05). ``None`` or ``nan`` values are treated as non‑significant.
    """
    alpha = 0.05
    # Pair each p‑value with its original index
    indexed = [(i, p) for i, p in enumerate(p_vals)]
    # Sort by p‑value (ignoring NaNs)
    sorted_idx = sorted(indexed, key=lambda x: (float("inf") if pd.isna(x[1]) else x[1]))
    m = len(p_vals)
    significant = [False] * m
    for rank, (orig_i, p) in enumerate(sorted_idx, start=1):
        if pd.isna(p):
            continue
        crit = alpha / (m - rank + 1)
        if p <= crit:
            significant[orig_i] = True
    return significant

# ----------------------------------------------------------------------
# Main analysis function
# ----------------------------------------------------------------------
def run_statistical_analysis() -> Dict:
    """Execute the full statistical analysis pipeline.

    Returns a dictionary that mirrors the JSON output written to
    ``results/statistics.json``.
    """
    # 1. Load data
    df = _load_fidelity_metrics()
    if df.empty:
        log.warning("Fidelity metrics CSV is empty – producing placeholder results.")
    # Metrics we care about
    metric_names = {
        "precision_intent": "precision_intent",
        "precision_surface": "precision_surface",
        "hallucination_rate": "hallucination_rate",
    }

    # Containers for results
    raw_p_values: Dict[str, float | None] = {}
    effect_sizes: Dict[str, float | None] = {}
    shapiro_ps: List[float] = []

    # Determine whether any metric violates normality
    use_friedman = False

    for key, col in metric_names.items():
        try:
            pivot = _pivot_metric(df, col)
        except Exception as e:
            log.error("Failed to pivot metric %s: %s", col, e)
            raw_p_values[key] = None
            effect_sizes[key] = None
            continue

        # Normality test on differences between first two models
        shapiro_p = _shapiro_on_differences(pivot)
        shapiro_ps.append(shapiro_p)

        if shapiro_p < 0.05:
            use_friedman = True

        if use_friedman:
            # Friedman test
            stat, p = _friedman_test(pivot)
            raw_p_values[key] = None if pd.isna(p) else float(p)
            if not pd.isna(stat):
                effect_sizes[key] = _kendalls_w(pivot, stat)
            else:
                effect_sizes[key] = None
        else:
            # Repeated‑measures ANOVA
            f_stat, p = _repeated_measures_anova(pivot, col)
            raw_p_values[key] = None if pd.isna(p) else float(p)
            if not pd.isna(f_stat):
                effect_sizes[key] = _eta_squared_anova(pivot, f_stat)
            else:
                effect_sizes[key] = None

    # Apply Holm‑Bonferroni correction
    p_vals_list = [raw_p_values.get(k) for k in metric_names.keys()]
    significance_flags = _holm_bonferroni(p_vals_list)
    significant: Dict[str, bool] = {
        k: bool(sig) for k, sig in zip(metric_names.keys(), significance_flags)
    }

    # Propagate exploratory flag
    exploratory = _read_exploratory_flag()

    # Assemble final JSON structure
    result = {
        "p_values": raw_p_values,
        "significant": significant,
        "effect_sizes": effect_sizes,
        "exploratory": exploratory,
    }

    # Write JSON output
    out_path = paths.results("statistics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.info("Statistical analysis written to %s", out_path)

    return result

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Command‑line entry point."""
    try:
        run_statistical_analysis()
        return 0
    except Exception as e:
        log.exception("Statistical analysis failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
