"""
Pilot Gate Script
==================

This module implements a gate that validates the pilot study
results before downstream tasks are allowed to run. It loads the
human rating data and the automatically extracted visual‑complexity
metrics, aggregates them per image, computes a Pearson correlation
between the two, and exits with a non‑zero status code if the
correlation coefficient ``r`` is below the required threshold
(0.5).

The implementation is deliberately lightweight and does not make
any assumptions about the exact metric columns – any numeric column
(besides the ``image_id`` key) is treated as a metric and the mean
across those columns is used as a single composite score.
"""

import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from scipy.stats import pearsonr

# ----------------------------------------------------------------------
# Configuration – default locations of the CSV artefacts produced by
# earlier pipeline steps.
# ----------------------------------------------------------------------
HUMAN_RATINGS_CSV = Path("data/measurements/human_ratings.csv")
METRICS_CSV = Path("data/processed/metrics.csv")
CORRELATION_THRESHOLD = 0.5


def load_human_ratings(csv_path: Path = HUMAN_RATINGS_CSV) -> pd.DataFrame:
    """
    Load the human rating CSV.

    Expected columns:
        - ``image_id``: identifier matching the metrics file.
        - ``participant_id``: identifier of the participant.
        - ``complexity_score``: numeric rating (e.g. 1‑5).

    Parameters
    ----------
    csv_path:
        Path to the CSV file. Defaults to the project‑wide location.

    Returns
    -------
    pandas.DataFrame
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Human ratings file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required = {"image_id", "complexity_score"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Human ratings CSV missing columns: {missing}")
    return df


def load_metrics(csv_path: Path = METRICS_CSV) -> pd.DataFrame:
    """
    Load the metrics CSV.

    Expected columns:
        - ``image_id``: identifier that matches the human rating file.
        - One or more numeric metric columns (e.g. ``entropy``,
          ``color_variance``, ``object_count``).

    Parameters
    ----------
    csv_path:
        Path to the CSV file. Defaults to the project‑wide location.

    Returns
    -------
    pandas.DataFrame
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    if "image_id" not in df.columns:
        raise ValueError("Metrics CSV must contain an 'image_id' column")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    # Ensure at least one metric column besides ``image_id`` exists.
    metric_cols = [c for c in numeric_cols if c != "image_id"]
    if not metric_cols:
        raise ValueError("Metrics CSV contains no numeric metric columns")
    return df


def aggregate_metrics(
    human_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> Tuple[pd.Series, pd.Series]:
    """
    Aggregate both data sources to a per‑image level.

    * Human ratings – mean of ``complexity_score`` per ``image_id``.
    * Metrics – mean of *all* numeric metric columns per ``image_id``,
      producing a single composite score.

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        ``(human_series, metric_series)`` where the index is ``image_id``.
    """
    # Human ratings aggregation
    human_series = (
        human_df.groupby("image_id")["complexity_score"]
        .mean()
        .rename("human_mean")
    )

    # Metric aggregation – create a composite metric as the row‑wise mean
    # of all metric columns (excluding ``image_id``).
    metric_numeric = metrics_df.drop(columns=["image_id"])
    metric_series = (
        metric_numeric.mean(axis=1).rename("metric_mean")
    )
    metric_series.index = metrics_df["image_id"]

    # Align the two series on the intersection of image IDs
    common_ids = human_series.index.intersection(metric_series.index)
    human_series = human_series.loc[common_ids]
    metric_series = metric_series.loc[common_ids]

    return human_series, metric_series


def compute_correlation(
    human_series: pd.Series, metric_series: pd.Series
) -> Tuple[float, float]:
    """
    Compute Pearson correlation between the two series.

    Parameters
    ----------
    human_series, metric_series:
        Pandas Series of equal length and aligned indices.

    Returns
    -------
    Tuple[float, float]
        ``(r, p_value)`` as returned by :func:`scipy.stats.pearsonr`.
    """
    if len(human_series) == 0:
        raise ValueError("No overlapping data to compute correlation")
    r, p = pearsonr(human_series.values, metric_series.values)
    return r, p


def main() -> None:
    """
    Entry‑point used by the CI gate.

    The function loads the data, aggregates it, computes the correlation,
    and exits with status ``0`` if the correlation meets the threshold,
    otherwise ``1``.
    """
    try:
        human_df = load_human_ratings()
        metrics_df = load_metrics()
        human_series, metric_series = aggregate_metrics(human_df, metrics_df)
        r, p = compute_correlation(human_series, metric_series)
    except Exception as exc:
        # Any failure should be loud – re‑raise after printing a helpful
        # message so the CI sees the traceback.
        print(f"[pilot_gate] ERROR: {exc}", file=sys.stderr)
        raise

    print(
        f"[pilot_gate] Pearson r = {r:.4f} (p = {p:.4g}); "
        f"threshold = {CORRELATION_THRESHOLD}"
    )
    if r < CORRELATION_THRESHOLD:
        print("[pilot_gate] Correlation below threshold – aborting.", file=sys.stderr)
        sys.exit(1)

    print("[pilot_gate] Correlation meets threshold – continuing.")
    sys.exit(0)


if __name__ == "__main__":
    main()