"""Validate visual complexity metrics against human ratings.

This script computes the Pearson correlation coefficient between
aggregated human complexity scores and each automated visual complexity
metric (entropy, color variance, object count). The results are written
to ``data/derived/pilot_validation_report.md`` as a Markdown table.

Expected input files:
  - Human ratings: ``data/measurements/human_ratings.csv`` with columns
    ``image_id``, ``participant_id``, ``complexity_score``.
  - Metrics: ``data/processed/metrics.csv`` with columns
    ``image_id``, ``entropy``, ``variance``, ``object_count``.

The script can be executed directly:
    python src/metrics/validate.py

It will create the output directory if it does not exist.
"""

from pathlib import Path

import pandas as pd


def load_human_ratings(path: Path) -> pd.DataFrame:
    """Load human ratings and compute the mean rating per image."""
    df = pd.read_csv(path)
    required = {"image_id", "complexity_score"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Human ratings CSV missing columns: {missing}")
    # Aggregate by image_id
    mean_ratings = df.groupby("image_id", as_index=False)["complexity_score"].mean()
    mean_ratings.rename(columns={"complexity_score": "human_mean_score"}, inplace=True)
    return mean_ratings


def load_metrics(path: Path) -> pd.DataFrame:
    """Load automated metrics."""
    df = pd.read_csv(path)
    required = {"image_id", "entropy", "variance", "object_count"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Metrics CSV missing columns: {missing}")
    return df


def compute_correlations(
    merged: pd.DataFrame,
) -> pd.DataFrame:
    """Compute Pearson correlation between human scores and each metric.

    Returns a DataFrame with columns: metric, correlation, p_value.
    """
    results = []
    human_series = merged["human_mean_score"]
    for metric in ["entropy", "variance", "object_count"]:
        metric_series = merged[metric]
        if metric_series.isnull().any():
            raise ValueError(f"Metric column '{metric}' contains NaN values.")
        corr = human_series.corr(metric_series, method="pearson")
        # pandas does not provide p-value directly; compute via scipy if available.
        try:
            from scipy.stats import pearsonr

            corr, p_val = pearsonr(human_series, metric_series)
        except Exception:
            # Fallback: set p-value to NaN if scipy is unavailable.
            p_val = float("nan")
        results.append(
            {"metric": metric, "correlation": corr, "p_value": p_val}
        )
    return pd.DataFrame(results)


def write_report(df: pd.DataFrame, output_path: Path) -> None:
    """Write a markdown report with a correlation table."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Pilot Validation Report\n\n")
        f.write(
            "Pearson correlation between aggregated human complexity scores "
            "and each automated visual‑complexity metric.\n\n"
        )
        f.write("| Metric | Pearson r | p‑value |\n")
        f.write("|--------|-----------|----------|\n")
        for _, row in df.iterrows():
            metric = row["metric"]
            r = f"{row['correlation']:.4f}"
            p = (
                f"{row['p_value']:.4g}"
                if not pd.isna(row["p_value"])
                else "N/A"
            )
            f.write(f"| {metric} | {r} | {p} |\n")


def main() -> None:
    """Entry point for the validation script."""
    # Define default input / output locations
    human_ratings_path = Path("data/measurements/human_ratings.csv")
    metrics_path = Path("data/processed/metrics.csv")
    report_path = Path("data/derived/pilot_validation_report.md")

    # Load data
    human_df = load_human_ratings(human_ratings_path)
    metrics_df = load_metrics(metrics_path)

    # Merge on image_id
    merged = pd.merge(human_df, metrics_df, on="image_id", how="inner")
    if merged.empty:
        raise ValueError(
            "Merged dataset is empty – check that image IDs match between "
            "human ratings and metrics files."
        )

    # Compute correlations
    corr_df = compute_correlations(merged)

    # Write report
    write_report(corr_df, report_path)
    print(f"Validation report written to {report_path}")


if __name__ == "__main__":
    main()