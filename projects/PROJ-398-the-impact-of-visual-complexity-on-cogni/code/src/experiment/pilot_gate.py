"""
Pilot Gate Script
-----------------
This script validates the pilot study results by computing the Pearson
correlation between human complexity ratings and automatically extracted
visual‑complexity metrics.  If the correlation coefficient (r) is below
the predefined threshold (0.5), the script exits with a non‑zero status
code, thereby acting as a gate that prevents downstream tasks from
running.

Expected data locations (produced by earlier tasks):
  * Human ratings CSV:      ``data/measurements/human_ratings.csv``
  * Metrics CSV:            ``data/processed/metrics.csv``

The CSVs must contain at least the following columns:
  * ``image_id`` – identifier that matches between the two files
  * ``complexity_score`` – human rating (1‑10)
  * ``entropy``, ``color_variance``, ``object_count`` – numeric metric columns
    (any subset is acceptable; the script will compute a single aggregated
    metric by averaging the available numeric columns).

The script is deliberately lightweight: it does **not** write any output
files; it merely prints the correlation value for logging purposes and
returns an appropriate exit code.
"""

import sys
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
HUMAN_RATINGS_PATH = Path("data/measurements/human_ratings.csv")
METRICS_PATH = Path("data/processed/metrics.csv")
CORRELATION_THRESHOLD = 0.5  # minimum acceptable Pearson r


def load_human_ratings(path: Path) -> pd.DataFrame:
    """Load the pilot human‑rating CSV."""
    if not path.is_file():
        raise FileNotFoundError(f"Human ratings file not found: {path}")
    df = pd.read_csv(path)
    required = {"image_id", "complexity_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Human ratings CSV missing columns: {missing}")
    return df[["image_id", "complexity_score"]]


def load_metrics(path: Path) -> pd.DataFrame:
    """Load the automatically extracted metrics CSV."""
    if not path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    df = pd.read_csv(path)
    # Identify numeric metric columns (exclude image_id)
    metric_cols = [c for c in df.columns if c != "image_id"]
    if not metric_cols:
        raise ValueError("Metrics CSV contains no metric columns.")
    return df[["image_id"] + metric_cols]


def aggregate_metrics(df_metrics: pd.DataFrame) -> pd.Series:
    """
    Produce a single numeric series per image by averaging all metric columns.
    This mirrors the simple aggregation used in the original pilot validation.
    """
    metric_cols = [c for c in df_metrics.columns if c != "image_id"]
    # Compute row‑wise mean, ignoring NaNs
    return df_metrics[metric_cols].mean(axis=1)


def compute_correlation(
    df_ratings: pd.DataFrame, df_metrics: pd.DataFrame
) -> float:
    """
    Merge the two data frames on ``image_id`` and compute Pearson's r.
    Returns the correlation coefficient (the p‑value is ignored for the gate).
    """
    merged = pd.merge(df_ratings, df_metrics, on="image_id", how="inner")
    if merged.empty:
        raise ValueError("No overlapping image_id entries between ratings and metrics.")
    # Aggregate the multiple metric columns into a single score
    merged["aggregated_metric"] = aggregate_metrics(merged)
    r, _ = pearsonr(merged["complexity_score"], merged["aggregated_metric"])
    return r


def main() -> int:
    """Entry point for the pilot gate."""
    try:
        df_ratings = load_human_ratings(HUMAN_RATINGS_PATH)
        df_metrics = load_metrics(METRICS_PATH)
        r = compute_correlation(df_ratings, df_metrics)
        print(f"Pilot correlation (Pearson r): {r:.4f}")
        if r < CORRELATION_THRESHOLD:
            print(
                f"Correlation {r:.4f} is below the required threshold "
                f"of {CORRELATION_THRESHOLD:.2f}. Exiting with error."
            )
            return 1
        else:
            print(
                f"Correlation {r:.4f} meets the required threshold "
                f"of {CORRELATION_THRESHOLD:.2f}. Proceeding."
            )
            return 0
    except Exception as exc:  # pragma: no cover – surface any unexpected error
        print(f"Pilot gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
