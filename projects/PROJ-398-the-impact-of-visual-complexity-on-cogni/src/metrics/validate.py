"""
src/metrics/validate.py

Compute Pearson correlation between human visual‑complexity ratings and the
automatically extracted image metrics (entropy, colour variance, object count).

The module provides a small CLI that loads the required CSV files, merges them
on ``image_id`` and writes a markdown report containing the correlation
coefficients and p‑values.

Public API
----------
* ``load_human_ratings()`` – returns a ``pandas.DataFrame`` with the human
  ratings.
* ``load_metrics()`` – returns a ``pandas.DataFrame`` with the extracted metrics.
* ``compute_correlations()`` – merges the two DataFrames, aggregates human
  scores per image and returns a ``dict`` mapping metric name to a tuple
  ``(r, p)``.
* ``write_report(correlations, output_path)`` – writes a markdown table with
  the results.
* ``main()`` – orchestrates the whole process.
"""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from scipy.stats import pearsonr

# ----------------------------------------------------------------------
# Configurable paths – tests can monkey‑patch these attributes.
# ----------------------------------------------------------------------
HUMAN_RATINGS_PATH = Path("data/measurements/human_ratings.csv")
METRICS_PATH = Path("data/processed/metrics.csv")
REPORT_PATH = Path("data/derived/validation_report.md")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_human_ratings() -> pd.DataFrame:
    """
    Load the human rating CSV.

    Expected columns: ``image_id``, ``participant_id``, ``complexity_score``.
    """
    if not HUMAN_RATINGS_PATH.is_file():
        raise FileNotFoundError(f"Human ratings file not found: {HUMAN_RATINGS_PATH}")
    df = pd.read_csv(HUMAN_RATINGS_PATH)
    required = {"image_id", "participant_id", "complexity_score"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Human ratings CSV missing columns: {missing}")
    return df

def load_metrics() -> pd.DataFrame:
    """
    Load the metrics CSV.

    Expected columns: ``image_id``, ``entropy``, ``variance``,
    ``object_count`` (additional columns are ignored).
    """
    if not METRICS_PATH.is_file():
        raise FileNotFoundError(f"Metrics file not found: {METRICS_PATH}")
    df = pd.read_csv(METRICS_PATH)
    required = {"image_id", "entropy", "variance", "object_count"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Metrics CSV missing columns: {missing}")
    return df

def compute_correlations() -> Dict[str, Tuple[float, float]]:
    """
    Compute Pearson correlation between each metric and the *average* human
    complexity score per image.

    Returns
    -------
    dict
        Mapping ``metric_name`` → ``(r, p_value)``.
    """
    # Load data
    human_df = load_human_ratings()
    metrics_df = load_metrics()

    # Average human rating per image
    human_mean = (
        human_df.groupby("image_id")["complexity_score"]
        .mean()
        .reset_index(name="mean_complexity")
    )

    # Merge with metrics
    merged = pd.merge(human_mean, metrics_df, on="image_id", how="inner")
    if merged.empty:
        raise ValueError("No overlapping image IDs between ratings and metrics.")

    # Compute correlations
    results: Dict[str, Tuple[float, float]] = {}
    metric_cols = ["entropy", "variance", "object_count"]
    for col in metric_cols:
        r, p = pearsonr(merged[col], merged["mean_complexity"])
        results[col] = (r, p)
    return results

def write_report(
    correlations: Dict[str, Tuple[float, float]], output_path: Path = REPORT_PATH
) -> None:
    """
    Write a markdown report containing a table of correlations.

    Parameters
    ----------
    correlations
        Mapping of metric name to ``(r, p)``.
    output_path
        Destination path for the markdown file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Validation Report",
        "",
        "Pearson correlation between human‑rated visual complexity and each "
        "automatically extracted metric.",
        "",
        "| Metric | Pearson r | p‑value |",
        "|--------|-----------|---------|",
    ]
    for metric, (r, p) in correlations.items():
        lines.append(f"| {metric} | {r:.4f} | {p:.4e} |")
    content = "\n".join(lines) + "\n"
    output_path.write_text(content, encoding="utf-8")

def main() -> None:
    """
    Entry‑point for the script. Loads data, computes correlations and writes
    the report.
    """
    correlations = compute_correlations()
    write_report(correlations)
    print(f"Validation report written to {REPORT_PATH}")

if __name__ == "__main__":
    main()
