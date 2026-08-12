import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Project utilities
from utils import setup_logging, pin_random_seed
from data_loader import load_datasets_from_raw
from analysis import run_baseline_analysis
from cleaning import (
    apply_iqr_outlier_removal,
    apply_mean_imputation,
    apply_median_imputation,
    apply_knn_imputation,
    apply_categorical_recoding,
)

logger = setup_logging(log_level="INFO")
pin_random_seed(42)

def _ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def run_cleaning_strategies(df):
    """
    Apply a representative subset of cleaning strategies and return a list
    of tuples ``(strategy_name, cleaned_df, metadata)``.
    """
    results = []

    # IQR outlier removal
    cleaned_iqr, meta_iqr = apply_iqr_outlier_removal(df)
    results.append(("iqr_outlier_removal", cleaned_iqr, meta_iqr))

    # Mean imputation (example on numeric columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cleaned_mean, meta_mean = apply_mean_imputation(df, numeric_cols)
    results.append(("mean_imputation", cleaned_mean, meta_mean))

    # Median imputation
    cleaned_median, meta_median = apply_median_imputation(df, numeric_cols)
    results.append(("median_imputation", cleaned_median, meta_median))

    # KNN imputation (k=5)
    cleaned_knn, meta_knn = apply_knn_imputation(df, numeric_cols, k=5)
    results.append(("knn_imputation", cleaned_knn, meta_knn))

    # Categorical recoding
    cleaned_cat, meta_cat = apply_categorical_recoding(df)
    results.append(("categorical_recoding", cleaned_cat, meta_cat))

    return results

def run_pipeline() -> None:
    """
    End‑to‑end pipeline that:
    1. Loads raw CSV datasets.
    2. Computes baseline metrics and writes them to ``baseline_metrics.json``.
    3. Applies cleaning strategies, re‑runs the analysis on each cleaned variant,
       and writes aggregated cleaned metrics to ``cleaned_metrics.json``.
    """
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    _ensure_dir(processed_dir)

    # ------------------------------------------------------------------
    # 1. Load raw datasets
    # ------------------------------------------------------------------
    logger.info("Loading raw datasets from %s", raw_dir)
    datasets: Dict[str, Any] = load_datasets_from_raw(raw_dir)

    # ------------------------------------------------------------------
    # 2. Baseline analysis
    # ------------------------------------------------------------------
    logger.info("Running baseline analysis")
    baseline_metrics = {}
    for name, df in datasets.items():
        try:
            metrics = run_baseline_analysis(dataframe=df)
            baseline_metrics[name] = metrics
        except Exception as e:
            logger.error("Baseline analysis failed for %s: %s", name, e)

    baseline_path = processed_dir / "baseline_metrics.json"
    logger.info("Writing baseline metrics to %s", baseline_path)
    with open(baseline_path, "w") as fp:
        json.dump(baseline_metrics, fp, indent=2)

    # ------------------------------------------------------------------
    # 3. Cleaning + re‑analysis
    # ------------------------------------------------------------------
    logger.info("Applying cleaning strategies and re‑running analysis")
    cleaned_aggregate: Dict[str, Any] = {}

    for name, df in datasets.items():
        strategy_results = run_cleaning_strategies(df)
        for strat_name, cleaned_df, meta in strategy_results:
            try:
                metrics = run_baseline_analysis(dataframe=cleaned_df)
                # Store under a composite key to keep results distinct
                key = f"{name}::{strat_name}"
                cleaned_aggregate[key] = {
                    "metrics": metrics,
                    "metadata": meta,
                }
            except Exception as e:
                logger.error(
                    "Cleaned analysis failed for %s (%s): %s", name, strat_name, e
                )

    cleaned_path = processed_dir / "cleaned_metrics.json"
    logger.info("Writing cleaned metrics to %s", cleaned_path)
    with open(cleaned_path, "w") as fp:
        json.dump(cleaned_aggregate, fp, indent=2)

def main() -> int:
    """
    Entry point used by ``python -m code.main`` or ``python code/main.py``.
    Returns an exit code (0 = success, non‑zero = failure).
    """
    try:
        run_pipeline()
        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as exc:
        logger.exception("Pipeline terminated with an error: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())