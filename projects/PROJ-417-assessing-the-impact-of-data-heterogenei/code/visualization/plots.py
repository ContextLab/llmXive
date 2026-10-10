"""
Visualization module for the heterogeneity impact study.

This script reads the aggregated metrics CSV produced by the analysis
pipeline and generates two PNG figures:

1. Coverage vs. τ² (saved as `data/results/coverage_vs_tau2.png`)
2. Mean Bias vs. τ² (saved as `data/results/mean_bias_vs_tau2.png`)

The script is intended to be run as a stand‑alone command:

    python code/visualization/plots.py

It will raise a clear error if the required input file is missing.
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Constants – keep them in one place for easy adjustment
# ----------------------------------------------------------------------
INPUT_CSV = Path("data/results/aggregated_metrics.csv")
COVERAGE_PNG = Path("data/results/coverage_vs_tau2.png")
BIAS_PNG = Path("data/results/mean_bias_vs_tau2.png")


def read_aggregated_metrics(csv_path: Path):
    """
    Load the aggregated metrics CSV into a list of dictionaries.

    Expected columns (at minimum):
        - tau2_level (float)
        - coverage_rate (float)
        - mean_bias (float)

    Returns:
        List[dict]: each dict corresponds to one row of the CSV.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Aggregated metrics file not found: {csv_path}")

    records = []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                records.append(
                    {
                        "tau2": float(row["tau2_level"]),
                        "coverage": float(row["coverage_rate"]),
                        "bias": float(row["mean_bias"]),
                    }
                )
            except (KeyError, ValueError) as exc:
                raise ValueError(
                    f"Malformed row in {csv_path}: {row}. "
                    "Expected numeric 'tau2_level', 'coverage_rate', and 'mean_bias'."
                ) from exc
    if not records:
        raise ValueError(f"The file {csv_path} contains no data rows.")
    # Sort by τ² for nicer plots
    records.sort(key=lambda r: r["tau2"])
    return records


def plot_coverage(records):
    """Create and save Coverage vs. τ² plot."""
    tau2_vals = [r["tau2"] for r in records]
    coverage_vals = [r["coverage"] for r in records]

    plt.figure(figsize=(6, 4))
    plt.plot(tau2_vals, coverage_vals, marker="o", linestyle="-", color="steelblue")
    plt.title("Coverage vs. τ²")
    plt.xlabel("Injected τ²")
    plt.ylabel("Coverage Rate")
    plt.ylim(0, 1.05)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    COVERAGE_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(COVERAGE_PNG, dpi=300)
    plt.close()


def plot_mean_bias(records):
    """Create and save Mean Bias vs. τ² plot."""
    tau2_vals = [r["tau2"] for r in records]
    bias_vals = [r["bias"] for r in records]

    plt.figure(figsize=(6, 4))
    plt.plot(tau2_vals, bias_vals, marker="s", linestyle="-", color="darkorange")
    plt.title("Mean Bias vs. τ²")
    plt.xlabel("Injected τ²")
    plt.ylabel("Mean Bias")
    plt.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    BIAS_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(BIAS_PNG, dpi=300)
    plt.close()


def main():
    """Entry point for the visualization script."""
    try:
        records = read_aggregated_metrics(INPUT_CSV)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    plot_coverage(records)
    plot_mean_bias(records)

    print(f"✅ Generated {COVERAGE_PNG}")
    print(f"✅ Generated {BIAS_PNG}")


if __name__ == "__main__":
    main()
