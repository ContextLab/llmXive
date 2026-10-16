"""
Script to generate the correlation results CSV file.

This script loads the processed performance and graph metrics, computes
Spearman correlations, applies FDR correction, and writes the final
results to ``data/processed/correlation_results.csv``.
"""

import logging
import pandas as pd
from pathlib import Path

# Local imports
from stats_engine import (
    load_and_merge_metrics,
    compute_spearman_correlations,
    apply_benjamini_hochberg_fdr,
    save_correlation_results,
)
from logger import setup_logger

# Initialise a module‑level logger
logger = setup_logger(__name__)

def main() -> None:
    """Run the end‑to‑end correlation generation pipeline."""
    logger.info("Starting correlation results generation...")

    # Verify required input files exist
    perf_path = Path("data/processed/performance_metrics.csv")
    graph_path = Path("data/processed/graph_metrics.csv")
    if not perf_path.is_file():
        logger.error(f"Performance metrics file not found: {perf_path}")
        raise FileNotFoundError(perf_path)
    if not graph_path.is_file():
        logger.error(f"Graph metrics file not found: {graph_path}")
        raise FileNotFoundError(graph_path)

    # Load and merge the datasets
    logger.info("Loading and merging metrics...")
    merged_df = load_and_merge_metrics(
        performance_path=str(perf_path), graph_path=str(graph_path)
    )

    if merged_df.empty:
        logger.error("Merged DataFrame is empty – cannot compute correlations.")
        raise ValueError("No data available after merging performance and graph metrics.")

    # Compute raw Spearman correlations
    logger.info("Computing Spearman correlations...")
    raw_corr_df = compute_spearman_correlations(merged_df)

    if raw_corr_df.empty:
        logger.warning("No numeric metric pairs found – creating an empty results file.")
        empty_path = Path("data/processed/correlation_results.csv")
        empty_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            columns=["metric_a", "metric_b", "rho", "p_value", "adj_p_value", "is_significant"]
        ).to_csv(empty_path, index=False)
        logger.info(f"Empty correlation results written to {empty_path}")
        return

    # Apply Benjamini‑Hochberg FDR correction
    logger.info("Applying Benjamini‑Hochberg FDR correction...")
    corrected_df = apply_benjamini_hochberg_fdr(raw_corr_df)

    # Persist the final results
    output_path = Path("data/processed/correlation_results.csv")
    logger.info(f"Saving correlation results to {output_path}...")
    save_correlation_results(corrected_df, str(output_path))

    # Summarise significance
    sig_count = int((corrected_df["adj_p_value"] < 0.05).sum())
    total = len(corrected_df)
    logger.info(f"Correlation results saved. Total pairs: {total}, Significant (adj p < 0.05): {sig_count}")

if __name__ == "__main__":
    # Configure root logging for direct script execution
    logging.basicConfig(level=logging.INFO)
    main()