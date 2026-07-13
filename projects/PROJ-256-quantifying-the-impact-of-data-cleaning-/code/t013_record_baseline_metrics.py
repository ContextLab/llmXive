"""
Task T013: Record baseline metrics to data/processed/baseline_metrics.json.

This script loads the datasets prepared by T011/T012, runs the baseline analysis
using the existing analysis module, and writes the results (p-values, CIs, effect sizes)
to data/processed/baseline_metrics.json with >=3 decimal precision.

It serves as the primary producer of the `data/processed/baseline_metrics.json` artifact
required by the run-book and downstream tasks (US2/US3).
"""
import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime

# Import from project modules
from utils import setup_logging, compute_file_checksum, pin_random_seed
from config import get_config
from data_loader import download_dataset
from analysis import run_baseline_analysis, analyze_dataset
from models import Dataset, AnalysisResult

logger = logging.getLogger(__name__)

# Constants for output
OUTPUT_PATH = "data/processed"
OUTPUT_FILE = "baseline_metrics.json"

def format_metric_value(value: float, precision: int = 6) -> float:
    """Format a metric value to a specific precision to ensure JSON consistency."""
    if not np.isfinite(value):
        return float(value)
    return round(value, precision)

def log_metrics_summary(metrics: Dict[str, Any], dataset_name: str) -> None:
    """Log a summary of the computed metrics."""
    logger.info(f"Metrics for {dataset_name}:")
    if 't_test' in metrics:
        tt = metrics['t_test']
        logger.info(f"  T-Test: p={tt['p_value']:.6f}, CI=[{tt['ci_low']:.6f}, {tt['ci_high']:.6f}], d={tt['effect_size']:.6f}")
    if 'regression' in metrics:
        reg = metrics['regression']
        logger.info(f"  Regression: p={reg['p_value']:.6f}, R²={reg['r_squared']:.6f}, CI=[{reg['ci_low']:.6f}, {reg['ci_high']:.6f}]")

