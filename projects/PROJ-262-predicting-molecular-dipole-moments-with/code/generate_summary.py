"""Generate a comprehensive results summary for the dipole moment prediction project.

This script aggregates:
  * Metrics per seed (MAE, RMSE) from ``results/metrics.csv``
  * Confidence intervals for MAE and RMSE
  * Feature attribution rankings from ``results/attributions.json``
  * Statistical significance results from ``results/significance.csv``
  * Lists of generated visualisation files under ``results/figures/``

The final markdown report is written to ``results/summary.md``.
"""

from __future__ import annotations

import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Tuple

# Project‑specific utilities
from analysis.confidence_intervals import compute_confidence_interval

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def read_metrics(csv_path: Path) -> Tuple[List[float], List[float], List[dict]]:
    """Read MAE and RMSE values per seed.

    Returns:
        mae_vals: List of MAE values.
        rmse_vals: List of RMSE values.
        rows: List of the raw dictionaries (for the per‑seed table).
    """
    mae_vals: List[float] = []
    rmse_vals: List[float] = []
    rows: List[dict] = []

    if not csv_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            try:
                mae_vals.append(float(row["mae"]))
                rmse_vals.append(float(row["rmse"]))
            except KeyError as exc:
                raise KeyError(f"Expected columns 'mae' and 'rmse' in {csv_path}") from exc
    return mae_vals, rmse_vals, rows

def read_attributions(json_path: Path) -> List[Tuple[str, float]]:
    """Load attributions and return a list sorted by descending importance."""
    if not json_path.is_file():
        raise FileNotFoundError(f"Attributions file not found: {json_path}")

    with json_path.open() as f:
        data = json.load(f)

    # Expect a mapping feature -> importance
    if not isinstance(data, dict):
        raise ValueError(f"Attributions JSON must be an object mapping features to scores: {json_path}")

    sorted_attrib = sorted(data.items(), key=lambda kv: kv[1], reverse=True)
    return sorted_attrib

def read_significance(csv_path: Path) -> List[dict]:
    """Read significance test results (e.g., p‑values)."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Significance file not found: {csv_path}")

    results: List[dict] = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def list_figure_files(fig_dir: Path) -> List[Path]:
    """Return a list of PNG files in the figure directory."""
    if not fig_dir.is_dir():
        return []
    return sorted(fig_dir.glob("*.png"))

# ---------------------------------------------------------------------------
# Main generation routine
# ---------------------------------------------------------------------------

def generate_summary() -> None:
    """Create ``results/summary.md`` aggregating all final artifacts."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Define expected locations (relative to the repository root)
    repo_root = Path(__file__).resolve().parent.parent  # project root
    results_dir = repo_root / "results"
    metrics_path = results_dir / "metrics.csv"
    attributions_path = results_dir / "attributions.json"
    significance_path = results_dir / "significance.csv"
    figures_dir = results_dir / "figures"
    summary_path = results_dir / "summary.md"

    # -----------------------------------------------------------------------
    # Load data
    # -----------------------------------------------------------------------
    mae_vals, rmse_vals, metric_rows = read_metrics(metrics_path)
    attrib_sorted = read_attributions(attributions_path)
    significance_rows = read_significance(significance_path)
    figure_files = list_figure_files(figures_dir)

    # -----------------------------------------------------------------------
    # Compute statistics
    # -----------------------------------------------------------------------
    mae_mean = sum(mae_vals) / len(mae_vals)
    rmse_mean = sum(rmse_vals) / len(rmse_vals)

    mae_ci_low, mae_ci_high = compute_confidence_interval(mae_vals)  # type: ignore[arg-type]
    rmse_ci_low, rmse_ci_high = compute_confidence_interval(rmse_vals)  # type: ignore[arg-type]

    # -----------------------------------------------------------------------
    # Build markdown content
    # -----------------------------------------------------------------------
    lines: List[str] = ["# Final Results Summary", ""]

    # 1️⃣ Metrics per seed
    lines.append("## 1. Per‑seed Metrics")
    lines.append("")
    header = ["seed", "MAE", "RMSE"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for row in metric_rows:
        seed = row.get("seed", "-")
        mae = row.get("mae", "-")
        rmse = row.get("rmse", "-")
        lines.append(f"| {seed} | {mae} | {rmse} |")
    lines.append("")

    # 2️⃣ Overall statistics
    lines.append("## 2. Overall Statistics")
    lines.append("")
    lines.append(f"- **Mean MAE:** {mae_mean:.4f}")
    lines.append(f"- **95 % CI for MAE:** [{mae_ci_low:.4f}, {mae_ci_high:.4f}]")
    lines.append(f"- **Mean RMSE:** {rmse_mean:.4f}")
    lines.append(f"- **95 % CI for RMSE:** [{rmse_ci_low:.4f}, {rmse_ci_high:.4f}]")
    lines.append("")

    # 3️⃣ Feature attribution
    lines.append("## 3. Feature Attribution (Top 10)")
    lines.append("")
    lines.append("| Feature | Importance |")
    lines.append("|---|---|")
    for feature, score in attrib_sorted[:10]:
        lines.append(f"| {feature} | {score:.6f} |")
    lines.append("")

    # 4️⃣ Statistical significance
    lines.append("## 4. Statistical Significance Tests")
    lines.append("")
    if significance_rows:
        # Assume columns: test, metric, p_value
        headers = significance_rows[0].keys()
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "---|" * len(headers))
        for row in significance_rows:
            line = "| " + " | ".join(row[h] for h in headers) + " |"
            lines.append(line)
    else:
        lines.append("_No significance data found._")
    lines.append("")

    # 5️⃣ Visualisations
    lines.append("## 5. Generated Visualisations")
    lines.append("")
    if figure_files:
        for fig in figure_files:
            rel_path = fig.relative_to(repo_root)
            lines.append(f"![{fig.stem}]({rel_path})")
    else:
        lines.append("_No figure files detected in `results/figures/`._")
    lines.append("")

    # -----------------------------------------------------------------------
    # Write out the markdown file
    # -----------------------------------------------------------------------
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logging.info(f"Summary written to {summary_path}")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate_summary()
