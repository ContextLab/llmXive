"""
generate_report.py

This script generates a statistical report (JSON and CSV) containing raw and
Holm‑Bonferroni corrected p‑values, effect sizes, and 95 % confidence
intervals for each memory metric present in the processed measurements
CSV. It re‑uses the public API from ``code.analyze`` where possible and
falls back to direct pandas/numpy operations for the pairing logic.

Output files:
  - data/processed/statistical_report.json
  - data/processed/statistical_report.csv
"""

import json
import pathlib
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Public API from code.analyze
from analyze import (
    load_memory_data,
    wilcoxon_signed_rank_test,
    calculate_effect_size,
    holm_bonferroni_correction,
    generate_analysis_report,
)


def _pair_metric(
    df: pd.DataFrame, metric: str
) -> Tuple[pd.Series, pd.Series]:
    """
    Return paired series (LLM, Human) for a given metric.

    The input ``df`` is expected to have the columns:
      - problem_id
      - source_type (values: "LLM" or "Human")
      - <metric> (numeric)
      - status (optional, rows with non‑OK status are dropped)

    Parameters
    ----------
    df: pd.DataFrame
        Full measurements data.
    metric: str
        Name of the numeric column to extract.

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        (llm_series, human_series) aligned by ``problem_id``.
    """
    # Keep only successful measurements
    if "status" in df.columns:
        df = df[df["status"] == "OK"]

    # Keep only rows where the metric is not missing
    df = df.dropna(subset=[metric])

    # Pivot so each problem_id has two rows: LLM and Human
    pivot = df.pivot(index="problem_id", columns="source_type", values=metric)

    # Ensure both columns exist
    if "LLM" not in pivot.columns or "Human" not in pivot.columns:
        raise ValueError(f"Both LLM and Human rows required for metric '{metric}'.")

    # Drop any problem where either side is missing
    paired = pivot.dropna(subset=["LLM", "Human"])

    return paired["LLM"], paired["Human"]


def _bootstrap_cohens_d_ci(
    diffs: np.ndarray, n_boot: int = 1000, ci: float = 0.95
) -> Tuple[float, float]:
    """
    Compute a bootstrap confidence interval for Cohen's d using the
    distribution of differences.

    Parameters
    ----------
    diffs : np.ndarray
        Array of paired differences (LLM - Human).
    n_boot : int, default 1000
        Number of bootstrap resamples.
    ci : float, default 0.95
        Desired confidence level.

    Returns
    -------
    Tuple[float, float]
        (lower_bound, upper_bound) of the confidence interval.
    """
    boot_stats = []
    rng = np.random.default_rng(0)  # deterministic seed

    for _ in range(n_boot):
        sample = rng.choice(diffs, size=diffs.shape[0], replace=True)
        mean_diff = sample.mean()
        std_diff = sample.std(ddof=1)
        # Avoid division by zero
        d = mean_diff / std_diff if std_diff != 0 else 0.0
        boot_stats.append(d)

    lower = np.percentile(boot_stats, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_stats, (1 + ci) / 2 * 100)
    return lower, upper


def main() -> None:
    """
    Orchestrates the full analysis pipeline and writes the report files.
    """
    # ------------------------------------------------------------------
    # 1. Load the processed measurements CSV
    # ------------------------------------------------------------------
    measurements_path = pathlib.Path("data/processed/memory_measurements.csv")
    df = load_memory_data(str(measurements_path))

    # ------------------------------------------------------------------
    # 2. Identify numeric metric columns to analyse
    # ------------------------------------------------------------------
    # Exclude identifier / categorical columns
    exclude_cols = {"problem_id", "source_type", "status"}
    metric_cols = [
        col
        for col in df.columns
        if col not in exclude_cols and np.issubdtype(df[col].dtype, np.number)
    ]

    if not metric_cols:
        raise RuntimeError("No numeric metric columns found for analysis.")

    # ------------------------------------------------------------------
    # 3. For each metric compute paired statistics
    # ------------------------------------------------------------------
    raw_p_values: List[float] = []
    metric_results: Dict[str, Dict] = {}

    for metric in metric_cols:
        try:
            llm_vals, human_vals = _pair_metric(df, metric)
        except ValueError as e:
            # Skip metrics without a full LLM/Human pairing
            print(f"Skipping metric '{metric}': {e}")
            continue

        # Wilcoxon signed‑rank test
        wilcoxon_res = wilcoxon_signed_rank_test(llm_vals, human_vals)
        statistic = wilcoxon_res.get("statistic")
        p_raw = wilcoxon_res.get("p_value")

        # Effect size (Cohen's d) and its confidence interval
        effect_res = calculate_effect_size(llm_vals, human_vals)
        cohens_d = effect_res.get("cohens_d")

        diffs = (llm_vals - human_vals).to_numpy()
        ci_low, ci_high = _bootstrap_cohens_d_ci(diffs)

        # Store intermediate results; corrected p‑value will be filled later
        metric_results[metric] = {
            "statistic": statistic,
            "p_value_raw": p_raw,
            "effect_size": cohens_d,
            "effect_size_ci": [ci_low, ci_high],
        }
        raw_p_values.append(p_raw)

    if not metric_results:
        raise RuntimeError("No metrics produced paired results.")

    # ------------------------------------------------------------------
    # 4. Apply Holm‑Bonferroni correction across all performed tests
    # ------------------------------------------------------------------
    corrected_p = holm_bonferroni_correction(raw_p_values)

    # Assign corrected p‑values back to the result dict (preserving order)
    for (metric, res), p_corr in zip(metric_results.items(), corrected_p):
        res["p_value_corrected"] = p_corr

    # ------------------------------------------------------------------
    # 5. Write JSON and CSV reports
    # ------------------------------------------------------------------
    output_json = pathlib.Path("data/processed/statistical_report.json")
    output_csv = pathlib.Path("data/processed/statistical_report.csv")

    # JSON report – a compact dictionary
    generate_analysis_report(metric_results, str(output_json))

    # CSV report – one row per metric
    rows = []
    for metric, res in metric_results.items():
        rows.append(
            {
                "metric": metric,
                "statistic": res["statistic"],
                "p_value_raw": res["p_value_raw"],
                "p_value_corrected": res["p_value_corrected"],
                "effect_size": res["effect_size"],
                "ci_low": res["effect_size_ci"][0],
                "ci_high": res["effect_size_ci"][1],
            }
        )
    pd.DataFrame(rows).to_csv(output_csv, index=False)

    print(f"Statistical report written to:\n  JSON: {output_json}\n  CSV: {output_csv}")


if __name__ == "__main__":
    main()
