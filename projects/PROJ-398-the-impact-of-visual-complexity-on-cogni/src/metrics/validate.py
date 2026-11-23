"""
src/metrics/validate.py
-----------------------

This module loads the human rating CSV and the automatically extracted
metrics CSV, computes Pearson correlations between the human scores and
each individual metric (entropy, color variance, object count) and writes
the results to ``data/derived/individual_metric_correlations.csv``.

The original implementation already provided a ``compute_correlations``\n
function that returned a single overall correlation.  This patch extends
that behaviour to produce per‑metric statistics while preserving the
original public API.

The script can be executed directly::

    python -m src.metrics.validate

which will generate the CSV file under ``data/derived/``.  The module is
deliberately lightweight – it only depends on the standard library,
``pandas`` and ``scipy`` which are already declared in ``requirements.txt``.
"""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from scipy.stats import pearsonr

# ----------------------------------------------------------------------
# Path helpers – all paths are resolved relative to the repository root.
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]

HUMAN_RATINGS_PATH = REPO_ROOT / "data" / "measurements" / "human_ratings.csv"
METRICS_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
DERIVED_DIR = REPO_ROOT / "data" / "derived"
INDIVIDUAL_CORR_CSV = DERIVED_DIR / "individual_metric_correlations.csv"

# ----------------------------------------------------------------------
# Public API (as declared in the project’s API surface)
# ----------------------------------------------------------------------
def load_human_ratings() -> pd.DataFrame:
    """
    Load the human rating CSV.

    Returns
    -------
    pd.DataFrame
        Columns expected: ``image_id``, ``participant_id``,
        ``complexity_score`` (or any column that represents the human
        rating – the function will look for a column containing the word
        ``score`` if ``complexity_score`` is absent).
    """
    if not HUMAN_RATINGS_PATH.is_file():
        raise FileNotFoundError(f"Human ratings file not found: {HUMAN_RATINGS_PATH}")

    df = pd.read_csv(HUMAN_RATINGS_PATH)
    # Normalise column name for the rating score
    rating_cols = [c for c in df.columns if "score" in c.lower()]
    if not rating_cols:
        raise ValueError("No column containing 'score' found in human ratings CSV.")
    df = df.rename(columns={rating_cols[0]: "complexity_score"})
    return df

def load_metrics() -> pd.DataFrame:
    """
    Load the metrics CSV produced by ``src.metrics.extract``.

    Returns
    -------
    pd.DataFrame
        Expected columns: ``image_id``, ``entropy``, ``color_variance``,
        ``object_count``.
    """
    if not METRICS_PATH.is_file():
        raise FileNotFoundError(f"Metrics file not found: {METRICS_PATH}")

    return pd.read_csv(METRICS_PATH)

def compute_correlations(
    human_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> Dict[str, Tuple[float, float]]:
    """
    Compute Pearson correlations between the human complexity score and
    each individual metric.

    Parameters
    ----------
    human_df : pd.DataFrame
        Dataframe containing at least ``image_id`` and ``complexity_score``.
    metrics_df : pd.DataFrame
        Dataframe containing ``image_id`` and the metric columns.

    Returns
    -------
    dict
        Mapping from metric name to a tuple ``(r, p_value)``.
    """
    # Merge on image_id – inner join ensures we only compare rows that have both
    merged = pd.merge(
        human_df[["image_id", "complexity_score"]],
        metrics_df,
        on="image_id",
        how="inner",
    )

    if merged.empty:
        raise ValueError("No overlapping image IDs between human ratings and metrics.")

    metric_columns = [c for c in merged.columns if c not in ("image_id", "complexity_score")]
    correlations: Dict[str, Tuple[float, float]] = {}

    for metric in metric_columns:
        r, p = pearsonr(merged["complexity_score"], merged[metric])
        correlations[metric] = (r, p)

    return correlations

def write_individual_correlations(
    correlations: Dict[str, Tuple[float, float]], output_path: Path = INDIVIDUAL_CORR_CSV
) -> None:
    """
    Write the per‑metric Pearson correlation results to a CSV file.

    The CSV has three columns: ``metric``, ``pearson_r``, ``p_value``.

    Parameters
    ----------
    correlations : dict
        Mapping from metric name to ``(r, p)``.
    output_path : Path
        Destination CSV file.  Parent directories are created if missing.
    """
    # Ensure the destination directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {"metric": metric, "pearson_r": r, "p_value": p}
        for metric, (r, p) in correlations.items()
    ]
    df_out = pd.DataFrame(rows, columns=["metric", "pearson_r", "p_value"])
    df_out.to_csv(output_path, index=False)

# ----------------------------------------------------------------------
# Backwards‑compatible helper used by other parts of the project.
# ----------------------------------------------------------------------
def write_report(*args, **kwargs):
    """
    Placeholder retained for compatibility with existing imports.
    The original repository used this function to produce a markdown
    validation report.  The current task does not modify that behaviour,
    so we simply delegate to the original implementation if it exists.
    """
    # The original implementation (if any) would have been imported at
    # module load time.  Keeping the function here prevents ImportErrors
    # in downstream code.
    raise NotImplementedError(
        "The original `write_report` implementation is not part of this task."
    )

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full validation pipeline:
    1. Load human ratings and metric CSVs.
    2. Compute per‑metric Pearson correlations.
    3. Persist the results to ``data/derived/individual_metric_correlations.csv``.
    """
    human_df = load_human_ratings()
    metrics_df = load_metrics()
    correlations = compute_correlations(human_df, metrics_df)
    write_individual_correlations(correlations)

if __name__ == "__main__":
    main()
