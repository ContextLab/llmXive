"""
src/metrics/validate.py

Implements the pilot validation step: compute Pearson correlation between
human‑provided complexity scores and the automatically extracted visual‑complexity
metrics (entropy, colour variance, object count).

The module provides a small public API used by the test suite and by downstream
pipeline stages:

* ``load_human_ratings()`` – loads ``data/measurements/human_ratings.csv``.
* ``load_metrics()`` – loads ``data/processed/metrics.csv``.
* ``compute_correlations(human_df, metrics_df)`` – returns a mapping from metric
  name to a ``(r, p_value)`` tuple.
* ``write_report(correlations, output_path)`` – writes a markdown report
  summarising the correlations.
* ``main()`` – orchestrates the full workflow.

The implementation relies only on the public API surface that already exists
in the repository:
  * ``src.config.get_relative_path`` – resolves project‑relative paths.
  * ``pandas`` – for CSV handling.
  * ``scipy.stats.pearsonr`` – for the statistical test.
"""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from scipy.stats import pearsonr

# ``get_relative_path`` is part of the public config API.
from src.config import get_relative_path


def load_human_ratings() -> pd.DataFrame:
    """
    Load the human ratings CSV produced by the pilot study.

    Returns
    -------
    pandas.DataFrame
        Columns expected: ``image_id``, ``participant_id``, ``complexity_score``.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist at the expected location.
    """
    csv_path = get_relative_path("data/measurements/human_ratings.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Human ratings file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required = {"image_id", "participant_id", "complexity_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Human ratings CSV missing columns: {missing}")
    return df


def load_metrics() -> pd.DataFrame:
    """
    Load the automatically extracted visual‑complexity metrics.

    Returns
    -------
    pandas.DataFrame
        Columns expected: ``image_id``, ``entropy``, ``color_variance``,
        ``object_count``.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist at the expected location.
    """
    csv_path = get_relative_path("data/processed/metrics.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required = {"image_id", "entropy", "color_variance", "object_count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Metrics CSV missing columns: {missing}")
    return df


def compute_correlations(
    human_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> Dict[str, Tuple[float, float]]:
    """
    Compute Pearson correlation (r) and two‑tailed p‑value between the human
    complexity scores and each visual‑complexity metric.

    Parameters
    ----------
    human_df : pandas.DataFrame
        Must contain ``image_id`` and ``complexity_score``.
    metrics_df : pandas.DataFrame
        Must contain ``image_id`` and the three metric columns.

    Returns
    -------
    dict
        Mapping ``metric_name -> (r, p_value)`` for ``entropy``,
        ``color_variance`` and ``object_count``.

    Notes
    -----
    The function merges the two DataFrames on ``image_id`` to ensure a
    one‑to‑one correspondence. Rows without a match are dropped.
    """
    # Merge on image_id to align human scores with metrics
    merged = pd.merge(
        human_df[["image_id", "complexity_score"]],
        metrics_df,
        on="image_id",
        how="inner",
    )
    if merged.empty:
        raise ValueError("No overlapping image IDs between human ratings and metrics.")

    correlations: Dict[str, Tuple[float, float]] = {}
    for metric in ["entropy", "color_variance", "object_count"]:
        r, p = pearsonr(merged["complexity_score"], merged[metric])
        correlations[metric] = (r, p)
    return correlations


def write_report(
    correlations: Dict[str, Tuple[float, float]], output_path: Path
) -> None:
    """
    Write a markdown report summarising the Pearson correlations.

    The report contains a small table with metric name, Pearson r and p‑value.

    Parameters
    ----------
    correlations : dict
        Mapping produced by :func:`compute_correlations`.
    output_path : pathlib.Path
        Destination file (will be created/overwritten).
    """
    lines = [
        "# Pilot Validation Report",
        "",
        "This report summarises the relationship between human‑rated visual complexity"
        " and the automatically extracted metrics for the pilot study.",
        "",
        "| Metric | Pearson r | p‑value |",
        "|--------|-----------|---------|",
    ]
    for metric, (r, p) in correlations.items():
        lines.append(f"| {metric} | {r:.4f} | {p:.4e} |")
    report_content = "\n".join(lines) + "\n"

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")


def main() -> None:
    """
    Entry‑point for the validation script.

    When executed as ``python -m src.metrics.validate`` it will:
      1. Load human ratings.
      2. Load metric extractions.
      3. Compute Pearson correlations.
      4. Write a markdown report to ``data/derived/pilot_validation_report.md``.
    """
    human_df = load_human_ratings()
    metrics_df = load_metrics()
    correlations = compute_correlations(human_df, metrics_df)

    report_path = get_relative_path("data/derived/pilot_validation_report.md")
    write_report(correlations, report_path)


if __name__ == "__main__":
    # Allow running the module directly.
    main()