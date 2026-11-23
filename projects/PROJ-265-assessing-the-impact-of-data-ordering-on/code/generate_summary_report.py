import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config import get_results_dir

def load_metrics_data(csv_path: str) -> pd.DataFrame:
    """Load the coverage metrics CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    return pd.read_csv(csv_path)

def generate_summary_text(df: pd.DataFrame) -> str:
    """Generate a summary text block."""
    total_rows = len(df)
    significant_count = len(df[df["p_value"].astype(float) < 0.05])
    avg_drop = df["diff"].astype(float).mean()

    return (
        f"Analysis completed on {total_rows} configurations.\n"
        f"Significant differences (p < 0.05) found in {significant_count} cases.\n"
        f"Average coverage drop (Ordered - Shuffled): {avg_drop:.4f}."
    )

def generate_coverage_table(df: pd.DataFrame) -> str:
    """Generate a markdown table of coverage metrics."""
    lines = ["| Phi | N | Ordered Coverage | Shuffled Coverage | Difference | P-Value |",
             "|-----|---|------------------|-------------------|------------|---------|"]

    for _, row in df.iterrows():
        lines.append(
            f"| {row['phi']:.1f} | {row['n']} | {row['ordered_cov']:.4f} | "
            f"{row['shuffled_cov']:.4f} | {row['diff']:.4f} | {row['p_value']} |"
        )

    return "\n".join(lines)

def generate_significance_table(df: pd.DataFrame) -> str:
    """Generate a table highlighting significant results."""
    lines = ["| Phi | N | Significant (p < 0.05) |",
             "|-----|---|------------------------|"]

    for _, row in df.iterrows():
        is_sig = "Yes" if float(row["p_value"]) < 0.05 else "No"
        lines.append(f"| {row['phi']:.1f} | {row['n']} | {is_sig} |")

    return "\n".join(lines)

def generate_markdown_report(df: pd.DataFrame, output_path: str):
    """Generate the full summary markdown report."""
    report_lines = [
        "# Summary Report",
        "",
        "## Summary",
        generate_summary_text(df),
        "",
        "## Coverage Table",
        "",
        generate_coverage_table(df),
        "",
        "## Significance Table",
        "",
        generate_significance_table(df),
        "",
    ]

    with open(output_path, "w") as f:
        f.write("\n".join(report_lines))

    logging.info(f"Summary report written to {output_path}")

def main():
    results_dir = get_results_dir()
    csv_path = os.path.join(results_dir, "coverage_metrics.csv")
    report_path = os.path.join(results_dir, "summary_report.md")

    logging.basicConfig(level=logging.INFO)

    try:
        df = load_metrics_data(csv_path)
        generate_markdown_report(df, report_path)
        logging.info("Summary report generation complete.")
    except FileNotFoundError as e:
        logging.error(str(e))
        logging.error("Run 'python code/generate_metrics_csv.py' first.")

if __name__ == "__main__":
    main()