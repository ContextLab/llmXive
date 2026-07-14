"""Generate a final results summary for the molecular dipole moment project.

This script aggregates the various result artifacts produced by earlier
pipeline stages—metrics, significance tests, attributions and visualisation
figures—into a single markdown report saved as ``results/summary.md`` (or a
user‑specified location).

The script is deliberately lightweight and depends only on the Python
standard library so that it can run in the constrained execution
environment used by the CI pipeline.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import List, Dict

def load_csv_as_dicts(csv_path: Path) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of rows as dictionaries."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_json(json_path: Path) -> Dict:
    """Load a JSON file and return the parsed object."""
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with json_path.open() as f:
        return json.load(f)

def list_figure_paths(fig_dir: Path) -> List[Path]:
    """Return a sorted list of PNG files in the given directory."""
    if not fig_dir.is_dir():
        return []
    return sorted(fig_dir.glob("*.png"))

def markdown_table_from_dicts(rows: List[Dict[str, str]]) -> str:
    """Convert a list of dict rows into a markdown table string."""
    if not rows:
        return "No data available.\n"
    headers = rows[0].keys()
    header_line = " | ".join(headers)
    separator = " | ".join("---" for _ in headers)
    lines = [f"| {header_line} |", f"| {separator} |"]
    for row in rows:
        line = " | ".join(str(row[h]) for h in headers)
        lines.append(f"| {line} |")
    return "\n".join(lines) + "\n"

def generate_summary(
    metrics_path: Path,
    significance_path: Path,
    attributions_path: Path,
    figures_dir: Path,
    output_path: Path,
) -> None:
    """Create the markdown summary file."""
    # Load data
    metrics = load_csv_as_dicts(metrics_path)
    significance = load_csv_as_dicts(significance_path)
    attributions = load_json(attributions_path)

    # Prepare markdown content
    md_parts: List[str] = ["# Final Results Summary\n"]

    # 1. Metrics table
    md_parts.append("## Model Performance Metrics\n")
    md_parts.append(markdown_table_from_dicts(metrics))

    # 2. Significance tests
    md_parts.append("## Statistical Significance of Performance Difference\n")
    md_parts.append(markdown_table_from_dicts(significance))

    # 3. Top attributions (show top‑10 features if available)
    md_parts.append("## Feature Attribution Rankings (Top 10)\n")
    if isinstance(attributions, dict):
        # Expect a mapping feature -> importance score
        sorted_items = sorted(attributions.items(), key=lambda kv: kv[1], reverse=True)
        top_items = sorted_items[:10]
        if top_items:
            md_parts.append("| Feature | Importance |\n")
            md_parts.append("| --- | --- |\n")
            for feat, score in top_items:
                md_parts.append(f"| {feat} | {score:.4f} |\n")
            md_parts.append("\n")
        else:
            md_parts.append("No attribution entries found.\n")
    else:
        md_parts.append("Attribution file does not contain a dictionary.\n")

    # 4. Visualisation figures
    md_parts.append("## Visualisations\n")
    figure_paths = list_figure_paths(figures_dir)
    if figure_paths:
        for fig_path in figure_paths:
            # Use relative path for markdown embedding
            rel_path = fig_path.relative_to(output_path.parent)
            md_parts.append(f"![{fig_path.stem}]({rel_path})\n")
    else:
        md_parts.append("No figures were found in the expected directory.\n")

    # Write out markdown
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        f.write("\n".join(md_parts))

    print(f"Summary written to {output_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a markdown summary of all final results."
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("results/metrics.csv"),
        help="Path to the CSV file containing model performance metrics.",
    )
    parser.add_argument(
        "--significance",
        type=Path,
        default=Path("results/significance.csv"),
        help="Path to the CSV file with statistical significance results.",
    )
    parser.add_argument(
        "--attributions",
        type=Path,
        default=Path("results/attributions.json"),
        help="Path to the JSON file with feature attribution rankings.",
    )
    parser.add_argument(
        "--figures",
        type=Path,
        default=Path("results/figures"),
        help="Directory containing PNG visualisation figures.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/summary.md"),
        help="Output markdown file path.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    generate_summary(
        metrics_path=args.metrics,
        significance_path=args.significance,
        attributions_path=args.attributions,
        figures_dir=args.figures,
        output_path=args.output,
    )

if __name__ == "__main__":
    main()