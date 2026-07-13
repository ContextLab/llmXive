"""
Task T013: Record baseline metrics (p-value, 95% CI, Cohen's d/R²) to data/processed/baseline_metrics.json
with >= 3 decimal precision.
"""
import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

# Local imports
from utils import setup_logging, compute_file_checksum
from config import Config, get_config
from analysis import run_baseline_analysis, load_datasets_from_raw

# Ensure output directory exists
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "baseline_metrics.json")

def format_metric_value(value: float, precision: int = 3) -> float:
    """Format a numeric value to the specified decimal precision."""
    if value is None or not isinstance(value, (int, float)):
        return value
    return round(float(value), precision)

def log_metrics_summary(metrics: List[Dict[str, Any]]) -> None:
    """Log a summary of the recorded metrics."""
    logger = logging.getLogger(__name__)
    logger.info(f"Recording {len(metrics)} dataset baseline metrics.")
    for entry in metrics:
        ds_name = entry.get("dataset", "unknown")
        outcome = entry.get("outcome", "unknown")
        logger.info(f"  - Dataset: {ds_name}, Outcome: {outcome}")
        if "tests" in entry:
            for test_name, test_data in entry["tests"].items():
                p_val = test_data.get("p_value", "N/A")
                logger.info(f"    Test '{test_name}': p={p_val}")
        if "regressions" in entry:
            for reg_name, reg_data in entry["regressions"].items():
                r_sq = reg_data.get("r_squared", "N/A")
                logger.info(f"    Regression '{reg_name}': R²={r_sq}")

def process_dataset_for_baseline(
    df: Any,
    dataset_name: str,
    outcome_col: str,
    config: Config,
    raw_dir: str
) -> Optional[Dict[str, Any]]:
    """
    Run baseline analysis on a single dataset and format the result.
    Uses the flexible run_baseline_analysis which accepts (df, dataset_name=...)
    or (df, outcome_col=...) depending on implementation, but here we pass
    the dataframe and let the analysis module handle the rest.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Run baseline analysis. 
        # Note: run_baseline_analysis in analysis.py is designed to be flexible.
        # We pass the dataframe and the dataset name.
        # The analysis module will identify the outcome column if not specified,
        # or we can assume 'target' or similar based on data_loader conventions.
        # For safety, we try calling with keyword arguments that match the known signatures.
        
        # Attempt 1: Standard call with dataset name
        results = run_baseline_analysis(df, dataset_name=dataset_name, outcome_col=outcome_col)
        
        if not results:
            logger.warning(f"No results returned for {dataset_name}. Skipping.")
            return None

        # Format the results to ensure >= 3 decimal precision
        formatted_entry = {
            "dataset": dataset_name,
            "outcome": outcome_col,
            "timestamp": datetime.now().isoformat(),
            "checksum": compute_file_checksum(os.path.join(raw_dir, f"{dataset_name}.csv"))
        }

        # Process Tests (t-tests)
        if "tests" in results:
            formatted_entry["tests"] = {}
            for test_name, test_data in results["tests"].items():
                formatted_test = {}
                for key, val in test_data.items():
                    if isinstance(val, (int, float)):
                        formatted_test[key] = format_metric_value(val, 3)
                    else:
                        formatted_test[key] = val
                formatted_entry["tests"][test_name] = formatted_test

        # Process Regressions
        if "regressions" in results:
            formatted_entry["regressions"] = {}
            for reg_name, reg_data in results["regressions"].items():
                formatted_reg = {}
                for key, val in reg_data.items():
                    if isinstance(val, (int, float)):
                        formatted_reg[key] = format_metric_value(val, 3)
                    elif isinstance(val, list):
                        # Format list items if they are floats
                        formatted_reg[key] = [format_metric_value(v, 3) if isinstance(v, (int, float)) else v for v in val]
                    else:
                        formatted_reg[key] = val
                formatted_entry["regressions"][reg_name] = formatted_reg

        # Process Effect Sizes
        if "effect_sizes" in results:
            formatted_entry["effect_sizes"] = {}
            for eff_name, eff_val in results["effect_sizes"].items():
                formatted_entry["effect_sizes"][eff_name] = format_metric_value(eff_val, 3)

        # Validation: Ensure p-values are in (0, 1) and CIs are finite
        if "tests" in formatted_entry:
            for test_name, test_data in formatted_entry["tests"].items():
                p_val = test_data.get("p_value")
                if p_val is not None:
                    if not (0 < p_val < 1):
                        logger.warning(f"Dataset {dataset_name}, Test {test_name}: p-value {p_val} out of range (0,1).")
                    ci_lower = test_data.get("ci_lower")
                    ci_upper = test_data.get("ci_upper")
                    if ci_lower is not None and (not isinstance(ci_lower, (int, float)) or not (ci_lower == ci_lower)): # NaN check
                        logger.warning(f"Dataset {dataset_name}, Test {test_name}: CI lower bound invalid.")
                    if ci_upper is not None and (not isinstance(ci_upper, (int, float)) or not (ci_upper == ci_upper)):
                        logger.warning(f"Dataset {dataset_name}, Test {test_name}: CI upper bound invalid.")

        return formatted_entry

    except Exception as e:
        logger.error(f"Error processing dataset {dataset_name}: {e}", exc_info=True)
        return None

def main() -> int:
    """
    Main entry point for T013.
    1. Loads datasets from raw directory.
    2. Runs baseline analysis on each.
    3. Aggregates results.
    4. Writes to data/processed/baseline_metrics.json with 3 decimal precision.
    """
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    config = get_config()
    
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory not found: {raw_dir}. Please run data acquisition first.")
        return 1

    logger.info(f"Loading datasets from {raw_dir}...")
    datasets = load_datasets_from_raw(raw_dir)
    
    if not datasets:
        logger.error("No datasets found in raw directory. Aborting.")
        return 1

    logger.info(f"Found {len(datasets)} datasets.")
    all_metrics = []

    for dataset_name, df in datasets.items():
        # Determine outcome column. 
        # Typically 'target', 'outcome', or the last column. 
        # We'll assume 'target' if present, else last column.
        outcome_col = "target" if "target" in df.columns else df.columns[-1]
        
        logger.info(f"Processing {dataset_name} (outcome: {outcome_col})...")
        result = process_dataset_for_baseline(df, dataset_name, outcome_col, config, raw_dir)
        if result:
            all_metrics.append(result)

    if not all_metrics:
        logger.warning("No metrics were successfully generated.")
        return 1

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write to JSON
    logger.info(f"Writing {len(all_metrics)} entries to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_metrics, f, indent=2)

    log_metrics_summary(all_metrics)
    logger.info("T013 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
