import os
import sys
import logging
import traceback
import json
import time
from typing import Optional, Dict, Any
import pandas as pd

from utils.logging import get_logger
from data.download import download_dataset
from data.preprocess import preprocess_data, normalize_units
from data.descriptors import calculate_descriptors, filter_missing_properties

logger = get_logger(__name__)

def run_pipeline(
    input_url: Optional[str] = None,
    output_csv: str = "data/processed/hea_descriptors.csv",
    skip_download: bool = False
) -> pd.DataFrame:
    """
    Orchestrates the full data pipeline:
    1. Download dataset (unless skip_download is True)
    2. Preprocess (filter single-phase, room-temp, handle missing YS)
    3. Normalize units (to MPa)
    4. Calculate descriptors (delta, dchi, VEC, entropy, melting var)
    5. Filter entries with missing elemental properties
    6. Save to CSV
    7. Write detailed pipeline_log.json for auditability

    Args:
        input_url: URL to the dataset. If None, uses config.
        output_csv: Path to save the final processed CSV.
        skip_download: If True, assumes data exists at 'data/raw/hea_compositions.csv'.

    Returns:
        The processed DataFrame.
    """
    logger.info("Starting HEA Yield Strength Prediction Pipeline")
    
    # Initialize pipeline log structure
    pipeline_log = {
        "task_id": "T116",
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operations": [],
        "warnings": [],
        "end_time": None,
        "status": "running"
    }

    def log_operation(name: str, status: str, details: Optional[Dict] = None):
        """Helper to log an operation step."""
        entry = {
            "name": name,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        if details:
            entry["details"] = details
        pipeline_log["operations"].append(entry)

    def add_warning(msg: str):
        """Helper to add a warning."""
        pipeline_log["warnings"].append({
            "message": msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    try:
        # Step 1: Download
        step_start = time.time()
        if not skip_download:
            logger.info("Step 1: Downloading dataset...")
            raw_df = download_dataset(url=input_url)
            log_operation("Download", "SUCCESS", {"source": input_url or "config"})
        else:
            raw_path = "data/raw/hea_compositions.csv"
            if not os.path.exists(raw_path):
                raise FileNotFoundError(f"Skip download requested but {raw_path} not found.")
            logger.info(f"Step 1: Loading existing raw data from {raw_path}")
            raw_df = pd.read_csv(raw_path)
            log_operation("Download", "SKIPPED (Existing File)", {"path": raw_path})
        
        step_duration = time.time() - step_start
        pipeline_log["operations"][-1]["duration_seconds"] = step_duration

        # Step 2: Preprocess (filter single-phase, room temp, missing YS)
        step_start = time.time()
        logger.info("Step 2: Preprocessing data...")
        processed_df = preprocess_data(raw_df)
        log_operation("Preprocess", "SUCCESS", {
            "initial_rows": len(raw_df),
            "final_rows": len(processed_df)
        })
        step_duration = time.time() - step_start
        pipeline_log["operations"][-1]["duration_seconds"] = step_duration

        # Step 3: Normalize units to MPa
        step_start = time.time()
        logger.info("Step 3: Normalizing units to MPa...")
        processed_df = normalize_units(processed_df)
        log_operation("Normalize Units", "SUCCESS", {"target_unit": "MPa"})
        step_duration = time.time() - step_start
        pipeline_log["operations"][-1]["duration_seconds"] = step_duration

        # Step 4: Calculate descriptors
        step_start = time.time()
        logger.info("Step 4: Calculating compositional descriptors...")
        df_with_descriptors = calculate_descriptors(processed_df)
        log_operation("Calculate Descriptors", "SUCCESS", {
            "descriptors": ["delta", "dchi", "VEC", "entropy", "melting_variance"]
        })
        step_duration = time.time() - step_start
        pipeline_log["operations"][-1]["duration_seconds"] = step_duration

        # Step 5: Filter missing properties
        step_start = time.time()
        logger.info("Step 5: Filtering entries with missing elemental properties...")
        final_df = filter_missing_properties(df_with_descriptors)
        log_operation("Filter Missing Properties", "SUCCESS", {
            "rows_before": len(df_with_descriptors),
            "rows_after": len(final_df)
        })
        step_duration = time.time() - step_start
        pipeline_log["operations"][-1]["duration_seconds"] = step_duration

        # Step 6: Save to CSV
        step_start = time.time()
        logger.info(f"Step 6: Saving processed data to {output_csv}")
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        final_df.to_csv(output_csv, index=False)
        log_operation("Save CSV", "SUCCESS", {"path": output_csv, "rows": len(final_df)})
        step_duration = time.time() - step_start
        pipeline_log["operations"][-1]["duration_seconds"] = step_duration

        # Check for warnings from previous tasks (Power Analysis, VIF) if available
        # We check for existence of output files to conditionally add warnings
        if os.path.exists("output/power_analysis.json"):
            with open("output/power_analysis.json", "r") as f:
                power_data = json.load(f)
                if power_data.get("status") == "low_power":
                    add_warning("Power analysis indicates low power; sample size may be insufficient.")
        
        if os.path.exists("output/vif_results.json"):
            with open("output/vif_results.json", "r") as f:
                vif_data = json.load(f)
                high_vif = [k for k, v in vif_data.get("results", {}).items() if v > 5]
                if high_vif:
                    add_warning(f"High VIF detected for features: {high_vif}. Remediation may be required.")

        pipeline_log["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        pipeline_log["status"] = "SUCCESS"
        pipeline_log["total_rows_processed"] = len(final_df)

    except Exception as e:
        logger.exception("Pipeline failed")
        pipeline_log["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        pipeline_log["status"] = "FAILED"
        pipeline_log["error"] = str(e)
        add_warning(f"Pipeline execution failed: {str(e)}")
        raise

    finally:
        # Write the pipeline log to output/pipeline_log.json
        log_path = "output/pipeline_log.json"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(pipeline_log, f, indent=2)
        logger.info(f"Pipeline log written to {log_path}")

    return final_df

def main():
    """
    Main entry point for the pipeline script.
    Reads the verified dataset URL from config and runs the full pipeline.
    """
    from utils.config import get_verified_dataset_url
    
    try:
        url = get_verified_dataset_url()
        if not url:
            logger.error("No verified dataset URL found in config. Cannot proceed.")
            sys.exit(1)
        
        run_pipeline(input_url=url, output_csv="data/processed/hea_descriptors.csv")
        
        # Trigger status writer after pipeline
        from data.status_writer import main as status_main
        status_main()
        
    except Exception as e:
        logger.exception("Pipeline failed")
        sys.exit(1)

if __name__ == "__main__":
    main()