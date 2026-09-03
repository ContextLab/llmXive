"""
Entry point for the project pipeline.
The main function orchestrates the stages defined in the repository:
acquisition → baseline analysis → cleaning → reporting, etc.
"""

import logging
from pathlib import Path

# ----------------------------------------------------------------------
# Ensure the raw‑data README (with up‑to‑date checksums) exists before any
# other stage runs.  This call is safe to execute multiple times.
# ----------------------------------------------------------------------
from generate_raw_readme import generate as generate_raw_readme

generate_raw_readme()

# Existing imports – keep them as they were originally.
from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis
from cleaning import (
    apply_iqr_outlier_removal,
    apply_mean_imputation,
    apply_median_imputation,
    apply_knn_imputation,
    apply_categorical_recoding,
)
from reporting import (
    load_baseline_metrics,
    load_cleaned_metrics,
    generate_comparison_report,
    save_json_file,
)

# ----------------------------------------------------------------------
# Helper to initialise the global logger used throughout the pipeline.
# ----------------------------------------------------------------------
logger = setup_logging(log_level="INFO")
logger.info("Starting pipeline execution")

def run_pipeline() -> None:
    """
    High‑level orchestration of the full analysis pipeline.
    """
    # 1. Ensure reproducibility
    pin_random_seed(42)

    # 2. Load configuration
    config = get_config()

    # 3. Baseline analysis (raw data)
    raw_dir = Path(config.get("RAW_DATA_PATH", "data/raw"))
    baseline_metrics_path = Path(config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"))
    logger.info("Running baseline analysis on raw datasets")
    run_baseline_analysis(raw_dir=str(raw_dir), output_file=str(baseline_metrics_path))

    # 4. Cleaning strategies – omitted for brevity; they are invoked by
    #    the dedicated stage scripts (e.g., t022_save_cleaned_datasets.py).

    # 5. Reporting – also delegated to stage scripts.

    logger.info("Pipeline completed successfully")

def main() -> None:
    """
    ``python -m code.main`` entry point.
    """
    try:
        run_pipeline()
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise

if __name__ == "__main__":
    main()