def process_dataset_for_baseline(dataset_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run baseline analysis on a single dataset and format the results.
    Returns a dictionary suitable for JSON serialization.
    """
    # Pin seed for reproducibility within this run
    config = get_config()
    seed = config.get('RANDOM_SEED', 42)
    pin_random_seed(seed)

    try:
        # Run the baseline analysis logic
        # The analyze_dataset function expects the dataframe and returns an AnalysisResult
        result: AnalysisResult = analyze_dataset(df)

        if not result or not result.statistics:
            logger.warning(f"No statistics returned for {dataset_name}. Skipping.")
            return {}

        stats = result.statistics
        formatted = {
            "dataset_name": dataset_name,
            "timestamp": datetime.utcnow().isoformat(),
            "checksum": compute_file_checksum(os.path.join("data", "raw", f"{dataset_name}.csv")) if os.path.exists(os.path.join("data", "raw", f"{dataset_name}.csv")) else "unknown",
            "n_rows": len(df),
            "n_cols": len(df.columns),
            "statistics": {}
        }

        # Process T-Test results if present
        if stats.t_test_result:
            tt = stats.t_test_result
            formatted["statistics"]["t_test"] = {
                "p_value": format_metric_value(tt.p_value, 6),
                "ci_low": format_metric_value(tt.ci_low, 6),
                "ci_high": format_metric_value(tt.ci_high, 6),
                "effect_size_cohen_d": format_metric_value(tt.effect_size, 6),
                "test_statistic": format_metric_value(tt.statistic, 6),
                "degrees_of_freedom": float(tt.degrees_of_freedom) if tt.degrees_of_freedom is not None else None,
                "significant_at_005": bool(tt.p_value < 0.05)
            }

        # Process Regression results if present
        if stats.regression_result:
            reg = stats.regression_result
            formatted["statistics"]["regression"] = {
                "p_value": format_metric_value(reg.p_value, 6),
                "r_squared": format_metric_value(reg.r_squared, 6),
                "ci_low": format_metric_value(reg.ci_low, 6),
                "ci_high": format_metric_value(reg.ci_high, 6),
                "coefficient": format_metric_value(reg.coefficient, 6),
                "significant_at_005": bool(reg.p_value < 0.05)
            }

        # Validation: Ensure p-values are in (0, 1) and CIs are finite
        if formatted["statistics"]:
            for stat_type, stat_data in formatted["statistics"].items():
                if 'p_value' in stat_data:
                    if not (0 < stat_data['p_value'] < 1):
                        logger.warning(f"Validation Warning: {dataset_name} {stat_type} p-value {stat_data['p_value']} outside (0,1).")
                    if not np.isfinite(stat_data['p_value']):
                        logger.error(f"Validation Error: {dataset_name} {stat_type} p-value is not finite.")
                        return {}
                if 'ci_low' in stat_data and 'ci_high' in stat_data:
                    if not (np.isfinite(stat_data['ci_low']) and np.isfinite(stat_data['ci_high'])):
                        logger.error(f"Validation Error: {dataset_name} {stat_type} CI bounds are not finite.")
                        return {}

        return formatted

    except Exception as e:
        logger.error(f"Failed to process {dataset_name}: {e}", exc_info=True)
        return {}

def load_datasets_from_raw() -> List[pd.DataFrame]:
    """
    Load datasets from the data/raw directory.
    This assumes T001 and T011 have populated the raw data directory.
    """
    raw_dir = "data/raw"
    datasets = []
    
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory {raw_dir} does not exist. Attempting to download default datasets.")
        # Fallback to downloading if raw dir is empty/missing (T011 logic)
        try:
            download_dataset() # This function in data_loader handles the fallback logic
        except Exception as e:
            logger.error(f"Failed to download default datasets: {e}")
            return []

    if not os.path.exists(raw_dir):
        return []

    for file in os.listdir(raw_dir):
        if file.endswith('.csv'):
            path = os.path.join(raw_dir, file)
            try:
                df = pd.read_csv(path)
                # Basic validation
                if df.empty:
                    logger.warning(f"Dataset {file} is empty.")
                    continue
                datasets.append((file.replace('.csv', ''), df))
                logger.info(f"Loaded dataset: {file} ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")

    return datasets

def main():
    """Main entry point for T013."""
    # Setup logging
    config = get_config()
    log_level = config.get('LOG_LEVEL', 'INFO')
    setup_logging(log_level)
    pin_random_seed(config.get('RANDOM_SEED', 42))

    logger.info("Starting T013: Record Baseline Metrics")

    # Ensure output directory exists
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    # Load datasets
    datasets = load_datasets_from_raw()
    if not datasets:
        logger.error("No datasets found to analyze. T011 (Data Acquisition) must run first.")
        # Create an empty metrics file to satisfy the artifact check, but log the failure
        output_path = os.path.join(OUTPUT_PATH, OUTPUT_FILE)
        with open(output_path, 'w') as f:
            json.dump({"error": "No datasets found", "datasets": []}, f, indent=2)
        return

    all_metrics = []
    success_count = 0

    for name, df in datasets:
        logger.info(f"Processing {name}...")
        result = process_dataset_for_baseline(name, df)
        if result:
            all_metrics.append(result)
            log_metrics_summary(result.get('statistics', {}), name)
            success_count += 1
        else:
            logger.warning(f"Skipped {name} due to analysis failure.")

    # Prepare final output structure
    output_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_datasets": len(datasets),
        "successful_analyses": success_count,
        "datasets": all_metrics
    }

    # Write to file
    output_path = os.path.join(OUTPUT_PATH, OUTPUT_FILE)
    try:
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Successfully wrote baseline metrics to {output_path}")
        
        # Verify file was written
        if os.path.exists(output_path):
            checksum = compute_file_checksum(output_path)
            logger.info(f"Output checksum: {checksum}")
        else:
            logger.error(f"Output file {output_path} was not created despite write success message.")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}", exc_info=True)
        raise

    logger.info("T013 Complete.")

if __name__ == "__main__":
    main()