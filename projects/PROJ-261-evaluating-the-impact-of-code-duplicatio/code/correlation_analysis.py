from __future__ import annotations
import csv
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing public functions (preserved)
# ----------------------------------------------------------------------
# The original file already defines the following helpers:
#   load_clone_metrics, load_perplexity_scores,
#   load_bug_detection_results, compute_spearman_correlation,
#   run_correlation_analysis, etc.
# They are kept unchanged – they appear earlier in the file.

# ----------------------------------------------------------------------
# New implementation for saving correlation results
# ----------------------------------------------------------------------
def save_correlation_results(
    clone_metrics_path: Path | str = "data/processed/clone_metrics.csv",
    perplexity_path: Path | str = "data/processed/perplexity_scores.csv",
    bug_detection_path: Path | str = "data/processed/bug_detection_results.csv",
    output_path: Path | str = "data/analysis/correlation_results.csv",
) -> None:
    """
    Load the three metric files, compute Spearman correlations between
    clone density and perplexity as well as between clone density and
    bug‑detection accuracy, and write the results (including p‑values) to
    ``output_path``.

    The CSV header is:
    metric_x,metric_y,spearman_rho,p_value,n
    """
    clone_path = Path(clone_metrics_path)
    perp_path = Path(perplexity_path)
    bug_path = Path(bug_detection_path)
    out_path = Path(output_path)

    # Ensure the output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load dataframes; missing files are treated as empty frames
    try:
        df_clone = pd.read_csv(clone_path)
    except FileNotFoundError:
        logger.error("Clone metrics file not found: %s", clone_path)
        df_clone = pd.DataFrame(columns=["file_path", "clone_density"])

    try:
        df_perp = pd.read_csv(perp_path)
    except FileNotFoundError:
        logger.error("Perplexity scores file not found: %s", perp_path)
        df_perp = pd.DataFrame(columns=["file_path", "perplexity"])

    try:
        df_bug = pd.read_csv(bug_path)
    except FileNotFoundError:
        logger.error("Bug‑detection results file not found: %s", bug_path)
        df_bug = pd.DataFrame(columns=["file_path", "accuracy"])

    # Merge on file_path to align rows
    merged = df_clone.merge(df_perp, on="file_path", how="inner")
    merged = merged.merge(df_bug, on="file_path", how="inner")

    if merged.empty:
        logger.warning("No overlapping records found for correlation analysis.")
        # Still write an empty CSV with headers
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["metric_x", "metric_y", "spearman_rho", "p_value", "n"]
            )
        return

    results: List[Tuple[str, str, float, float, int]] = []

    # 1) Clone density vs Perplexity
    rho, p = spearmanr(merged["clone_density"], merged["perplexity"], nan_policy="omit")
    results.append(
        ("clone_density", "perplexity", float(rho), float(p), int(len(merged)))
    )

    # 2) Clone density vs Bug‑Detection Accuracy (if present)
    if "accuracy" in merged.columns:
        rho2, p2 = spearmanr(
            merged["clone_density"], merged["accuracy"], nan_policy="omit"
        )
        results.append(
            ("clone_density", "accuracy", float(rho2), float(p2), int(len(merged)))
        )

    # Write results
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["metric_x", "metric_y", "spearman_rho", "p_value", "n"]
        )
        for row in results:
            writer.writerow(row)

    logger.info("Correlation results saved to %s", out_path)

# ----------------------------------------------------------------------
# Convenience entry point used by ``generate_correlation_results.py``
# ----------------------------------------------------------------------
def main() -> None:
    """Run the full correlation analysis and persist results."""
    save_correlation_results()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
