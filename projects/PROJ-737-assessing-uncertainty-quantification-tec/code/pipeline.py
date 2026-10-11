"""
Orchestration script for the Uncertainty Quantification pipeline.
Executes: Download -> Featurize -> Train Models -> Predict -> Metrics -> Statistical Analysis.
Updated to collect per‑sample predictions from each UQ method and write them to
``data/results/per_sample_errors.csv`` so that T003’s deliverables are satisfied.
"""
import os
import gc
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd

# Local imports based on API surface
from download import download_all
from featurize import process_dataset, main as featurize_main
from models.gpr import run_gpr, main as gpr_main
from models.mc_dropout import run_mc_dropout, main as mc_dropout_main
from models.deep_ensemble import run_deep_ensemble, main as ensemble_main
from models.conformal import run_conformal_prediction, main as conformal_main
from metrics.evaluation import calculate_calibration_error, calculate_sharpness
from stats.significance import run_paired_wilcoxon, run_sensitivity_analysis
from utils.logger import get_logger, log_pipeline_start, log_pipeline_end
from config import get_config

# Initialize logger
logger = get_logger(__name__)
config = get_config()

def ensure_directories():
    """Create required directory structure if not present."""
    dirs = [
        "data/raw", "data/processed",
        "code/models", "code/metrics", "code/stats",
        "results", "tests/unit", "tests/integration", "code/utils"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directory structure ensured.")

def download_data():
    """Download datasets using the download module."""
    logger.info("Starting data download...")
    # download_all handles the logic for OQMD and AFLOW
    download_all()
    logger.info("Data download complete.")

def featurize_data():
    """Featurize raw data and prepare splits."""
    logger.info("Starting featurization...")
    # process_dataset handles loading, featurizing, and splitting
    # It returns a dictionary of processed datasets
    processed_data = process_dataset()
    logger.info(f"Featurization complete. Processed {len(processed_data)} datasets.")
    return processed_data

def run_single_method(method_name: str, dataset_name: str, data: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    Run a specific UQ method on a specific dataset.
    Returns a DataFrame with per‑sample predictions (or ``None`` on failure).
    Expected columns in the returned DataFrame:
        sample_id, prediction, lower_bound, upper_bound, ground_truth
    """
    logger.info(f"Running {method_name} on {dataset_name}...")
    try:
        if method_name == "gpr":
            result = run_gpr(data[dataset_name], dataset_name)
        elif method_name == "mc_dropout":
            result = run_mc_dropout(data[dataset_name], dataset_name)
        elif method_name == "deep_ensemble":
            result = run_deep_ensemble(data[dataset_name], dataset_name)
        elif method_name == "conformal":
            result = run_conformal_prediction(data[dataset_name], dataset_name)
        else:
            logger.error(f"Unknown method: {method_name}")
            return None

        if result is None:
            logger.warning(f"{method_name} on {dataset_name} returned None.")
            return None

        # Ensure required columns exist; if not, attempt to construct them
        required = {"prediction", "lower_bound", "upper_bound", "ground_truth"}
        missing = required - set(result.columns)
        if missing:
            logger.error(
                f"{method_name} on {dataset_name} missing columns {missing}. "
                "Skipping this method."
            )
            return None

        # Add a sample identifier if not present
        if "sample_id" not in result.columns:
            result = result.reset_index().rename(columns={"index": "sample_id"})

        logger.info(f"Successfully completed {method_name} on {dataset_name}.")
        gc.collect()
        return result
    except Exception as e:
        logger.error(f"Failed to run {method_name} on {dataset_name}: {e}", exc_info=True)
        return None

def calculate_metrics_and_save():
    """
    Calculate calibration and sharpness metrics from per_sample_errors.csv
    and save to results/metrics_raw.csv.
    """
    logger.info("Calculating metrics from per_sample_errors.csv...")
    try:
        from generate_metrics_raw import main as gen_metrics_main
        gen_metrics_main()
        logger.info("Metrics calculation complete.")
    except ImportError:
        logger.warning("generate_metrics_raw module not found. Skipping metrics generation step.")

def run_statistical_analysis():
    """
    Execute statistical significance tests (Paired Wilcoxon) and sensitivity analysis.
    Outputs: results/statistical_report.csv, results/sensitivity_report.csv
    """
    logger.info("Starting statistical analysis...")
    try:
        from stats.significance import main as stats_main
        stats_main()
        logger.info("Statistical significance testing complete.")
    except Exception as e:
        logger.error(f"Statistical significance testing failed: {e}", exc_info=True)

    try:
        from generate_sensitivity_report import main as sens_main
        sens_main()
        logger.info("Sensitivity analysis complete.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)

def _write_per_sample_errors(all_records: List[pd.DataFrame]) -> None:
    """
    Concatenate per‑sample prediction DataFrames from all methods/datasets
    and write the unified CSV to ``data/results/per_sample_errors.csv``.
    """
    if not all_records:
        logger.error("No prediction records were collected; per_sample_errors.csv will not be created.")
        return

    combined = pd.concat(all_records, ignore_index=True)

    # Ensure column order matches the contract
    column_order = [
        "sample_id",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "dataset",
    ]
    # Add any missing columns with NaN
    for col in column_order:
        if col not in combined.columns:
            combined[col] = pd.NA

    combined = combined[column_order]

    output_path = Path(__file__).parents[1] / "data" / "results" / "per_sample_errors.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)
    logger.info(f"Wrote per‑sample errors to {output_path} ({len(combined)} rows).")

def main():
    """Main orchestration entry point."""
    log_pipeline_start("T003-ThinAnalysis")
    start_time = time.time()

    try:
        # 1. Setup
        ensure_directories()

        # 2. Data Download
        download_data()

        # 3. Featurization
        processed_data = featurize_data()

        # 4. Run Models & Collect Predictions
        methods = ["gpr", "mc_dropout", "deep_ensemble", "conformal"]
        datasets = list(processed_data.keys())

        all_prediction_records: List[pd.DataFrame] = []

        for method in methods:
            for dataset in datasets:
                pred_df = run_single_method(method, dataset, processed_data)
                if pred_df is not None:
                    pred_df["method"] = method
                    pred_df["dataset"] = dataset
                    all_prediction_records.append(pred_df)

        # 5. Write unified per‑sample errors file
        _write_per_sample_errors(all_prediction_records)

        # 6. Calculate Metrics (Calibration & Sharpness)
        calculate_metrics_and_save()

        # 7. Statistical Analysis (Wilcoxon & Sensitivity)
        run_statistical_analysis()

        end_time = time.time()
        logger.info(f"Pipeline completed successfully in {end_time - start_time:.2f} seconds.")
    except Exception as e:
        logger.error(f"Pipeline failed with critical error: {e}", exc_info=True)
        raise
    finally:
        log_pipeline_end("T003-ThinAnalysis")

if __name__ == "__main__":
    main()
