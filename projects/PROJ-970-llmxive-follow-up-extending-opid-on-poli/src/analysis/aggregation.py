"""
Aggregation utilities for post‑processing episode results.

Functions:
  - ``load_episode_results``: read the CSV into a pandas DataFrame.
  - ``compute_summary_stats``: group by tier & threshold, compute success
    rate, mean entropy, entropy variance, mean log‑prob shift, and write a
    summary CSV.
  - ``calculate_baseline_success``: extract baseline success (threshold = 1.0)
    and write to JSON.
  - ``calculate_rigidity``: fit quadratic entropy regression (via
    ``src.analysis.stats.run_entropy_regression``) and compute residual
    variance per tier‑threshold.
  - ``calculate_cost_benefit``: compute the distillation cost‑benefit ratio
    and augment the summary CSV.
"""

import json
from pathlib import Path

import pandas as pd
from llmxive_toolkit import paths

from .stats import run_entropy_regression

def load_episode_results() -> pd.DataFrame:
    """Load the episode results CSV."""
    csv_path = paths.results("episode_results.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Episode results not found at {csv_path}")
    return pd.read_csv(csv_path)

def compute_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics grouped by tier and threshold."""
    agg = df.groupby(["tier", "threshold"]).agg(
        success_rate=("success", "mean"),
        mean_entropy=("action_entropy", "mean"),
        entropy_variance=("action_entropy", "var"),
        mean_log_prob_shift=("log_prob_shift", "mean"),
        n_episodes=("success", "size"),
    ).reset_index()
    summary_path = paths.results("summary_stats.csv")
    agg.to_csv(summary_path, index=False)
    return agg

def calculate_baseline_success(df: pd.DataFrame) -> None:
    """Write baseline success rate (threshold == 1.0) to JSON."""
    baseline = df[df["threshold"] == 1.0]["success"].mean()
    out_path = paths.results("baseline_success_rate.json")
    out_path.write_text(json.dumps({"baseline_success_rate": baseline}))
    return baseline

def calculate_rigidity(df: pd.DataFrame) -> pd.DataFrame:
    """Compute policy rigidity (residual variance) and merge into summary."""
    # First, run the quadratic regression to obtain coefficients per tier
    regression_path = paths.results("entropy_regression.json")
    if not regression_path.is_file():
        # Run regression if not already present
        run_entropy_regression(
            input_path=str(paths.results("episode_results.csv")),
            output_path=str(regression_path),
        )
    with regression_path.open() as f:
        reg_data = json.load(f)

    # Compute predicted entropy per row and residuals
    def predict(row):
        tier = str(row["tier"])
        coeffs = reg_data["tiers"].get(tier, {}).get("coefficients", {"a": 0, "b": 0, "c": 0})
        a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
        return a * row["threshold"] ** 2 + b * row["threshold"] + c

    df["predicted_entropy"] = df.apply(predict, axis=1)
    df["entropy_residual"] = df["action_entropy"] - df["predicted_entropy"]
    # Residual variance per tier‑threshold
    rigidity = (
        df.groupby(["tier", "threshold"])["entropy_residual"]
        .var()
        .reset_index()
        .rename(columns={"entropy_residual": "policy_rigidity"})
    )
    # Merge into summary stats
    summary = compute_summary_stats(df)
    merged = summary.merge(rigidity, on=["tier", "threshold"], how="left")
    merged_path = paths.results("summary_stats_with_rigidity.csv")
    merged.to_csv(merged_path, index=False)
    return merged

def calculate_cost_benefit(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate distillation cost‑benefit ratio and augment the summary."""
    baseline = calculate_baseline_success(df)
    # Split into train/validation (fixed seed for reproducibility)
    validation = df.sample(frac=0.2, random_state=999)
    agg = (
        validation.groupby(["tier", "threshold"])
        .agg(mean_log_prob_shift=("log_prob_shift", "mean"), success_rate=("success", "mean"))
        .reset_index()
    )
    agg["success_rate_improvement"] = agg["success_rate"] - baseline
    agg["distillation_cost_benefit"] = agg.apply(
        lambda row: row["mean_log_prob_shift"] / row["success_rate_improvement"]
        if row["success_rate_improvement"] > 0
        else float("nan"),
        axis=1,
    )
    # Merge back into the main summary
    summary = compute_summary_stats(df)
    final = summary.merge(
        agg[["tier", "threshold", "distillation_cost_benefit"]],
        on=["tier", "threshold"],
        how="left",
    )
    final_path = paths.results("summary_stats_final.csv")
    final.to_csv(final_path, index=False)
    return final