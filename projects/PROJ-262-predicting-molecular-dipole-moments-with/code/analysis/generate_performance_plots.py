"""Generate performance visualizations for model training results.

This script reads a CSV file containing model performance metrics (e.g., MAE and
RMSE across different random seeds) and produces PNG figures summarizing the
results. The generated figures are saved under ``results/figures/``.

Expected CSV format (as produced by ``code/generate_metrics.py``):
    seed,model,mae,rmse
    0,GNN,0.123,0.156
    0,RandomForest,0.140,0.170
    ...

The script creates two bar plots:
    - MAE per model (averaged over seeds, with error bars showing std dev)
    - RMSE per model (averaged over seeds, with error bars showing std dev)

The module can be executed directly:
    $ python code/analysis/generate_performance_plots.py
"""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd


def load_metrics(csv_path: Path) -> pd.DataFrame:
    """Load the metrics CSV into a pandas DataFrame.

    Parameters
    ----------
    csv_path: Path
        Path to the CSV file containing the metrics.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``seed``, ``model``, ``mae``, ``rmse``.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    expected_cols = {"seed", "model", "mae", "rmse"}
    if not expected_cols.issubset(df.columns):
        missing = expected_cols - set(df.columns)
        raise ValueError(f"Metrics CSV missing columns: {missing}")
    return df


def aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics across seeds for each model.

    Returns a DataFrame indexed by model with mean and std for MAE and RMSE.
    """
    agg = (
        df.groupby("model")
        .agg(
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
            rmse_mean=("rmse", "mean"),
            rmse_std=("rmse", "std"),
        )
        .reset_index()
    )
    return agg


def plot_metric(
    agg_df: pd.DataFrame,
    metric_mean_col: str,
    metric_std_col: str,
    ylabel: str,
    output_path: Path,
) -> None:
    """Create a bar plot for a given metric.

    Parameters
    ----------
    agg_df: pd.DataFrame
        Aggregated metrics DataFrame (output of ``aggregate_metrics``).
    metric_mean_col: str
        Column name for the mean values (e.g., ``mae_mean``).
    metric_std_col: str
        Column name for the std deviation values (e.g., ``mae_std``).
    ylabel: str
        Y‑axis label for the plot.
    output_path: Path
        Destination file path for the PNG image.
    """
    models = agg_df["model"]
    means = agg_df[metric_mean_col]
    stds = agg_df[metric_std_col]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(models, means, yerr=stds, capsize=5, color="#4c72b0")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} per Model (averaged over seeds)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Annotate bar heights
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{mean:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def generate_plots(metrics_csv: Path, figures_dir: Path) -> List[Path]:
    """Generate MAE and RMSE bar plots from a metrics CSV.

    Parameters
    ----------
    metrics_csv: Path
        Path to the CSV containing raw metrics.
    figures_dir: Path
        Directory where PNG files will be written.

    Returns
    -------
    List[Path]
        Paths to the generated PNG files.
    """
    df = load_metrics(metrics_csv)
    agg = aggregate_metrics(df)

    mae_path = figures_dir / "mae_per_model.png"
    rmse_path = figures_dir / "rmse_per_model.png"

    plot_metric(
        agg,
        metric_mean_col="mae_mean",
        metric_std_col="mae_std",
        ylabel="Mean Absolute Error (MAE)",
        output_path=mae_path,
    )
    plot_metric(
        agg,
        metric_mean_col="rmse_mean",
        metric_std_col="rmse_std",
        ylabel="Root Mean Squared Error (RMSE)",
        output_path=rmse_path,
    )
    return [mae_path, rmse_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate performance figures from metrics CSV."
    )
    parser.add_argument(
        "--metrics-csv",
        type=Path,
        default=Path("results/metrics.csv"),
        help="Path to the metrics CSV file (default: results/metrics.csv)",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=Path("results/figures"),
        help="Directory to store generated PNG figures (default: results/figures)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated = generate_plots(args.metrics_csv, args.figures_dir)
    print(f"Generated {len(generated)} figure(s):")
    for p in generated:
        print(f" - {p}")


if __name__ == "__main__":
    main()