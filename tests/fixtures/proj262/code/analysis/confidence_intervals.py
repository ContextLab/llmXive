"""confidence_intervals.py
-------------------------

Compute 95% confidence intervals for MAE and RMSE metrics across
multiple random seeds.

The script expects a CSV file at ``results/metrics.csv`` with the
following columns (header row required):

    seed,mae,rmse

It reads the file, calculates the mean and 95 % confidence interval
for each metric using a Student's t‑distribution, and writes the
results to ``results/confidence_intervals.csv`` with the columns:

    metric,mean,lower_ci,upper_ci

The module also provides a ``compute_confidence_interval`` utility
that can be imported by tests or other analysis code.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy import stats

__all__ = [
    "compute_confidence_interval",
    "main",
]


def compute_confidence_interval(
    data: List[float] | np.ndarray,
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Compute the mean and confidence interval for a list of values.

    Parameters
    ----------
    data: list or np.ndarray
        Numeric data points (e.g., MAE values from different seeds).
    confidence: float, optional
        Desired confidence level (default 0.95 for 95 % CI).

    Returns
    -------
    tuple (mean, lower_bound, upper_bound)
        Mean of the data and the lower/upper bounds of the confidence
        interval calculated with a Student's t‑distribution.
    """
    if isinstance(data, list):
        data = np.asarray(data, dtype=float)

    if data.size == 0:
        raise ValueError("Data array is empty; cannot compute confidence interval.")

    n = data.size
    mean = np.mean(data)
    # Standard error of the mean; scipy.stats.sem handles n==1 gracefully.
    sem = stats.sem(data, ddof=1)
    # t critical value for two‑tailed interval
    t_crit = stats.t.ppf((1 + confidence) / 2.0, df=n - 1)
    margin = t_crit * sem
    lower = mean - margin
    upper = mean + margin
    return float(mean), float(lower), float(upper)


def _read_metrics(csv_path: Path) -> Tuple[List[float], List[float]]:
    """
    Read ``mae`` and ``rmse`` columns from the supplied CSV file.

    Returns
    -------
    mae_vals, rmse_vals : lists of floats
    """
    mae_vals: List[float] = []
    rmse_vals: List[float] = []

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        required_fields = {"mae", "rmse"}
        if not required_fields.issubset(reader.fieldnames or []):
            missing = required_fields - set(reader.fieldnames or [])
            raise ValueError(
                f"Input CSV {csv_path} is missing required columns: {missing}"
            )
        for row in reader:
            mae_vals.append(float(row["mae"]))
            rmse_vals.append(float(row["rmse"]))

    return mae_vals, rmse_vals


def _write_confidence_intervals(
    output_path: Path,
    results: List[Tuple[str, float, float, float]],
) -> None:
    """
    Write confidence‑interval results to a CSV file.

    Parameters
    ----------
    output_path: Path
        Destination CSV file.
    results: list of tuples
        Each tuple contains (metric_name, mean, lower_ci, upper_ci).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "mean", "lower_ci", "upper_ci"])
        for metric, mean, lower, upper in results:
            writer.writerow([metric, f"{mean:.6f}", f"{lower:.6f}", f"{upper:.6f}"])


def main() -> None:
    """
    Entry‑point for the confidence‑interval computation script.

    It reads ``results/metrics.csv`` relative to the project root,
    computes 95 % confidence intervals for MAE and RMSE, and writes
    ``results/confidence_intervals.csv``.
    """
    # Resolve paths relative to the repository root.
    repo_root = Path(__file__).resolve().parents[3]  # code/analysis/ -> project root
    metrics_path = repo_root / "results" / "metrics.csv"
    output_path = repo_root / "results" / "confidence_intervals.csv"

    if not metrics_path.is_file():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")

    mae_vals, rmse_vals = _read_metrics(metrics_path)

    mae_mean, mae_lower, mae_upper = compute_confidence_interval(mae_vals, confidence=0.95)
    rmse_mean, rmse_lower, rmse_upper = compute_confidence_interval(rmse_vals, confidence=0.95)

    results = [
        ("MAE", mae_mean, mae_lower, mae_upper),
        ("RMSE", rmse_mean, rmse_lower, rmse_upper),
    ]

    _write_confidence_intervals(output_path, results)
    print(f"Confidence intervals written to {output_path}")


if __name__ == "__main__":
    main()
