"""
Task T013: Record baseline metrics to data/processed/baseline_metrics.json.

This script executes the baseline analysis pipeline (leveraging T011/T012 logic),
computes effect sizes (Cohen's d or R²), and writes the results to the specified
JSON artifact with the required precision.
"""
import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Import from existing project surface
from utils import pin_random_seed, compute_file_checksum, setup_logging
from config import get_config
from data_loader import download_dataset
from analysis import run_baseline_analysis, analyze_dataset

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """Log a concise summary of the computed metrics."""
    logger = logging.getLogger(__name__)
    dataset_id = metrics.get("dataset_id", "unknown")
    strategy = metrics.get("strategy", "baseline")
    
    # Extract p-values for logging
    p_values = metrics.get("p_values", {})
    p_str = ", ".join([f"{k}: {v:.4f}" for k, v in p_values.items()])
    
    effect_sizes = metrics.get("effect_sizes", {})
    es_str = ", ".join([f"{k}: {v:.4f}" for k, v in effect_sizes.items()])
    
    logger.info(f"Recorded metrics for {dataset_id} ({strategy}):")
    logger.info(f"  P-values: {p_str}")
    logger.info(f"  Effect Sizes: {es_str}")

def format_metric_value(value: float, precision: int = 3) -> float:
    """
    Format a float to a specific precision to satisfy SC-006/Task requirements.
    Returns the float rounded to the specified decimal places.
    """
    if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    return round(float(value), precision)

def process_dataset_for_baseline(
    dataset_id: str, 
    df: pd.DataFrame, 
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Run baseline analysis on a single dataset and format the result.
    """
    logger = logging.getLogger(__name__)
    
    # Run the baseline analysis logic defined in analysis.py
    # This returns a dictionary containing p-values, CIs, and effect sizes
    try:
        results = run_baseline_analysis(df, config)
    except Exception as e:
        logger.error(f"Failed to run baseline analysis on {dataset_id}: {e}", exc_info=True)
        return None

    # Validate results structure
    if not isinstance(results, dict):
        logger.error(f"Analysis result for {dataset_id} is not a dictionary.")
        return None

    # Extract and format specific fields
    formatted_metrics = {
        "dataset_id": dataset_id,
        "strategy": "baseline",
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "checksum": compute_file_checksum(f"data/raw/{dataset_id}.csv") if os.path.exists(f"data/raw/{dataset_id}.csv") else "N/A",
        "p_values": {},
        "confidence_intervals": {},
        "effect_sizes": {},
        "statistics": {}
    }

    # Process P-values
    raw_p = results.get("p_values", {})
    for test_name, p_val in raw_p.items():
        formatted_metrics["p_values"][test_name] = format_metric_value(p_val)

    # Process Confidence Intervals
    raw_ci = results.get("confidence_intervals", {})
    for test_name, ci in raw_ci.items():
        if ci and len(ci) == 2:
            formatted_metrics["confidence_intervals"][test_name] = {
                "lower": format_metric_value(ci[0]),
                "upper": format_metric_value(ci[1])
            }
        else:
            formatted_metrics["confidence_intervals"][test_name] = None

    # Process Effect Sizes (Cohen's d or R²)
    raw_es = results.get("effect_sizes", {})
    for test_name, es in raw_es.items():
        formatted_metrics["effect_sizes"][test_name] = format_metric_value(es)

    # Process other statistics (degrees of freedom, t-stats, etc.)
    raw_stats = results.get("statistics", {})
    for stat_name, stat_val in raw_stats.items():
        formatted_metrics["statistics"][stat_name] = format_metric_value(stat_val)

    return formatted_metrics

def main():
    """Main entry point for T013."""
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    logger.info("Starting T013: Record Baseline Metrics")

    # Load configuration
    config = get_config()
    random_seed = int(config.get("RANDOM_SEED", 42))
    pin_random_seed(random_seed)

    # Determine output path
    output_dir = "data/processed"
    output_path = os.path.join(output_dir, "baseline_metrics.json")
    os.makedirs(output_dir, exist_ok=True)

    # Retrieve dataset list from config or default to known datasets
    # T011/T012 already downloaded these, so we look for them in data/raw/
    raw_data_dir = "data/raw"
    dataset_files = [f for f in os.listdir(raw_data_dir) if f.endswith(".csv") and f.startswith("dataset_")]
    
    if not dataset_files:
        logger.warning("No dataset files found in data/raw/. Attempting to download defaults.")
        # Fallback to download if empty (matching T011 logic implicitly)
        from data_loader import download_dataset
        # Assuming standard IDs based on T011 description
        default_ids = ["ucihar", "ucishopper"] 
        for ds_id in default_ids:
            try:
                download_dataset(ds_id)
            except Exception as e:
                logger.warning(f"Could not download {ds_id}: {e}")
        dataset_files = [f for f in os.listdir(raw_data_dir) if f.endswith(".csv")]

    all_metrics = []

    for filename in dataset_files:
        dataset_id = filename.replace(".csv", "")
        filepath = os.path.join(raw_data_dir, filename)
        
        logger.info(f"Processing {dataset_id}...")
        try:
            df = pd.read_csv(filepath)
            
            # Clean column names for safety
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            
            # Run processing
            metrics = process_dataset_for_baseline(dataset_id, df, config)
            
            if metrics:
                log_metrics_summary(metrics)
                all_metrics.append(metrics)
            else:
                logger.warning(f"Skipping {dataset_id} due to analysis failure.")
                
        except Exception as e:
            logger.error(f"Error processing {dataset_id}: {e}", exc_info=True)
            continue

    # Write final JSON
    if all_metrics:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_metrics, f, indent=2)
        logger.info(f"Successfully wrote {len(all_metrics)} datasets to {output_path}")
    else:
        logger.error("No metrics were generated. Output file not created.")
        raise RuntimeError("T013 failed: No valid metrics generated.")

if __name__ == "__main__":
    main()
