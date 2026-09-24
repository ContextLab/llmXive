"""Generate a validation report for the pilot study.

This script loads human complexity ratings and visual complexity metrics,
computes the Pearson correlation between them, creates a scatter plot, and
writes a markdown report containing the plot and the correlation statistics.

The output files are:
  - data/derived/pilot_validation_scatter.png
  - data/derived/pilot_validation_report.md
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
HUMAN_RATINGS_CSV = Path("data/measurements/human_ratings.csv")
METRICS_CSV = Path("data/processed/metrics.csv")
OUTPUT_DIR = Path("data/derived")
SCATTER_PATH = OUTPUT_DIR / "pilot_validation_scatter.png"
REPORT_PATH = OUTPUT_DIR / "pilot_validation_report.md"

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def load_human_ratings(csv_path: Path) -> pd.DataFrame:
    """Load human ratings and compute the mean rating per image."""
    df = pd.read_csv(csv_path)
    required = {"image_id", "complexity_score"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Human ratings CSV missing columns: {missing}")
    # Average across participants for each image
    mean_ratings = df.groupby("image_id", as_index=False)["complexity_score"].mean()
    mean_ratings = mean_ratings.rename(columns={"complexity_score": "human_score"})
    return mean_ratings

def load_metrics(csv_path: Path) -> pd.DataFrame:
    """Load visual complexity metrics."""
    df = pd.read_csv(csv_path)
    if "image_id" not in df.columns:
        raise ValueError("Metrics CSV must contain an 'image_id' column.")
    # For simplicity we use the average of all numeric metric columns as a single score.
    metric_cols = df.select_dtypes(include="number").columns.drop("image_id")
    if metric_cols.empty:
        raise ValueError("No numeric metric columns found in metrics CSV.")
    df["metric_score"] = df[metric_cols].mean(axis=1)
    return df[["image_id", "metric_score"]]

def compute_correlation(
    human_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> tuple[float, float]:
    """Merge the two dataframes on image_id and compute Pearson r and p-value."""
    merged = pd.merge(human_df, metrics_df, on="image_id", how="inner")
    if merged.empty:
        raise ValueError("No overlapping image IDs between ratings and metrics.")
    r, p = pearsonr(merged["human_score"], merged["metric_score"])
    return r, p, merged

def create_scatter_plot(df: pd.DataFrame, output_path: Path) -> None:
    """Create and save a scatter plot of metric vs. human score."""
    plt.figure(figsize=(6, 4))
    plt.scatter(df["metric_score"], df["human_score"], alpha=0.7, edgecolor="k")
    plt.title("Pilot Validation: Metric vs. Human Complexity Rating")
    plt.xlabel("Metric Score (mean of visual metrics)")
    plt.ylabel("Human Rating (average across participants)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()

def write_markdown_report(
    r: float, p: float, plot_path: Path, report_path: Path
) -> None:
    """Write a markdown report that embeds the scatter plot and shows statistics."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Pilot Validation Report\n\n")
        f.write(
            "This report presents the relationship between the automatically\n"
            "computed visual‑complexity metric and the human‑rated complexity scores\n"
            "collected during the pilot study.\n\n"
        )
        f.write(f"**Pearson correlation coefficient (r):** `{r:.4f}`\n\n")
        f.write(f"**Two‑tailed p‑value:** `{p:.4e}`\n\n")
        f.write("![Scatter Plot](" + plot_path.name + ")\n")

# --------------------------------------------------------------------------- #
# Main execution
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    """Run the validation report generation pipeline."""
    # Resolve paths relative to the repository root
    human_path = Path(HUMAN_RATINGS_CSV)
    metrics_path = Path(METRICS_CSV)

    # Load data
    human_df = load_human_ratings(human_path)
    metrics_df = load_metrics(metrics_path)

    # Compute correlation
    r, p, merged_df = compute_correlation(human_df, metrics_df)

    # Create visualisation
    create_scatter_plot(merged_df, SCATTER_PATH)

    # Write markdown report
    write_markdown_report(r, p, SCATTER_PATH, REPORT_PATH)

    print(f"Report written to {REPORT_PATH}")
    print(f"Scatter plot saved to {SCATTER_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
